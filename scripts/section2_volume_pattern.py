"""섹션 2: 거래량 폭증(전일 대비 500~1000%) 후 급감(전일 대비 25% 이하) + 5일선 이격 스크리닝."""
import argparse
import json

import krx_data
import pattern_logic


def build_section2(
    as_of: str,
    lookback_calendar_days: int = 90,
    market: str = "ALL",
    **pattern_kwargs,
) -> list[dict]:
    dates = krx_data.recent_calendar_dates(as_of, lookback_calendar_days)
    snapshots = krx_data.market_snapshots(dates, market=market)
    panel = pattern_logic.build_ticker_panel(snapshots)
    matched = pattern_logic.find_volume_spike_crash_patterns(panel, **pattern_kwargs)

    for item in matched:
        item["name"] = krx_data.ticker_name(item["ticker"])

    matched.sort(key=lambda r: r["crash_date"], reverse=True)
    return matched


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="거래량 폭증→급감 + 5일선 이격 스크리닝")
    parser.add_argument("--date", required=True, help="기준일 YYYYMMDD (이 날짜까지의 데이터를 조회)")
    parser.add_argument("--lookback-days", type=int, default=90, help="조회할 과거 달력일 수")
    parser.add_argument("--out", help="결과를 저장할 JSON 경로")
    args = parser.parse_args()

    result = build_section2(args.date, lookback_calendar_days=args.lookback_days)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"저장 완료: {args.out} ({len(result)}건)")
    else:
        print(output)
