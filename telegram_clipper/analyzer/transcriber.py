"""
Transcription module supporting YouTube Captions API and local faster-whisper fallback.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess

logger = logging.getLogger(__name__)

class VideoTranscriber:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def get_transcript(self, video_id: Optional[str], audio_path: Path) -> List[Dict[str, Any]]:
        """
        Extract transcript:
        1. Attempt online transcript via youtube-transcript-api (instant, 0 CPU).
        2. If unavailable, extract audio & transcribe locally using faster-whisper (100% free, offline).
        """
        # Step 1: Online YouTube transcript
        if video_id:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                ytt_api = YouTubeTranscriptApi()
                # Try fetching english or any generated transcript
                transcript = ytt_api.get_transcript(video_id, languages=['en', 'en-US', 'en-GB', 'hi', 'es'])
                logger.info(f"Retrieved {len(transcript)} transcript segments via YouTubeTranscriptApi.")
                formatted = []
                for entry in transcript:
                    start = float(entry['start'])
                    duration = float(entry['duration'])
                    formatted.append({
                        'start': start,
                        'end': start + duration,
                        'text': entry['text'].strip()
                    })
                if formatted:
                    return formatted
            except Exception as e:
                logger.warning(f"YouTubeTranscriptApi failed/disabled: {e}. Falling back to local audio transcription.")

        # Step 2: Local Whisper fallback
        return self._transcribe_local_audio(audio_path)

    def _transcribe_local_audio(self, video_or_audio_path: Path) -> List[Dict[str, Any]]:
        """Transcribe audio using faster-whisper (tiny or base model for fast free inference)."""
        logger.info("Starting local speech recognition with faster-whisper...")
        try:
            from faster_whisper import WhisperModel
            # Using 'tiny' or 'base' for fast zero-cost CPU/GPU execution
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, info = model.transcribe(str(video_or_audio_path), beam_size=1)
            
            results = []
            for seg in segments:
                results.append({
                    'start': float(seg.start),
                    'end': float(seg.end),
                    'text': seg.text.strip()
                })
            logger.info(f"Local Whisper completed with {len(results)} segments.")
            return results
        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            return []
