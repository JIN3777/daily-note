"""종목별 캔들 + 거래량 차트 생성 (mplfinance). 국내 관례대로 상승은 빨강, 하락은 파랑."""
import os
from datetime import datetime, timedelta

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import mplfinance as mpf
import pandas as pd
import pykrx
from pykrx import stock

from config import NOTES_DIR

CHARTS_DIR = NOTES_DIR / "charts"
LOOKBACK_CALENDAR_DAYS = 120  # 60일선까지 넉넉히 그려지도록 (달력일 기준, 휴장일 포함)
MAV_PERIODS = (5, 20, 60)
MAV_COLORS = ("#e67e22", "#16a34a", "#8e44ad")  # 5/20/60일선 색상 (범례로 구분)

# pykrx가 내장 배포하는 한글 폰트를 등록 (matplotlib 기본 폰트는 한글 글리프가 없음).
_FONT_PATH = os.path.join(os.path.dirname(pykrx.__file__), "NanumBarunGothic.ttf")
fm.fontManager.addfont(_FONT_PATH)
_FONT_NAME = fm.FontProperties(fname=_FONT_PATH).get_name()

_MARKET_COLORS = mpf.make_marketcolors(up="red", down="blue", edge="inherit", wick="inherit", volume="inherit")
_STYLE = mpf.make_mpf_style(base_mpf_style="yahoo", marketcolors=_MARKET_COLORS, rc={"font.family": _FONT_NAME})


def fetch_ohlcv(ticker: str, as_of: str, lookback_days: int = LOOKBACK_CALENDAR_DAYS) -> pd.DataFrame:
    """as_of(YYYYMMDD) 기준 과거 lookback_days 달력일의 OHLCV. 실패하면 빈 DataFrame."""
    end_dt = datetime.strptime(as_of, "%Y%m%d")
    start_dt = end_dt - timedelta(days=lookback_days)
    try:
        df = stock.get_market_ohlcv_by_date(start_dt.strftime("%Y%m%d"), as_of, ticker)
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.rename(columns={"시가": "Open", "고가": "High", "저가": "Low", "종가": "Close", "거래량": "Volume"})
    df.index = pd.to_datetime(df.index)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def render_chart(df: pd.DataFrame, ticker: str, name: str, as_of: str) -> str | None:
    """차트 PNG를 notes/charts/에 저장하고, notes/ 기준 상대 경로를 반환. 실패하면 None."""
    if df is None or df.empty:
        return None

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    dt = datetime.strptime(as_of, "%Y%m%d")
    filename = f"{dt:%Y-%m-%d}_{ticker}.png"
    out_path = CHARTS_DIR / filename

    # mplfinance의 mav= 옵션은 범례 라벨을 안 붙여주므로, addplot으로 직접 그려서
    # MA5/MA20/MA60이 어떤 선인지 범례에 표시되게 한다.
    addplots = [
        mpf.make_addplot(
            df["Close"].rolling(period).mean(),
            color=color,
            width=1.2,
            label=f"MA{period}",
        )
        for period, color in zip(MAV_PERIODS, MAV_COLORS)
    ]

    try:
        mpf.plot(
            df,
            type="candle",
            volume=True,
            style=_STYLE,
            title=f"{name} ({ticker})",
            addplot=addplots,
            figsize=(7, 4.5),
            savefig=dict(fname=out_path, dpi=120, bbox_inches="tight"),
        )
    except Exception:
        return None
    return f"charts/{filename}"
