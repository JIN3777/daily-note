import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import create_desktop_icon as icon


def test_create_windows_shortcut_content(tmp_path):
    path = icon.create_windows_shortcut(tmp_path, "일일 시황 노트", "https://example.com/")
    assert path.name == "일일 시황 노트.url"
    assert path.read_text(encoding="utf-8") == "[InternetShortcut]\nURL=https://example.com/\n"


def test_create_macos_shortcut_content(tmp_path):
    path = icon.create_macos_shortcut(tmp_path, "일일 시황 노트", "https://example.com/")
    assert path.name == "일일 시황 노트.webloc"
    assert "<string>https://example.com/</string>" in path.read_text(encoding="utf-8")


def test_create_linux_shortcut_content(tmp_path):
    path = icon.create_linux_shortcut(tmp_path, "일일 시황 노트", "https://example.com/")
    assert path.name == "일일 시황 노트.desktop"
    content = path.read_text(encoding="utf-8")
    assert "Type=Link" in content
    assert "URL=https://example.com/" in content
    assert (path.stat().st_mode & 0o755) == 0o755


def test_find_desktop_dir_prefers_existing_korean_name(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(icon.Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / "바탕화면").mkdir()

    assert icon.find_desktop_dir() == tmp_path / "바탕화면"


def test_default_target_points_to_local_index():
    target = icon.default_target()
    assert target.startswith("file://")
    assert target.endswith("notes/index.html")
