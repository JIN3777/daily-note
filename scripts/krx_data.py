"""KRX 시세 데이터 조회 (pykrx 래퍼). 실행 환경에 실제 인터넷 접속이 필요합니다."""
from datetime import datetime, timedelta

import pandas as pd
from pykrx import stock

OHLCV_COLUMNS = ["시가", "고가", "저가", "종가", "거래량", "거래대금", "등락률"]


def market_snapshot(date: str, market: str = "ALL") -> pd.DataFrame:
    """지정일의 전종목 시세 스냅샷. 휴장일이면 빈 DataFrame."""
    df = stock.get_market_ohlcv_by_ticker(date, market=market)
    if df is None or df.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS)
    return df


def market_snapshots(dates: list[str], market: str = "ALL") -> dict[str, pd.DataFrame]:
    """날짜 리스트에 대한 스냅샷을 조회하고, 실제 거래가 있었던 날짜만 반환."""
    result = {}
    for d in dates:
        snap = market_snapshot(d, market=market)
        if not snap.empty:
            result[d] = snap
    return result


def recent_calendar_dates(as_of: str, lookback_days: int) -> list[str]:
    """as_of로부터 과거 lookback_days 달력일의 YYYYMMDD 문자열 목록(오래된 순)."""
    end = datetime.strptime(as_of, "%Y%m%d")
    dates = [(end - timedelta(days=i)).strftime("%Y%m%d") for i in range(lookback_days, -1, -1)]
    return dates


def ticker_name(ticker: str) -> str:
    try:
        return stock.get_market_ticker_name(ticker)
    except Exception:
        return ticker
