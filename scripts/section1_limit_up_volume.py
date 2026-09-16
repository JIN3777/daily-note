"""섹션 1: 당일 상한가 / 거래량 1,000만주 이상 종목 + 관련 뉴스·공시 수집."""
import argparse
import json

import dart_client
import krx_data
import news_client
from limit_up_logic import find_limit_up_and_high_volume


def build_section1(date: str, with_news: bool = True, with_disclosures: bool = True) -> list[dict]:
    snapshot = krx_data.market_snapshot(date)
    matched = find_limit_up_and_high_volume(snapshot)

    corp_code_map = {}
    if with_disclosures:
        try:
            corp_code_map = dart_client.build_ticker_to_corp_code()
        except Exception as e:
            print(f"[경고] DART corp_code 매핑 실패, 공시 조회 생략: {e}")
            with_disclosures = False

    for item in matched:
        ticker = item["ticker"]
        item["name"] = krx_data.ticker_name(ticker)

        item["news"] = []
        if with_news:
            try:
                item["news"] = news_client.search_news(item["name"], date)
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

    return matched


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="상한가/거래량 급증 종목 스크리닝")
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--no-news", action="store_true")
    parser.add_argument("--no-disclosures", action="store_true")
    parser.add_argument("--out", help="결과를 저장할 JSON 경로")
    args = parser.parse_args()

    result = build_section1(
        args.date, with_news=not args.no_news, with_disclosures=not args.no_disclosures
    )
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"저장 완료: {args.out} ({len(result)}건)")
    else:
        print(output)
