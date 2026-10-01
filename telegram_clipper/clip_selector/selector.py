"""
Clip selection engine: combines Gemini suggestions with speech-density and sentence-boundary heuristics.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ClipSelector:
    def __init__(self, min_duration: int = 15, max_duration: int = 60, max_clips: int = 4):
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.max_clips = max_clips

    def select_clips(
        self,
        gemini_clips: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, Any]],
        video_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Produce finalized list of non-overlapping clip intervals.
        Falls back to transcript speech-density heuristics if gemini_clips is empty.
        """
        # If Gemini returned valid clips, align boundaries to sentence ends
        if gemini_clips:
            refined = []
            for c in gemini_clips:
                c_start = max(0.0, c['start'])
                c_end = min(video_duration, c['end']) if video_duration else c['end']
                
                # Check sentence boundary snapping from transcript
                snapped_start, snapped_end = self._snap_to_boundaries(c_start, c_end, transcript_segments)
                duration = snapped_end - snapped_start
                if self.min_duration <= duration <= self.max_duration + 5:
                    refined.append({
                        'start': snapped_start,
                        'end': snapped_end,
                        'duration': round(duration, 1),
                        'hook_title': c.get('hook_title', 'Insightful Moment'),
                        'reason': c.get('reason', 'AI selected')
                    })
            if refined:
                return refined[:self.max_clips]

        # Fallback: Local rule-based heuristic selector based on speech density
        return self._heuristic_selection(transcript_segments, video_duration)

    def _snap_to_boundaries(self, start: float, end: float, transcript: List[Dict[str, Any]]) -> tuple[float, float]:
        """Align start and end timestamps so words and sentences are not truncated."""
        if not transcript:
            return start, end

        best_start = start
        best_end = end

        # Find closest segment start within 3 seconds
        for seg in transcript:
            if abs(seg['start'] - start) < 3.5:
                best_start = seg['start']
                break

        # Find closest segment end within 4 seconds
        for seg in reversed(transcript):
            if abs(seg['end'] - end) < 4.0:
                best_end = seg['end']
                break

        if best_end <= best_start:
            return start, end

        return best_start, best_end

    def _heuristic_selection(self, transcript: List[Dict[str, Any]], total_duration: float) -> List[Dict[str, Any]]:
        """
        Local fallback when Gemini is unavailable:
        Groups transcript sentences into high-density blocks between 20s and 45s.
        """
        if not transcript:
            # Blind chunking if no transcript exists at all
            clips = []
            cur_time = 10.0
            step = 30.0
            idx = 1
            while cur_time + step < total_duration and len(clips) < self.max_clips:
                clips.append({
                    'start': cur_time,
                    'end': cur_time + step,
                    'duration': step,
                    'hook_title': f"Clip #{idx}",
                    'reason': "Evenly spaced sample"
                })
                cur_time += max(step, (total_duration - 20) / (self.max_clips + 1))
                idx += 1
            return clips

        # Form sentence blocks
        blocks = []
        i = 0
        while i < len(transcript):
            block_start = transcript[i]['start']
            j = i
            block_text = []
            while j < len(transcript):
                seg = transcript[j]
                block_text.append(seg['text'])
                duration = seg['end'] - block_start
                if duration >= 25.0:
                    if duration <= self.max_duration:
                        # Found a good block
                        full_text = " ".join(block_text)
                        # Extract first 4 words as title
                        first_words = " ".join(full_text.split()[:5])
                        blocks.append({
                            'start': block_start,
                            'end': seg['end'],
                            'duration': round(seg['end'] - block_start, 1),
                            'hook_title': first_words if first_words else f"Moment {len(blocks)+1}",
                            'reason': "High conversational density"
                        })
                    break
                j += 1
            i = max(i + 1, j + 1)
            if len(blocks) >= self.max_clips:
                break

        return blocks[:self.max_clips]
