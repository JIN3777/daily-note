import pandas as pd
from limit_up_logic import find_limit_up_and_high_volume


def make_snapshot():
    return pd.DataFrame(
        {
            "등락률": [29.91, 7.66, 1.2, -3.0],
            "거래량": [7_610_000, 13_920_000, 500_000, 9_999_999],
            "종가": [10000, 5000, 20000, 3000],
        },
        index=["003550", "047310", "005930", "000660"],
    )


def test_limit_up_detected():
    result = find_limit_up_and_high_volume(make_snapshot())
    tickers = {r["ticker"] for r in result}
    assert "003550" in tickers  # 상한가
    assert "047310" in tickers  # 거래량 1,000만주 이상
    assert "005930" not in tickers  # 둘 다 미달
    assert "000660" not in tickers  # 거래량 999만9999주는 기준 미달


def test_sorted_by_change_pct_desc():
    result = find_limit_up_and_high_volume(make_snapshot())
    changes = [r["change_pct"] for r in result]
    assert changes == sorted(changes, reverse=True)


def test_flags():
    result = find_limit_up_and_high_volume(make_snapshot())
    by_ticker = {r["ticker"]: r for r in result}
    assert by_ticker["003550"]["is_limit_up"] is True
    assert by_ticker["047310"]["is_limit_up"] is False
    assert by_ticker["047310"]["is_high_volume"] is True
