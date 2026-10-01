"""
YouTube video downloader & metadata extractor using yt-dlp.
"""
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yt_dlp
from telegram_clipper.config.settings import FFMPEG_PATH

logger = logging.getLogger(__name__)

YOUTUBE_URL_REGEX = re.compile(
    r'^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|embed/|live/)|youtu\.be/)([\w\-]{11})'
)

def validate_youtube_url(url: str) -> bool:
    """Validate whether the provided string is a valid YouTube URL."""
    if not url:
        return False
    return bool(YOUTUBE_URL_REGEX.search(url.strip()))

def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL."""
    match = YOUTUBE_URL_REGEX.search(url.strip())
    if match:
        return match.group(5)
    return None

class YtDlpDownloader:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Fetch video metadata without downloading full video."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'ffmpeg_location': FFMPEG_PATH,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info

    def download_video(self, url: str, max_duration_sec: int = 1800) -> Dict[str, Any]:
        """
        Download video and audio streams into an MP4 file.
        Limits resolution to max 1080p to keep processing fast and free of bloat.
        """
        output_template = str(self.output_dir / "source_video.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
            'ffmpeg_location': FFMPEG_PATH,
            # Subtitle options: attempt to extract subtitles automatically if present
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en', 'auto'],
            'subtitlesformat': 'vtt/srt/best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            duration = info.get('duration', 0)
            if duration and duration > max_duration_sec:
                raise ValueError(
                    f"Video length ({duration // 60}m) exceeds the free processing limit of {max_duration_sec // 60} minutes."
                )
            
            # Find the actual downloaded mp4 file
            mp4_candidates = list(self.output_dir.glob("source_video*.mp4"))
            if not mp4_candidates:
                # check any video file
                all_candidates = [p for p in self.output_dir.iterdir() if p.suffix in ('.mp4', '.mkv', '.webm')]
                if not all_candidates:
                    raise FileNotFoundError("Video download failed to produce a valid media file.")
                video_file = all_candidates[0]
            else:
                video_file = mp4_candidates[0]
                
            return {
                'title': info.get('title', 'Unknown Title'),
                'duration': duration,
                'author': info.get('uploader', 'Unknown Author'),
                'video_file': video_file,
                'info': info
            }
