"""KRX 시세 데이터 조회 (pykrx 래퍼). 실행 환경에 실제 인터넷 접속이 필요합니다."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pandas as pd

import config  # noqa: F401  (pykrx가 모듈 import 시점에 KRX_ID/KRX_PW를 읽으므로, .env 로딩이 먼저 실행돼야 함)
from pykrx import stock

OHLCV_COLUMNS = ["시가", "고가", "저가", "종가", "거래량", "거래대금", "등락률"]
MAX_WORKERS = 8


def market_snapshot(date: str, market: str = "ALL") -> pd.DataFrame:
    """지정일의 전종목 시세 스냅샷. 휴장일이면 빈 DataFrame.

    주말/공휴일에 조회하면 KRX가 빈 응답을 주고, pykrx가 그걸 파싱하다가
    KeyError를 던지는 경우가 있다. 자동 실행(cron 등) 중 공휴일마다 실패하지
    않도록, 그 경우도 "데이터 없음"으로 취급한다.
    """
    try:
        df = stock.get_market_ohlcv_by_ticker(date, market=market)
    except (KeyError, ValueError):
        return pd.DataFrame(columns=OHLCV_COLUMNS)
    if df is None or df.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS)
    return df


def market_snapshots(dates: list[str], market: str = "ALL") -> dict[str, pd.DataFrame]:
    """날짜 리스트에 대한 스냅샷을 병렬로 조회하고, 실제 거래가 있었던 날짜만 반환.

    하루씩 순차 조회하면 (섹션2 기본 35일 기준) KRX 요청만 35번 직렬로 나가서
    가장 큰 병목이었다. 날짜별 조회는 서로 독립적이라 스레드풀로 병렬 처리한다.
    """
    result = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        snapshots = executor.map(lambda d: market_snapshot(d, market), dates)
        for d, snap in zip(dates, snapshots):
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
