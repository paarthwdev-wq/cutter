"""
Configuration and Environment Settings for Telegram AI Video Clipper.
"""
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# API Keys and Tokens
DEFAULT_FALLBACK_TOKEN = "8895390613:AAHs0lPiJK23Y5InsGYudgf209osHV0-u0A"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or DEFAULT_FALLBACK_TOKEN
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Video clipping parameters
MIN_CLIP_DURATION = int(os.getenv("MIN_CLIP_DURATION", "15"))
MAX_CLIP_DURATION = int(os.getenv("MAX_CLIP_DURATION", "60"))
MAX_CLIPS_COUNT = int(os.getenv("MAX_CLIPS_COUNT", "4"))
TARGET_ASPECT_RATIO = os.getenv("TARGET_ASPECT_RATIO", "9:16")
OUTPUT_RESOLUTION = os.getenv("OUTPUT_RESOLUTION", "720x1280")

# Storage & Cleanup
TEMP_STORAGE_DIR = Path(os.getenv("TEMP_STORAGE_DIR", str(BASE_DIR / "storage_temp"))).resolve()
AUTO_CLEANUP = os.getenv("AUTO_CLEANUP", "1").strip() in ("1", "true", "True")

# Locate FFmpeg binary (prefer imageio-ffmpeg bundled binary, fallback to system PATH)
def get_ffmpeg_binary() -> str:
    # Check if system ffmpeg exists
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_binary()
