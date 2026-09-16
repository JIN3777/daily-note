"""섹션 2: 거래량 폭증(전일 대비 500~1000%) 후 급감(전일 대비 25% 이하) + 5일선 이격 스크리닝.

패턴 판정 자체는 최근 며칠간의 시계열이 필요하지만(폭증일 -> 며칠 뒤 급감일), 매일 노트에는
"오늘이 급감일인 종목"만 보여주는 것이 기본 동작이다(only_target_date=True).
"""
import argparse
import json
from datetime import datetime

import krx_data
import pattern_logic

# crash_window_days(급감일 탐색 범위) + MA5 + 폭증일 등락비 계산에 필요한 최소 거래일수를
# 감안해 달력일로 넉넉히 잡은 기본값. 90일씩 긁어올 필요는 없음.
DEFAULT_LOOKBACK_CALENDAR_DAYS = 35


def build_section2(
    as_of: str,
    lookback_calendar_days: int = DEFAULT_LOOKBACK_CALENDAR_DAYS,
    market: str = "ALL",
    only_target_date: bool = True,
    **pattern_kwargs,
) -> list[dict]:
    dates = krx_data.recent_calendar_dates(as_of, lookback_calendar_days)
    snapshots = krx_data.market_snapshots(dates, market=market)
    panel = pattern_logic.build_ticker_panel(snapshots)
    matched = pattern_logic.find_volume_spike_crash_patterns(panel, **pattern_kwargs)

    for item in matched:
        item["name"] = krx_data.ticker_name(item["ticker"])

    if only_target_date:
        target = datetime.strptime(as_of, "%Y%m%d").strftime("%Y-%m-%d")
        matched = [item for item in matched if item["crash_date"] == target]

    matched.sort(key=lambda r: r["crash_date"], reverse=True)
    return matched


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="거래량 폭증→급감 + 5일선 이격 스크리닝")
    parser.add_argument("--date", required=True, help="기준일 YYYYMMDD (이 날짜가 급감일인 종목만 표시)")
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=DEFAULT_LOOKBACK_CALENDAR_DAYS,
        help="패턴 판정에 사용할 과거 달력일 수 (결과 표시 범위가 아니라 계산용 조회 범위)",
    )
    parser.add_argument(
        "--all-window",
        action="store_true",
        help="기준일뿐 아니라 조회 기간(lookback-days) 내 모든 매치를 표시",
    )
    parser.add_argument("--out", help="결과를 저장할 JSON 경로")
    args = parser.parse_args()

    result = build_section2(
        args.date, lookback_calendar_days=args.lookback_days, only_target_date=not args.all_window
    )
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"저장 완료: {args.out} ({len(result)}건)")
    else:
        print(output)
