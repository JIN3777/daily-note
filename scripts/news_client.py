"""구글 뉴스(Google News) RSS 검색 + 본문 추출. 별도 API 키/가입이 필요 없다.

네이버 뉴스 검색 오픈API는 2026년 기준 신규 발급을 받지 않아(기존 제휴 업체만 유지),
가입 없이 바로 쓸 수 있는 Google News RSS로 대체했다. 종목마다 여러 기사를 나열하는
대신, 그날 상승/거래량 급증에 가장 영향을 줬을 법한 기사 1건만 골라 본문을 붙인다.
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup
from readability import Document

RSS_URL = "https://news.google.com/rss/search"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 신뢰도가 높다고 판단하는 언론사 (앞쪽일수록 우선순위 높음). 부분 일치로 비교한다.
TRUSTED_SOURCES = [
    "한국경제", "연합뉴스", "로이터", "Reuters", "블룸버그", "Bloomberg",
    "매일경제", "조선일보", "중앙일보", "동아일보", "서울경제", "이데일리",
    "머니투데이", "파이낸셜뉴스", "헤럴드경제", "한국경제TV", "뉴시스",
]

_WS_RE = re.compile(r"\s+")


def _source_rank(source: str) -> int:
    for i, name in enumerate(TRUSTED_SOURCES):
        if name in source:
            return i
    return len(TRUSTED_SOURCES)


def _fetch_candidates(query: str, target_date: str) -> list[dict]:
    """query 관련 뉴스 중 target_date(YYYYMMDD)에 발행된 기사 후보 전체 (정렬 전)."""
    dt = datetime.strptime(target_date, "%Y%m%d")
    next_dt = dt + timedelta(days=1)
    q = f"{query} after:{dt:%Y-%m-%d} before:{next_dt:%Y-%m-%d}"

    params = {"q": q, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
    resp = requests.get(RSS_URL, params=params, timeout=20)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    target = dt.date()
    candidates = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)]

        pub_date_raw = item.findtext("pubDate")
        try:
            pub_dt = parsedate_to_datetime(pub_date_raw) if pub_date_raw else None
        except Exception:
            pub_dt = None
        if pub_dt is None or pub_dt.date() != target:
            continue

        candidates.append(
            {
                "title": title,
                "source": source,
                "url": (item.findtext("link") or "").strip(),
                "pub_dt": pub_dt,
            }
        )
    return candidates


def fetch_article_body(url: str, max_chars: int = 800) -> str:
    """기사 원문 페이지에서 본문 텍스트를 추출 (best-effort). 실패하면 빈 문자열."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        doc = Document(resp.text)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        text = _WS_RE.sub(" ", soup.get_text(separator=" ")).strip()
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "…"
        return text
    except Exception:
        return ""


def get_top_news(query: str, target_date: str) -> dict | None:
    """당일 기사 중 신뢰 언론사 우선, 그다음 가장 이른 시각(사건에 가장 근접) 1건을 골라 본문과 함께 반환."""
    candidates = _fetch_candidates(query, target_date)
    if not candidates:
        return None

    candidates.sort(key=lambda c: (_source_rank(c["source"]), c["pub_dt"]))
    best = candidates[0]

    return {
        "title": best["title"],
        "source": best["source"],
        "url": best["url"],
        "pub_date": best["pub_dt"].date().isoformat(),
        "body": fetch_article_body(best["url"]),
    }
