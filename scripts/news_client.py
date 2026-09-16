"""네이버 뉴스 검색 Open API 클라이언트. https://developers.naver.com/docs/serviceapi/search/news/news.md"""
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests

from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text or "").replace("&quot;", '"').replace("&amp;", "&")


def search_news(query: str, target_date: str, display: int = 10) -> list[dict]:
    """query 관련 뉴스 중 target_date(YYYYMMDD)와 같은 날 발행된 기사만 반환.

    네이버 뉴스 검색 API는 날짜 필터를 직접 지원하지 않으므로, 최신순으로
    가져온 뒤 pubDate가 target_date와 일치하는 기사만 걸러낸다.
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise RuntimeError("NAVER_CLIENT_ID/NAVER_CLIENT_SECRET이 설정되지 않았습니다 (.env 확인)")

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": "date"}
    resp = requests.get(SEARCH_URL, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    items = resp.json().get("items", [])

    target = datetime.strptime(target_date, "%Y%m%d").date()
    matched = []
    for item in items:
        try:
            pub_date = parsedate_to_datetime(item["pubDate"]).date()
        except Exception:
            continue
        if pub_date != target:
            continue
        matched.append(
            {
                "title": _strip_tags(item.get("title")),
                "summary": _strip_tags(item.get("description")),
                "url": item.get("originallink") or item.get("link"),
                "press_link": item.get("link"),
                "pub_date": pub_date.isoformat(),
            }
        )
    return matched
