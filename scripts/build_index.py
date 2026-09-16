"""notes/index.json(날짜별 요약)을 갱신하고, notes/index.html(전체 목록 페이지)을 생성."""
import html
import json
from datetime import datetime

from config import NOTES_DIR

INDEX_JSON = NOTES_DIR / "index.json"

_STYLE = """
:root {
  color-scheme: light dark;
  --bg: #ffffff; --fg: #1a1a1a; --muted: #6b7280; --card: #f8f9fb;
  --border: #e5e7eb; --link: #2563eb; --accent: #c0392b; --accent2: #2563eb;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16181d; --fg: #e6e6e6; --muted: #9aa0a6; --card: #1e2128;
    --border: #2b2f38; --link: #6ea8fe; --accent: #ff6b5e; --accent2: #6ea8fe;
  }
}
* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--fg); margin: 0; padding: 24px 16px 64px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Malgun Gothic", sans-serif;
}
.wrap { max-width: 640px; margin: 0 auto; }
h1 { font-size: 22px; margin: 0 0 20px; }
.row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  background: var(--card); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 18px; margin-bottom: 10px; text-decoration: none; color: var(--fg);
}
.row:hover { border-color: var(--link); }
.date { font-weight: 600; font-size: 15px; }
.counts { font-size: 13px; color: var(--muted); white-space: nowrap; }
.counts .n1 { color: var(--accent); font-weight: 600; }
.counts .n2 { color: var(--accent2); font-weight: 600; }
.empty { color: var(--muted); }
"""


def _load_entries() -> list[dict]:
    if not INDEX_JSON.exists():
        return []
    with open(INDEX_JSON, encoding="utf-8") as f:
        return json.load(f)


def _save_entries(entries: list[dict]):
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def update_index(date_str: str, section1_count: int, section2_count: int):
    """date_str: 'YYYY-MM-DD'. 같은 날짜가 이미 있으면 갱신, 없으면 추가 후 index.html 재생성."""
    entries = _load_entries()
    entries = [e for e in entries if e["date"] != date_str]
    entries.append({"date": date_str, "section1_count": section1_count, "section2_count": section2_count})
    entries.sort(key=lambda e: e["date"], reverse=True)
    _save_entries(entries)
    _write_index_html(entries)


def _write_index_html(entries: list[dict]):
    if not entries:
        rows = '<p class="empty">아직 생성된 노트가 없습니다.</p>'
    else:
        rows = "".join(
            f'<a class="row" href="{html.escape(e["date"])}.html">'
            f'<span class="date">{_fmt_date_kr(e["date"])}</span>'
            f'<span class="counts"><span class="n1">상한가/거래량 {e["section1_count"]}</span> · '
            f'<span class="n2">패턴 {e["section2_count"]}</span></span>'
            f"</a>"
            for e in entries
        )
    doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>시황 노트 목록</title>
<style>{_STYLE}</style>
</head>
<body>
<div class="wrap">
  <h1>매일 시황 노트</h1>
  {rows}
</div>
</body>
</html>"""
    with open(NOTES_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(doc)


def _fmt_date_kr(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.year}년 {dt.month}월 {dt.day}일"


if __name__ == "__main__":
    # notes/index.json에 저장된 기록을 바탕으로 index.html만 다시 생성 (예: 파일을 직접 지웠을 때)
    _write_index_html(_load_entries())
    print(f"index.html 재생성 완료: {NOTES_DIR / 'index.html'}")
