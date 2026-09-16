"""매일 실행하는 진입점: 섹션1 + 섹션2 스크리닝 -> 노트 생성.

사용 예:
    python scripts/run_daily.py --date 20260916
"""
import argparse
from concurrent.futures import ThreadPoolExecutor

from build_note import save_note
from section1_limit_up_volume import build_section1
from section2_volume_pattern import DEFAULT_LOOKBACK_CALENDAR_DAYS, build_section2


def main():
    parser = argparse.ArgumentParser(description="일일 시황 노트 생성")
    parser.add_argument("--date", required=True, help="YYYYMMDD (기준 거래일)")
    parser.add_argument("--no-news", action="store_true", help="뉴스 조회 생략")
    parser.add_argument("--no-disclosures", action="store_true", help="공시 조회 생략")
    parser.add_argument("--no-chart", action="store_true", help="차트 이미지 생성 생략")
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=DEFAULT_LOOKBACK_CALENDAR_DAYS,
        help="섹션2 패턴 판정용 과거 달력일 조회 범위 (결과는 항상 --date 당일 급감 종목만 표시)",
    )
    args = parser.parse_args()

    print(f"[1/2] 섹션1(상한가/거래량) + 섹션2(폭증→급감, 최근 {args.lookback_days}일) 동시 스크리닝 중... ({args.date})")
    with ThreadPoolExecutor(max_workers=2) as executor:
        section1_future = executor.submit(
            build_section1,
            args.date,
            with_news=not args.no_news,
            with_disclosures=not args.no_disclosures,
            with_chart=not args.no_chart,
        )
        section2_future = executor.submit(
            build_section2, args.date, lookback_calendar_days=args.lookback_days
        )
        section1_items = section1_future.result()
        section2_items = section2_future.result()
    print(f"  -> 섹션1 {len(section1_items)}건, 섹션2 {len(section2_items)}건 발견")

    print("[2/2] 노트 작성 중...")
    md_path, html_path = save_note(args.date, section1_items, section2_items)
    print(f"완료: {md_path}")
    print(f"브라우저로 보기: {html_path}  (또는 notes/index.html 에서 전체 목록)")


if __name__ == "__main__":
    main()
