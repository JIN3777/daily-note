import pandas as pd
import section2_volume_pattern as s2


def make_snapshots():
    base_vol = 100_000
    dates = [f"2026090{i}" for i in range(1, 8)]
    close = [1000, 1000, 1000, 1000, 1050, 1020, 1010]
    volume = [base_vol] * 4 + [base_vol * 7, base_vol * 7 * 0.2, base_vol]

    snapshots = {}
    for i, date in enumerate(dates):
        snapshots[date] = pd.DataFrame.from_dict(
            {"AAA": {"종가": close[i], "거래량": int(volume[i])}}, orient="index"
        )
    return snapshots


def test_only_target_date_filters_to_crash_day(monkeypatch):
    monkeypatch.setattr(s2.krx_data, "recent_calendar_dates", lambda as_of, n: list(make_snapshots()))
    monkeypatch.setattr(s2.krx_data, "market_snapshots", lambda dates, market="ALL": make_snapshots())
    monkeypatch.setattr(s2.krx_data, "ticker_name", lambda ticker: "테스트종목")

    on_crash_day = s2.build_section2("20260906", crash_window_days=5)
    assert len(on_crash_day) == 1
    assert on_crash_day[0]["crash_date"] == "2026-09-06"

    on_other_day = s2.build_section2("20260907", crash_window_days=5)
    assert on_other_day == []


def test_all_window_returns_match_regardless_of_date(monkeypatch):
    monkeypatch.setattr(s2.krx_data, "recent_calendar_dates", lambda as_of, n: list(make_snapshots()))
    monkeypatch.setattr(s2.krx_data, "market_snapshots", lambda dates, market="ALL": make_snapshots())
    monkeypatch.setattr(s2.krx_data, "ticker_name", lambda ticker: "테스트종목")

    result = s2.build_section2("20260907", crash_window_days=5, only_target_date=False)
    assert len(result) == 1
    assert result[0]["crash_date"] == "2026-09-06"
