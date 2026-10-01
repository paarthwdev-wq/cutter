"""
AI Moment Analyzer using Google Gemini Free Tier API with JSON response schema.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from telegram_clipper.config.settings import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

GEMINI_ANALYSIS_PROMPT = """
You are an expert viral short-form video editor for YouTube Shorts, TikTok, and Instagram Reels.
Analyze the following timestamped video transcript and identify the top {max_clips} best standalone clips.

Evaluation criteria:
1. HOOK STRENGTH: Starts with an engaging hook, intriguing question, punchy statement, or high emotion.
2. STANDALONE COMPLETENESS: The clip makes complete sense on its own without needing external context.
3. STORY COMPLETENESS: Do not cut off in the middle of a sentence or thought.
4. DURATION: Each clip must be strictly between {min_duration} and {max_duration} seconds.
5. NO DEAD AIR: Avoid silence, filler, or intro/outro roll.

TRANSCRIPT:
{transcript_text}

OUTPUT REQUIREMENT:
Return ONLY valid JSON matching this exact structure:
[
  {{
    "start": 12.5,
    "end": 45.0,
    "hook_title": "Short Punchy Title (Max 6 words)",
    "reason": "Why this moment was selected"
  }}
]
"""

class GeminiAnalyzer:
    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini Client: {e}")

    def is_available(self) -> bool:
        return bool(self.api_key and self.client)

    def analyze_transcript(
        self,
        transcript_segments: List[Dict[str, Any]],
        video_title: str,
        min_duration: int = 15,
        max_duration: int = 60,
        max_clips: int = 4
    ) -> List[Dict[str, Any]]:
        """Send transcript to Gemini to pick viral moments."""
        if not self.is_available():
            logger.info("Gemini API key is not configured; will rely on heuristic selector.")
            return []

        # Prepare formatted transcript text with timestamps
        formatted_lines = []
        for s in transcript_segments:
            start_str = f"{int(s['start'] // 60):02d}:{int(s['start'] % 60):02d}"
            formatted_lines.append(f"[{start_str}] {s['text']}")
        transcript_text = "\n".join(formatted_lines[:800]) # Cap to avoid exceeding token limit

        prompt = GEMINI_ANALYSIS_PROMPT.format(
            max_clips=max_clips,
            min_duration=min_duration,
            max_duration=max_duration,
            transcript_text=transcript_text
        )

        try:
            from google.genai import types
            logger.info(f"Querying Gemini ({self.model_name}) for viral clip moments...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Video Title: {video_title}\n\n{prompt}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            raw_text = response.text
            if not raw_text:
                return []
            
            # Parse json response
            data = json.loads(raw_text)
            if isinstance(data, list):
                valid_clips = []
                for item in data:
                    start = float(item.get('start', 0))
                    end = float(item.get('end', 0))
                    duration = end - start
                    if min_duration <= duration <= (max_duration + 5):
                        valid_clips.append({
                            'start': start,
                            'end': end,
                            'duration': duration,
                            'hook_title': item.get('hook_title', 'Key Moment').strip(),
                            'reason': item.get('reason', '')
                        })
                logger.info(f"Gemini selected {len(valid_clips)} viral moments.")
                return valid_clips[:max_clips]
        except Exception as e:
            logger.error(f"Gemini API analysis failed: {e}")

        return []
