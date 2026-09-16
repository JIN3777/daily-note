"""구글 뉴스(Google News) RSS 검색. 별도 API 키/가입이 필요 없다.

네이버 뉴스 검색 오픈API는 2026년 기준 신규 발급을 받지 않아(기존 제휴 업체만 유지),
가입 없이 바로 쓸 수 있는 Google News RSS로 대체했다. 종목마다 여러 기사를 나열하는
대신, 그날 상승/거래량 급증에 가장 영향을 줬을 법한 기사 1건만 골라 링크로 남긴다.

기사 본문을 직접 가져와 보여주는 것도 시도해봤지만, 구글 뉴스 링크가 언론사 원문이
아니라 구글 자체 래퍼 페이지로 연결되는 경우가 많아(비공식 우회 방법도 신뢰도가 낮음)
매번 실패하는 게 더 흔했다. 그래서 링크만 확실하게 남기는 쪽으로 정리했다.
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests

RSS_URL = "https://news.google.com/rss/search"

# 신뢰도가 높다고 판단하는 언론사 (앞쪽일수록 우선순위 높음). 부분 일치로 비교한다.
TRUSTED_SOURCES = [
    "한국경제", "연합뉴스", "로이터", "Reuters", "블룸버그", "Bloomberg",
    "매일경제", "조선일보", "중앙일보", "동아일보", "서울경제", "이데일리",
    "머니투데이", "파이낸셜뉴스", "헤럴드경제", "한국경제TV", "뉴시스",
]


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
    }
