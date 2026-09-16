"""매일 실행하는 진입점: 섹션1 + 섹션2 스크리닝 -> 노트 생성.

사용 예:
    python scripts/run_daily.py --date 20260916
"""
import argparse
from datetime import datetime

from build_note import build_note
from config import NOTES_DIR
from section1_limit_up_volume import build_section1
from section2_volume_pattern import build_section2


def main():
    parser = argparse.ArgumentParser(description="일일 시황 노트 생성")
    parser.add_argument("--date", required=True, help="YYYYMMDD (기준 거래일)")
    parser.add_argument("--no-news", action="store_true", help="뉴스 조회 생략")
    parser.add_argument("--no-disclosures", action="store_true", help="공시 조회 생략")
    parser.add_argument(
        "--lookback-days", type=int, default=90, help="섹션2용 과거 달력일 조회 범위"
    )
    args = parser.parse_args()

    print(f"[1/3] 섹션1 (상한가/거래량) 스크리닝 중... ({args.date})")
    section1_items = build_section1(
        args.date, with_news=not args.no_news, with_disclosures=not args.no_disclosures
    )
    print(f"  -> {len(section1_items)}건 발견")

    print(f"[2/3] 섹션2 (거래량 폭증→급감) 스크리닝 중... (최근 {args.lookback_days}일)")
    section2_items = build_section2(args.date, lookback_calendar_days=args.lookback_days)
    print(f"  -> {len(section2_items)}건 발견")

    print("[3/3] 노트 작성 중...")
    note = build_note(args.date, section1_items, section2_items)
    dt = datetime.strptime(args.date, "%Y%m%d")
    out_path = NOTES_DIR / f"{dt:%Y-%m-%d}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(note)
    print(f"완료: {out_path}")


if __name__ == "__main__":
    main()
