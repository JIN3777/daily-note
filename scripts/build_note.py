"""섹션 1/2 결과(JSON)를 마크다운 노트 + 브라우저에서 보는 HTML 페이지로 변환."""
import argparse
import html
import json
from datetime import datetime

from build_index import update_index
from config import NOTES_DIR


def _fmt_volume(volume: int) -> str:
    return f"{volume / 10000:,.0f}만 주"


def _fmt_date_kr(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y%m%d") if len(date_str) == 8 else datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.year}년 {dt.month}월 {dt.day}일"


def _to_date_obj(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y%m%d") if len(date_str) == 8 else datetime.strptime(date_str, "%Y-%m-%d")


# ---------------------------------------------------------------------------
# 마크다운
# ---------------------------------------------------------------------------


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
        news = item.get("news")
        if news:
            if news.get("body"):
                lines.append(f"**{news['title']}**")
                lines.append("")
                lines.append(news["body"])
            else:
                # 본문 추출 실패 시, 최소한 원문을 찾아갈 수 있게 링크는 남겨둔다.
                lines.append(f"**[{news['title']}]({news['url']})**")
            lines.append("")
            lines.append(f"[{news.get('source', '')}, {news['pub_date']}]")
        else:
            lines.append("_(관련기사 없음 / 미조회)_")
        lines.append("")
        lines.append("**◎ 공시**")
        if item.get("disclosures"):
            for d in item["disclosures"]:
                lines.append(f"- [{d['title']}]({d['url']}) — {d['submitter']}, {d['date']}")
        else:
            lines.append("- _(공시 없음 / 미조회)_")
        if item.get("chart"):
            lines.append("")
            lines.append(f"![{item['name']} 차트]({item['chart']})")
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


# ---------------------------------------------------------------------------
# HTML (브라우저에서 보는 페이지)
# ---------------------------------------------------------------------------

_HTML_STYLE = """
:root {
  color-scheme: light dark;
  --bg: #ffffff; --fg: #1a1a1a; --muted: #6b7280; --card: #f8f9fb;
  --border: #e5e7eb; --accent: #c0392b; --accent-bg: #fdecea;
  --accent2: #2563eb; --accent2-bg: #eef2ff; --link: #2563eb;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16181d; --fg: #e6e6e6; --muted: #9aa0a6; --card: #1e2128;
    --border: #2b2f38; --accent: #ff6b5e; --accent-bg: #3a2020;
    --accent2: #6ea8fe; --accent2-bg: #1c2333; --link: #6ea8fe;
  }
}
* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--fg); margin: 0; padding: 24px 16px 64px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Malgun Gothic", sans-serif;
  line-height: 1.55;
}
.wrap { max-width: 760px; margin: 0 auto; }
.topnav { margin-bottom: 20px; }
.topnav a { color: var(--muted); text-decoration: none; font-size: 14px; }
.topnav a:hover { color: var(--link); }
h1 { font-size: 22px; margin: 0 0 4px; }
h2 { font-size: 17px; margin: 36px 0 14px; padding-bottom: 8px; border-bottom: 2px solid var(--border); }
.section-note { color: var(--muted); font-size: 13px; margin: -8px 0 16px; }
.card {
  background: var(--card); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px 18px; margin-bottom: 14px;
}
.card-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }
.name { font-size: 16px; font-weight: 600; }
.badge {
  font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 999px;
}
.badge.limit-up { color: var(--accent); background: var(--accent-bg); }
.badge.high-volume { color: var(--accent2); background: var(--accent2-bg); }
.metric { color: var(--muted); font-size: 14px; margin-bottom: 10px; }
.metric .up { color: var(--accent); font-weight: 600; }
.subhead { font-size: 13px; font-weight: 700; color: var(--muted); margin: 12px 0 6px; }
.chart-img { width: 100%; border-radius: 8px; border: 1px solid var(--border); margin-top: 14px; display: block; }
.news-title { font-size: 14px; font-weight: 700; margin-bottom: 6px; }
.news-title a { color: var(--link); text-decoration: none; }
.news-title a:hover { text-decoration: underline; }
.news-body { font-size: 14px; line-height: 1.6; margin: 0 0 6px; white-space: pre-line; }
.news-cite { color: var(--muted); font-size: 13px; margin: 0; }
.disc-item { font-size: 14px; margin-bottom: 8px; }
.disc-item a { color: var(--link); text-decoration: none; }
.disc-item a:hover { text-decoration: underline; }
.empty { color: var(--muted); font-size: 14px; }
.gap-pos { color: #16a34a; }
.gap-neg { color: var(--accent); }
</style>
"""


def _esc(v) -> str:
    return html.escape(str(v)) if v is not None else ""


def render_section1_html(items: list[dict]) -> str:
    if not items:
        return '<h2>1. 상한가 / 거래량 1,000만주 이상 종목</h2><p class="empty">해당 종목 없음</p>'

    cards = []
    for item in items:
        badge = (
            '<span class="badge limit-up">상한가</span>'
            if item["is_limit_up"]
            else '<span class="badge high-volume">거래량 급증</span>'
        )
        news = item.get("news")
        if news:
            if news.get("body"):
                title_html = f'<div class="news-title">{_esc(news["title"])}</div>'
                body_html = f'<p class="news-body">{_esc(news["body"])}</p>'
            else:
                # 본문 추출 실패 시, 최소한 원문을 찾아갈 수 있게 링크는 남겨둔다.
                title_html = (
                    f'<div class="news-title">'
                    f'<a href="{_esc(news["url"])}" target="_blank" rel="noopener">{_esc(news["title"])}</a>'
                    f"</div>"
                )
                body_html = ""
            news_html = (
                title_html
                + body_html
                + f'<p class="news-cite">[{_esc(news.get("source", ""))}, {_esc(news["pub_date"])}]</p>'
            )
        else:
            news_html = '<p class="empty">관련기사 없음 / 미조회</p>'

        disc_html = "".join(
            f'<div class="disc-item">▸ <a href="{_esc(d["url"])}" target="_blank" rel="noopener">{_esc(d["title"])}</a>'
            f' <span class="section-note">— {_esc(d["submitter"])}, {_esc(d["date"])}</span></div>'
            for d in item.get("disclosures", [])
        ) or '<p class="empty">공시 없음 / 미조회</p>'

        chart_html = (
            f'<img class="chart-img" src="{_esc(item["chart"])}" alt="{_esc(item["name"])} 차트">'
            if item.get("chart")
            else ""
        )

        cards.append(
            f"""
<div class="card">
  <div class="card-head"><span class="name">{_esc(item['name'])}</span>{badge}</div>
  <div class="metric"><span class="up">{item['change_pct']:+.2f}%</span> · 거래량 {_fmt_volume(item['volume'])}</div>
  <div class="subhead">◎ 관련기사</div>
  {news_html}
  <div class="subhead">◎ 공시</div>
  {disc_html}
  {chart_html}
</div>"""
        )
    return f'<h2>1. 상한가 / 거래량 1,000만주 이상 종목</h2>{"".join(cards)}'


def render_section2_html(items: list[dict]) -> str:
    note = '<p class="section-note">폭증 전일 대비 500~1000%, 급감 전일 대비 25% 이하, 급감일 종가가 5일선 대비 -3% 이내</p>'
    if not items:
        return f"<h2>2. 거래량 폭증 후 급감 패턴 종목</h2>{note}" + '<p class="empty">해당 종목 없음</p>'

    cards = []
    for item in items:
        gap_class = "gap-pos" if item["ma5_gap_pct"] >= 0 else "gap-neg"
        cards.append(
            f"""
<div class="card">
  <div class="card-head"><span class="name">{_esc(item['name'])}</span></div>
  <div class="metric">폭증일 {_esc(item['spike_date'])} · 거래량 {_fmt_volume(item['spike_volume'])}
    (전일比 {item['spike_ratio_pct']:.0f}%)</div>
  <div class="metric">급감일 {_esc(item['crash_date'])} · 거래량 {_fmt_volume(item['crash_volume'])}
    (전일比 {item['crash_ratio_pct']:.0f}%)</div>
  <div class="metric">종가 {item['crash_close']:,.0f}원 / 5일선 {item['crash_ma5']:,.0f}원
    (이격률 <span class="{gap_class}">{item['ma5_gap_pct']:+.2f}%</span>)</div>
</div>"""
        )
    return f"<h2>2. 거래량 폭증 후 급감 패턴 종목</h2>{note}{''.join(cards)}"


def build_note_html(date: str, section1_items: list[dict], section2_items: list[dict]) -> str:
    title = f"{_fmt_date_kr(date)} 시황 노트"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>{_HTML_STYLE}
</head>
<body>
<div class="wrap">
  <div class="topnav"><a href="index.html">&larr; 전체 노트 목록</a></div>
  <h1>{_esc(title)}</h1>
  {render_section1_html(section1_items)}
  {render_section2_html(section2_items)}
</div>
</body>
</html>"""


def save_note(date: str, section1_items: list[dict], section2_items: list[dict]):
    """마크다운(.md) + HTML(.html)을 둘 다 저장하고, 목록(index.html)을 갱신한다."""
    dt = _to_date_obj(date)
    date_str = f"{dt:%Y-%m-%d}"

    md_path = NOTES_DIR / f"{date_str}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_note(date, section1_items, section2_items))

    html_path = NOTES_DIR / f"{date_str}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_note_html(date, section1_items, section2_items))

    update_index(date_str, len(section1_items), len(section2_items))
    return md_path, html_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="섹션 JSON을 노트(마크다운+HTML)로 변환")
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--section1", required=True, help="섹션1 JSON 경로")
    parser.add_argument("--section2", required=True, help="섹션2 JSON 경로")
    args = parser.parse_args()

    with open(args.section1, encoding="utf-8") as f:
        section1_items = json.load(f)
    with open(args.section2, encoding="utf-8") as f:
        section2_items = json.load(f)

    md_path, html_path = save_note(args.date, section1_items, section2_items)
    print(f"노트 생성 완료: {md_path}")
    print(f"HTML 생성 완료: {html_path}")
