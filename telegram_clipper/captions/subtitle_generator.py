"""
Synchronized Subtitle & Hook Title Generator (SRT / ASS format).
"""
from pathlib import Path
from typing import List, Dict, Any

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp HH:MM:SS,mmm"""
    millis = int(round((seconds - int(seconds)) * 1000))
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

class SubtitleGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def generate_clip_srt(
        self,
        clip_index: int,
        clip_start: float,
        clip_end: float,
        transcript_segments: List[Dict[str, Any]]
    ) -> Path:
        """
        Extract subtitles belonging to [clip_start, clip_end] and create an SRT file
        with timestamps offset to start at 00:00:00.
        """
        srt_file = self.output_dir / f"subtitles_clip_{clip_index}.srt"
        lines = []
        entry_idx = 1

        for seg in transcript_segments:
            s_start = seg['start']
            s_end = seg['end']
            text = seg['text'].strip()

            # Check overlap with clip window
            if s_end > clip_start and s_start < clip_end:
                # Offset relative to clip start
                rel_start = max(0.0, s_start - clip_start)
                rel_end = min(clip_end - clip_start, s_end - clip_start)

                if rel_end > rel_start and text:
                    lines.append(str(entry_idx))
                    lines.append(f"{format_timestamp_srt(rel_start)} --> {format_timestamp_srt(rel_end)}")
                    lines.append(text)
                    lines.append("")
                    entry_idx += 1

        # Write SRT content (ensure UTF-8)
        content = "\n".join(lines) if lines else "1\n00:00:01,000 --> 00:00:04,000\n[Speech]\n"
        srt_file.write_text(content, encoding="utf-8")
        return srt_file
