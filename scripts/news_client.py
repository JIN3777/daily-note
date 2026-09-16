"""구글 뉴스(Google News) RSS 검색. 별도 API 키/가입이 필요 없다.

네이버 뉴스 검색 오픈API는 2026년 기준 신규 발급을 받지 않아(기존 제휴 업체만 유지),
가입 없이 바로 쓸 수 있는 Google News RSS로 대체한다. 기사 링크는 구글 뉴스의
리다이렉트 링크라 클릭하면 실제 언론사 원문으로 이동한다.
"""
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests

RSS_URL = "https://news.google.com/rss/search"


def search_news(query: str, target_date: str, display: int = 10) -> list[dict]:
    """query 관련 뉴스 중 target_date(YYYYMMDD)에 발행된 기사만 반환."""
    dt = datetime.strptime(target_date, "%Y%m%d")
    next_dt = dt + timedelta(days=1)
    q = f"{query} after:{dt:%Y-%m-%d} before:{next_dt:%Y-%m-%d}"

    params = {"q": q, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
    resp = requests.get(RSS_URL, params=params, timeout=20)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    target = dt.date()
    matched = []
    for item in root.findall(".//item")[:display]:
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        # Google News 제목은 보통 "기사제목 - 언론사" 형식이라 언론사 접미사를 떼어낸다.
        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)]

        pub_date_raw = item.findtext("pubDate")
        try:
            pub_date = parsedate_to_datetime(pub_date_raw).date() if pub_date_raw else None
        except Exception:
            pub_date = None
        if pub_date != target:
            continue

        matched.append(
            {
                "title": title,
                "summary": source,
                "url": (item.findtext("link") or "").strip(),
                "press_link": (item.findtext("link") or "").strip(),
                "pub_date": target.isoformat(),
            }
        )
    return matched
