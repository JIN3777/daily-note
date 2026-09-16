import news_client

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
<title>루머성 기사 - 이름없는블로그</title>
<link>https://news.google.com/rss/articles/low-trust</link>
<pubDate>Wed, 18 May 2022 10:00:00 GMT</pubDate>
<source url="https://blog.example.com">이름없는블로그</source>
</item>
<item>
<title>HLB 미국 자회사 엘레바 상업화 위한 전문가 영입 - 한국경제</title>
<link>https://news.google.com/rss/articles/trusted</link>
<pubDate>Wed, 18 May 2022 09:00:00 GMT</pubDate>
<source url="https://hankyung.com">한국경제</source>
</item>
<item>
<title>다른 날짜 기사 - 매일경제</title>
<link>https://news.google.com/rss/articles/wrong-date</link>
<pubDate>Thu, 19 May 2022 09:00:00 GMT</pubDate>
<source url="https://mk.co.kr">매일경제</source>
</item>
</channel>
</rss>""".encode("utf-8")

ARTICLE_HTML = """<html><body><article>
<p>HLB 미국 자회사 엘레바가 리브보서파 상업화를 위해 전문가를 영입했다고 밝혔다.</p>
<p>업계에서는 이번 영입이 글로벌 진출에 속도를 낼 것으로 보고 있다.</p>
</article></body></html>"""


class _FakeResp:
    def __init__(self, content=b"", text=""):
        self.content = content
        self.text = text

    def raise_for_status(self):
        pass


def _fake_get(url, *args, **kwargs):
    if url == news_client.RSS_URL:
        return _FakeResp(content=SAMPLE_RSS)
    return _FakeResp(text=ARTICLE_HTML)


def test_get_top_news_prefers_trusted_source_and_includes_body(monkeypatch):
    monkeypatch.setattr(news_client.requests, "get", _fake_get)

    result = news_client.get_top_news("HLB글로벌", "20220518")

    assert result is not None
    assert result["title"] == "HLB 미국 자회사 엘레바 상업화 위한 전문가 영입"
    assert result["source"] == "한국경제"
    assert result["pub_date"] == "2022-05-18"
    assert "엘레바가 리브보서파" in result["body"]


def test_get_top_news_returns_none_when_no_same_day_article(monkeypatch):
    monkeypatch.setattr(news_client.requests, "get", _fake_get)

    result = news_client.get_top_news("HLB글로벌", "20220520")

    assert result is None


GENERIC_WRAP_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
<title>[마감 시황] 코스피, 상승 마감...기관 순매수로 지수 견인 - 필드뉴스</title>
<link>https://news.google.com/rss/articles/generic-wrap</link>
<pubDate>Wed, 16 Sep 2026 06:00:00 GMT</pubDate>
<source url="https://fieldnews.example.com">필드뉴스</source>
</item>
<item>
<title>큐라티스, 임상 3상 결과 발표에 상한가 - 이데일리</title>
<link>https://news.google.com/rss/articles/on-topic</link>
<pubDate>Wed, 16 Sep 2026 07:00:00 GMT</pubDate>
<source url="https://edaily.co.kr">이데일리</source>
</item>
</channel>
</rss>""".encode("utf-8")


def _fake_get_generic_wrap(url, *args, **kwargs):
    if url == news_client.RSS_URL:
        return _FakeResp(content=GENERIC_WRAP_RSS)
    return _FakeResp(text=ARTICLE_HTML)


def test_get_top_news_prefers_title_match_over_earlier_generic_article(monkeypatch):
    """일반 시황 기사가 더 일찍 나왔어도, 종목명이 제목에 들어간 기사를 우선해야 한다."""
    monkeypatch.setattr(news_client.requests, "get", _fake_get_generic_wrap)

    result = news_client.get_top_news("큐라티스", "20260916")

    assert result["title"] == "큐라티스, 임상 3상 결과 발표에 상한가"
    assert result["source"] == "이데일리"


def test_extract_data_p_payload_returns_none_without_attribute():
    assert news_client._extract_data_p_payload("<html><body>no signature here</body></html>") is None


def test_fetch_article_body_returns_empty_string_when_thin_and_no_signature(monkeypatch):
    """본문도 못 뽑고 우회용 서명(data-p)도 없는 극단적인 경우, 예외 없이 빈 문자열을 반환해야 한다."""

    def _fake_get_thin(url, *args, **kwargs):
        return _FakeResp(text="<html><body><script>location.replace('x')</script></body></html>")

    monkeypatch.setattr(news_client.requests, "get", _fake_get_thin)

    body = news_client.fetch_article_body("https://news.google.com/rss/articles/deadbeef")

    assert body == ""
