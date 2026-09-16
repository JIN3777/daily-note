"""DART(전자공시시스템) Open API 클라이언트. https://opendart.fss.or.kr"""
import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import requests

from config import CACHE_DIR, DART_API_KEY

CORP_CODE_CACHE = CACHE_DIR / "corpCode.xml"
LIST_URL = "https://opendart.fss.or.kr/api/list.json"
CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
DETAIL_URL_TMPL = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"


def _download_corp_code_map(cache_path: Path = CORP_CODE_CACHE) -> Path:
    if cache_path.exists():
        return cache_path
    if not DART_API_KEY:
        raise RuntimeError("DART_API_KEY가 설정되지 않았습니다 (.env 확인)")
    resp = requests.get(CORP_CODE_URL, params={"crtfc_key": DART_API_KEY}, timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        cache_path.write_bytes(zf.read("CORPCODE.xml"))
    return cache_path


def build_ticker_to_corp_code() -> dict[str, str]:
    """종목코드(6자리) -> DART corp_code(8자리) 매핑을 만든다. 최초 1회 다운로드 후 캐시."""
    path = _download_corp_code_map()
    tree = ET.parse(path)
    mapping = {}
    for item in tree.getroot().findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        corp_code = (item.findtext("corp_code") or "").strip()
        if stock_code:
            mapping[stock_code] = corp_code
    return mapping


def get_disclosures(corp_code: str, date: str) -> list[dict]:
    """date(YYYYMMDD)에 해당 기업이 제출한 공시 목록."""
    if not DART_API_KEY:
        raise RuntimeError("DART_API_KEY가 설정되지 않았습니다 (.env 확인)")
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bgn_de": date,
        "end_de": date,
        "page_count": 20,
    }
    resp = requests.get(LIST_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "000":
        return []
    disclosures = []
    for item in data.get("list", []):
        disclosures.append(
            {
                "title": item.get("report_nm"),
                "submitter": item.get("flr_nm"),
                "date": item.get("rcept_dt"),
                "url": DETAIL_URL_TMPL.format(rcept_no=item.get("rcept_no")),
            }
        )
    return disclosures
