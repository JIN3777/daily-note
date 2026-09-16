"""섹션 1: 당일 상한가 / 거래량 1,000만주 이상 종목 + 관련 뉴스·공시 수집."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

import chart_client
import dart_client
import krx_data
import news_client
from limit_up_logic import find_limit_up_and_high_volume

# 종목마다 뉴스 검색 + 기사 본문 fetch + 공시 조회 + 차트용 시세 조회를 하다 보니
# 종목 수가 많으면 순차 처리로는 오래 걸린다. I/O 대기가 대부분이라 스레드풀로 병렬 처리한다.
MAX_WORKERS = 8


def _enrich(item: dict, date: str, with_news: bool, with_disclosures: bool, with_chart: bool, corp_code_map: dict):
    ticker = item["ticker"]
    item["name"] = krx_data.ticker_name(ticker)

    item["news"] = None
    if with_news:
        try:
            item["news"] = news_client.get_top_news(item["name"], date)
        except Exception as e:
            print(f"[경고] {item['name']} 뉴스 조회 실패: {e}")

    item["disclosures"] = []
    if with_disclosures:
        corp_code = corp_code_map.get(ticker)
        if corp_code:
            try:
                item["disclosures"] = dart_client.get_disclosures(corp_code, date)
            except Exception as e:
                print(f"[경고] {item['name']} 공시 조회 실패: {e}")

    item["_ohlcv"] = None
    if with_chart:
        try:
            item["_ohlcv"] = chart_client.fetch_ohlcv(ticker, date)
        except Exception as e:
            print(f"[경고] {item['name']} 차트용 시세 조회 실패: {e}")


def build_section1(
    date: str, with_news: bool = True, with_disclosures: bool = True, with_chart: bool = True
) -> list[dict]:
    snapshot = krx_data.market_snapshot(date)
    matched = find_limit_up_and_high_volume(snapshot)

    corp_code_map = {}
    if with_disclosures:
        try:
            corp_code_map = dart_client.build_ticker_to_corp_code()
        except Exception as e:
            print(f"[경고] DART corp_code 매핑 실패, 공시 조회 생략: {e}")
            with_disclosures = False

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(
            executor.map(
                lambda item: _enrich(item, date, with_news, with_disclosures, with_chart, corp_code_map),
                matched,
            )
        )

    # matplotlib 렌더링은 스레드 안전하지 않으므로, 데이터 조회(병렬)와 분리해 순차로 그린다.
    for item in matched:
        ohlcv = item.pop("_ohlcv", None)
        item["chart"] = (
            chart_client.render_chart(ohlcv, item["ticker"], item["name"], date)
            if ohlcv is not None and not ohlcv.empty
            else None
        )

    return matched


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="상한가/거래량 급증 종목 스크리닝")
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--no-news", action="store_true")
    parser.add_argument("--no-disclosures", action="store_true")
    parser.add_argument("--no-chart", action="store_true")
    parser.add_argument("--out", help="결과를 저장할 JSON 경로")
    args = parser.parse_args()

    result = build_section1(
        args.date,
        with_news=not args.no_news,
        with_disclosures=not args.no_disclosures,
        with_chart=not args.no_chart,
    )
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"저장 완료: {args.out} ({len(result)}건)")
    else:
        print(output)
