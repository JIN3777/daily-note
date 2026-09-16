import news_client

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
<title>HLB 미국 자회사 엘레바 상업화 위한 전문가 영입 - 한국경제</title>
<link>https://news.google.com/rss/articles/abc123</link>
<pubDate>Wed, 18 May 2022 09:00:00 GMT</pubDate>
<source url="https://hankyung.com">한국경제</source>
</item>
<item>
<title>다른 날짜 기사 - 매일경제</title>
<link>https://news.google.com/rss/articles/xyz</link>
<pubDate>Thu, 19 May 2022 09:00:00 GMT</pubDate>
<source url="https://mk.co.kr">매일경제</source>
</item>
</channel>
</rss>""".encode("utf-8")


class _FakeResp:
    content = SAMPLE_RSS

    def raise_for_status(self):
        pass


def test_search_news_filters_by_date_and_strips_source_suffix(monkeypatch):
    monkeypatch.setattr(news_client.requests, "get", lambda *a, **k: _FakeResp())

    result = news_client.search_news("HLB글로벌", "20220518")

    assert len(result) == 1
    assert result[0]["title"] == "HLB 미국 자회사 엘레바 상업화 위한 전문가 영입"
    assert result[0]["summary"] == "한국경제"
    assert result[0]["url"] == "https://news.google.com/rss/articles/abc123"
    assert result[0]["pub_date"] == "2022-05-18"
