import build_index


def test_update_index_adds_and_updates_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(build_index, "NOTES_DIR", tmp_path)
    monkeypatch.setattr(build_index, "INDEX_JSON", tmp_path / "index.json")

    build_index.update_index("2026-09-10", section1_count=3, section2_count=0)
    build_index.update_index("2026-09-15", section1_count=24, section2_count=0)

    entries = build_index._load_entries()
    assert [e["date"] for e in entries] == ["2026-09-15", "2026-09-10"]  # 최신순

    # 같은 날짜 재실행 시 갱신되어야 함 (중복 추가 아님)
    build_index.update_index("2026-09-15", section1_count=25, section2_count=1)
    entries = build_index._load_entries()
    assert len(entries) == 2
    updated = next(e for e in entries if e["date"] == "2026-09-15")
    assert updated["section1_count"] == 25
    assert updated["section2_count"] == 1

    assert (tmp_path / "index.html").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "2026-09-15.html" in html
    assert "2026-09-10.html" in html
