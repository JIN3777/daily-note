import pandas as pd
from pattern_logic import build_ticker_panel, find_volume_spike_crash_patterns

DATES = [f"2026090{i}" for i in range(1, 8)]  # 20260901 ~ 20260907


def make_snapshots():
    """
    AAA: day5 거래량 폭증(7배), day6 거래량 급감(20%) + 종가가 5일선 위 -> 매칭 기대
    BBB: day5 거래량 폭증(15배, 범위 밖) -> 매칭 안 됨
    CCC: day5 거래량 폭증(7배), day6 급감하지만 5일선 대비 -9% 이탈 -> 매칭 안 됨(초과 이탈)
    """
    base_vol = 100_000
    data = {
        "AAA": {
            "close": [1000, 1000, 1000, 1000, 1050, 1020, 1010],
            "volume": [base_vol] * 4 + [base_vol * 7, base_vol * 7 * 0.2, base_vol],
        },
        "BBB": {
            "close": [1000, 1000, 1000, 1000, 1050, 1020, 1010],
            "volume": [base_vol] * 4 + [base_vol * 15, base_vol * 15 * 0.2, base_vol],
        },
        "CCC": {
            "close": [1000, 1000, 1000, 1000, 1050, 900, 900],
            "volume": [base_vol] * 4 + [base_vol * 7, base_vol * 7 * 0.2, base_vol],
        },
    }

    snapshots = {}
    for day_idx, date in enumerate(DATES):
        rows = {}
        for ticker, series in data.items():
            rows[ticker] = {
                "종가": series["close"][day_idx],
                "거래량": int(series["volume"][day_idx]),
            }
        snapshots[date] = pd.DataFrame.from_dict(rows, orient="index")
    return snapshots


def test_spike_crash_detected_for_aaa_only():
    panel = build_ticker_panel(make_snapshots())
    results = find_volume_spike_crash_patterns(panel, crash_window_days=5)
    tickers = {r["ticker"] for r in results}

    assert "AAA" in tickers
    assert "BBB" not in tickers  # 폭증 배율이 범위(5~10배) 밖
    assert "CCC" not in tickers  # 급감일 5일선 이격이 -3% 초과


def test_aaa_match_fields():
    panel = build_ticker_panel(make_snapshots())
    results = find_volume_spike_crash_patterns(panel, crash_window_days=5)
    aaa = next(r for r in results if r["ticker"] == "AAA")

    assert aaa["spike_date"] == "2026-09-05"
    assert aaa["crash_date"] == "2026-09-06"
    assert aaa["crash_ratio_pct"] <= 25
    assert aaa["spike_ratio_pct"] >= 500
