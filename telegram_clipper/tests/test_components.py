"""
Unit and Component Verification Tests for Telegram AI Video Clipper.
"""
import unittest
from pathlib import Path
from telegram_clipper.downloader.ytdlp_downloader import validate_youtube_url, extract_video_id
from telegram_clipper.clip_selector.selector import ClipSelector
from telegram_clipper.captions.subtitle_generator import SubtitleGenerator, format_timestamp_srt
from telegram_clipper.config.settings import FFMPEG_PATH

class TestClipperComponents(unittest.TestCase):

    def test_youtube_url_validation(self):
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://youtube.com/shorts/3f4Y2N4w8z8",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        invalid_urls = [
            "https://google.com",
            "not_a_url",
            "https://vimeo.com/123456"
        ]
        for url in valid_urls:
            self.assertTrue(validate_youtube_url(url), f"Failed for {url}")
            self.assertIsNotNone(extract_video_id(url), f"Failed to extract ID for {url}")

        for url in invalid_urls:
            self.assertFalse(validate_youtube_url(url), f"Should be invalid: {url}")

    def test_clip_selector_heuristics(self):
        selector = ClipSelector(min_duration=15, max_duration=60, max_clips=3)
        sample_transcript = [
            {"start": 0.0, "end": 5.0, "text": "Hello world welcome to this episode."},
            {"start": 5.0, "end": 15.0, "text": "Today we are discussing AI development."},
            {"start": 15.0, "end": 32.0, "text": "The key insight is completely changing the game."},
            {"start": 32.0, "end": 45.0, "text": "Let us summarize why this matters for creators."},
            {"start": 50.0, "end": 75.0, "text": "Another powerful discussion point occurs right here."}
        ]
        clips = selector.select_clips(gemini_clips=[], transcript_segments=sample_transcript, video_duration=80.0)
        self.assertGreater(len(clips), 0)
        for c in clips:
            self.assertGreaterEqual(c['duration'], 15.0)
            self.assertLessEqual(c['duration'], 65.0)
            self.assertIn('hook_title', c)

    def test_subtitle_generation(self):
        tmp_dir = Path("storage_temp_test")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        try:
            sub_gen = SubtitleGenerator(tmp_dir)
            sample_transcript = [
                {"start": 10.0, "end": 14.0, "text": "Hello and welcome!"},
                {"start": 14.5, "end": 20.0, "text": "This is a great moment."}
            ]
            srt_path = sub_gen.generate_clip_srt(
                clip_index=1,
                clip_start=10.0,
                clip_end=25.0,
                transcript_segments=sample_transcript
            )
            self.assertTrue(srt_path.exists())
            content = srt_path.read_text(encoding="utf-8")
            self.assertIn("Hello and welcome!", content)
            self.assertIn("00:00:00,000", content)
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_ffmpeg_detected(self):
        self.assertTrue(Path(FFMPEG_PATH).exists() or FFMPEG_PATH == "ffmpeg")

if __name__ == "__main__":
    unittest.main()
