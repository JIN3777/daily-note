import build_note


def _item(ticker="001520", name="동양"):
    return {
        "ticker": ticker,
        "name": name,
        "is_limit_up": True,
        "change_pct": 29.97,
        "volume": 5_020_000,
        "news": None,
        "disclosures": [],
        "chart": None,
    }


def test_section1_html_includes_memo_box_keyed_by_date_and_ticker():
    out = build_note.render_section1_html("2026-09-19", [_item()])

    assert 'class="memo-input"' in out
    assert 'data-key="2026-09-19:001520"' in out


def test_build_note_html_includes_memo_autosave_script():
    out = build_note.build_note_html("20260919", [_item()], [])

    assert "localStorage" in out
    assert 'data-key="2026-09-19:001520"' in out
