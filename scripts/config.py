"""환경 설정 및 API 키 로딩."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT_DIR / ".cache"
NOTES_DIR = ROOT_DIR / "notes"

load_dotenv(ROOT_DIR / ".env")

DART_API_KEY = os.environ.get("DART_API_KEY", "")

CACHE_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)
