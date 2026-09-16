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
