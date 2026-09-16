"""섹션 1/2 결과(JSON)를 이미지 예시와 같은 형식의 마크다운 노트로 변환."""
import argparse
import json
from datetime import datetime

from config import NOTES_DIR


def _fmt_volume(volume: int) -> str:
    return f"{volume / 10000:,.0f}만 주"


def _fmt_date_kr(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y%m%d") if len(date_str) == 8 else datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.year}년 {dt.month}월 {dt.day}일"


def render_section1(date: str, items: list[dict]) -> str:
    lines = ["## 1. 상한가 / 거래량 1,000만주 이상 종목", ""]
    if not items:
        lines.append("_해당 종목 없음_\n")
        return "\n".join(lines)

    for item in items:
        tag = "상한가" if item["is_limit_up"] else "거래량 급증"
        lines.append(f"### {item['name']} ({tag})")
        lines.append(f"— 등락률 {item['change_pct']:+.2f}% / 거래량 {_fmt_volume(item['volume'])}")
        lines.append("")
        lines.append("**◎ 관련기사**")
        if item.get("news"):
            for n in item["news"]:
                lines.append(f"- [{n['title']}]({n['url']}) — {n['pub_date']}")
                if n.get("summary"):
                    lines.append(f"  > {n['summary']}")
        else:
            lines.append("- _(관련기사 없음 / 미조회)_")
        lines.append("")
        lines.append("**◎ 공시**")
        if item.get("disclosures"):
            for d in item["disclosures"]:
                lines.append(f"- [{d['title']}]({d['url']}) — {d['submitter']}, {d['date']}")
        else:
            lines.append("- _(공시 없음 / 미조회)_")
        lines.append("")
        lines.append("_(차트 캡처 첨부 위치)_")
        lines.append("\n---\n")
    return "\n".join(lines)


def render_section2(items: list[dict]) -> str:
    lines = [
        "## 2. 거래량 폭증 후 급감 패턴 종목",
        "_(폭증 전일 대비 500~1000%, 급감 전일 대비 25% 이하, 급감일 종가가 5일선 대비 -3% 이내)_",
        "",
    ]
    if not items:
        lines.append("_해당 종목 없음_\n")
        return "\n".join(lines)

    for item in items:
        lines.append(f"### {item['name']}")
        lines.append(
            f"- 폭증일: {item['spike_date']}, 거래량 {_fmt_volume(item['spike_volume'])}"
            f" (전일 대비 {item['spike_ratio_pct']:.0f}%)"
        )
        lines.append(
            f"- 급감일: {item['crash_date']}, 거래량 {_fmt_volume(item['crash_volume'])}"
            f" (전일 대비 {item['crash_ratio_pct']:.0f}%)"
        )
        lines.append(
            f"- 급감일 종가 {item['crash_close']:,.0f}원 / 5일선 {item['crash_ma5']:,.0f}원"
            f" (이격률 {item['ma5_gap_pct']:+.2f}%)"
        )
        lines.append("")
    return "\n".join(lines)


def build_note(date: str, section1_items: list[dict], section2_items: list[dict]) -> str:
    header = f"# {_fmt_date_kr(date)} 시황 노트\n"
    return "\n".join([header, render_section1(date, section1_items), render_section2(section2_items)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="섹션 JSON을 노트 마크다운으로 변환")
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--section1", required=True, help="섹션1 JSON 경로")
    parser.add_argument("--section2", required=True, help="섹션2 JSON 경로")
    parser.add_argument("--out", help="저장 경로 (기본: notes/YYYY-MM-DD.md)")
    args = parser.parse_args()

    with open(args.section1, encoding="utf-8") as f:
        section1_items = json.load(f)
    with open(args.section2, encoding="utf-8") as f:
        section2_items = json.load(f)

    note = build_note(args.date, section1_items, section2_items)

    dt = datetime.strptime(args.date, "%Y%m%d")
    out_path = args.out or (NOTES_DIR / f"{dt:%Y-%m-%d}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(note)
    print(f"노트 생성 완료: {out_path}")
