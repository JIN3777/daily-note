"""바탕화면에 노트 바로가기 아이콘을 만듭니다.

이 스크립트는 클라우드/샌드박스가 아니라 노트를 확인할 **본인 PC**에서 실행해야
합니다. 기본값으로는 로컬 `notes/index.html`(더블클릭으로 열던 그 페이지)을
가리키는 아이콘을 만들고, `--url`로 GitHub Pages 주소를 넘기면 그 주소를 여는
아이콘을 만듭니다.

사용 예:
    python scripts/create_desktop_icon.py
    python scripts/create_desktop_icon.py --url https://<깃허브아이디>.github.io/daily-note/
"""
import argparse
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def default_target() -> str:
    index = REPO_ROOT / "notes" / "index.html"
    return index.resolve().as_uri()


def find_desktop_dir() -> Path:
    home = Path.home()
    for name in ("Desktop", "바탕화면"):
        candidate = home / name
        if candidate.is_dir():
            return candidate
    return home / "Desktop"


def create_windows_shortcut(desktop: Path, name: str, target: str) -> Path:
    path = desktop / f"{name}.url"
    path.write_text(f"[InternetShortcut]\nURL={target}\n", encoding="utf-8")
    return path


def create_macos_shortcut(desktop: Path, name: str, target: str) -> Path:
    path = desktop / f"{name}.webloc"
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict><key>URL</key>'
        f"<string>{target}</string></dict></plist>\n",
        encoding="utf-8",
    )
    return path


def create_linux_shortcut(desktop: Path, name: str, target: str) -> Path:
    path = desktop / f"{name}.desktop"
    path.write_text(
        "[Desktop Entry]\n"
        "Type=Link\n"
        f"Name={name}\n"
        f"URL={target}\n"
        "Icon=text-html\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def create_shortcut(desktop: Path, name: str, target: str, system: str) -> Path:
    if system == "Windows":
        return create_windows_shortcut(desktop, name, target)
    if system == "Darwin":
        return create_macos_shortcut(desktop, name, target)
    return create_linux_shortcut(desktop, name, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        help="아이콘이 열 주소. 생략하면 로컬 notes/index.html을 사용합니다.",
    )
    parser.add_argument(
        "--name", default="일일 시황 노트", help="바탕화면에 표시될 아이콘 이름"
    )
    args = parser.parse_args()

    target = args.url
    if not target:
        if not (REPO_ROOT / "notes" / "index.html").exists():
            print(
                "notes/index.html이 아직 없습니다. 먼저 "
                "`python scripts/run_daily.py --date YYYYMMDD`로 노트를 한 번 생성하거나, "
                "--url로 GitHub Pages 주소를 지정하세요.",
                file=sys.stderr,
            )
            sys.exit(1)
        target = default_target()

    desktop = find_desktop_dir()
    desktop.mkdir(parents=True, exist_ok=True)

    path = create_shortcut(desktop, args.name, target, platform.system())
    print(f"바탕화면 아이콘을 만들었습니다: {path}")
    print(f"-> {target}")


if __name__ == "__main__":
    main()
