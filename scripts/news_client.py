"""구글 뉴스(Google News) RSS 검색 + 본문 추출. 별도 API 키/가입이 필요 없다.

네이버 뉴스 검색 오픈API는 2026년 기준 신규 발급을 받지 않아(기존 제휴 업체만 유지),
가입 없이 바로 쓸 수 있는 Google News RSS로 대체했다. 종목마다 여러 기사를 나열하는
대신, 그날 상승/거래량 급증에 가장 영향을 줬을 법한 기사 1건만 골라 본문을 붙인다.
"""
import base64
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup
from readability import Document

RSS_URL = "https://news.google.com/rss/search"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
_URL_IN_BYTES_RE = re.compile(rb'https?://[^\x00-\x1f\x7f<>"\' ]{8,}')

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


def _title_mentions_query(title: str, query: str) -> int:
    """종목명이 제목에 직접 들어간 기사를 우선한다 (0=제목에 있음, 1=없음).

    "코스피 마감시황"처럼 종목명이 본문 어딘가에만 스치듯 언급된 기사가
    구글 검색 결과에 섞여 들어오는 걸 걸러내기 위함.
    """
    return 0 if query in title else 1


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


def _decode_google_news_redirect(url: str) -> str | None:
    """news.google.com/rss/articles/<id> 형태의 링크에서, 인코딩된 id 안에 함께 들어있는
    원문 언론사 URL을 최대한 추출해본다 (Google이 공식으로 제공하는 방법이 아니라
    best-effort 디코딩; 실패해도 예외를 던지지 않고 None을 반환).
    """
    m = re.search(r"/articles/([^/?]+)", url)
    if not m:
        return None
    encoded = m.group(1)
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        decoded = base64.urlsafe_b64decode(padded)
    except Exception:
        return None

    found = _URL_IN_BYTES_RE.search(decoded)
    if not found:
        return None
    candidate = found.group(0).decode("utf-8", errors="ignore")
    return candidate if "google.com" not in candidate else None


def fetch_article_body(url: str, max_chars: int = 1000) -> str:
    """기사 원문 페이지에서 본문 텍스트를 추출 (best-effort). 실패하면 빈 문자열."""
    fetch_url = url
    for attempt in range(2):
        try:
            resp = requests.get(fetch_url, headers=REQUEST_HEADERS, timeout=15, allow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"[경고] 기사 본문 요청 실패 ({fetch_url}): {e}")
            return ""

        try:
            doc = Document(resp.text)
            soup = BeautifulSoup(doc.summary(), "html.parser")
            text = _WS_RE.sub(" ", soup.get_text(separator=" ")).strip()
        except Exception as e:
            print(f"[경고] 기사 본문 파싱 실패 ({fetch_url}): {e}")
            text = ""

        # 구글 뉴스 리다이렉트 페이지에 그대로 머물러서(=원문 사이트로 못 넘어가서)
        # 본문이 거의 안 뽑힌 경우, 인코딩된 링크 속 원문 URL을 추출해 한 번 더 시도.
        if len(text) < 50 and attempt == 0:
            decoded_url = _decode_google_news_redirect(url)
            if decoded_url and decoded_url != fetch_url:
                print(f"[정보] 구글 뉴스 리다이렉트 우회, 원문으로 재시도: {decoded_url}")
                fetch_url = decoded_url
                continue

        if not text:
            print(f"[경고] 기사 본문이 비어있음 ({fetch_url})")
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "…"
        return text
    return ""


def get_top_news(query: str, target_date: str) -> dict | None:
    """당일 기사 중 (1) 제목에 종목명이 직접 언급되고 (2) 신뢰 언론사인 기사를 우선 선택.

    같은 우선순위 내에서는 구글 뉴스가 매긴 원래 관련도 순서(=수집 순서)를 그대로
    유지한다 (발행 시각순으로 재정렬하면 오히려 관련 없는 기사가 앞으로 오는 경우가 있었음).
    """
    candidates = _fetch_candidates(query, target_date)
    if not candidates:
        return None

    candidates.sort(key=lambda c: (_title_mentions_query(c["title"], query), _source_rank(c["source"])))
    best = candidates[0]

    return {
        "title": best["title"],
        "source": best["source"],
        "url": best["url"],
        "pub_date": best["pub_dt"].date().isoformat(),
        "body": fetch_article_body(best["url"]),
    }
