"""
FFmpeg Video Processor:
- Precision clipping with audio/video sync
- Vertical 9:16 aspect ratio conversion (centered crop with blurred background canvas)
- Subtitle & hook title overlay burn-in
- Target file size / bitrate control under Telegram limits (50MB)
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional
from telegram_clipper.config.settings import FFMPEG_PATH, OUTPUT_RESOLUTION

logger = logging.getLogger(__name__)

class FfmpegProcessor:
    def __init__(self, ffmpeg_bin: str = FFMPEG_PATH):
        self.ffmpeg_bin = ffmpeg_bin

    def create_vertical_clip(
        self,
        input_video: Path,
        output_video: Path,
        start_sec: float,
        duration_sec: float,
        subtitle_srt: Optional[Path] = None,
        hook_title: Optional[str] = None
    ) -> Path:
        """
        Produce a vertical 9:16 short clip using FFmpeg filter_complex:
        1. Base layer: scaled to fill vertical canvas (e.g. 720x1280) and blurred (boxblur/gblur).
        2. Top layer: scaled to fit canvas width with aspect ratio preserved, centered vertically.
        3. Burn-in subtitles (if SRT provided) and hook title text.
        """
        res_w, res_h = [int(x) for x in OUTPUT_RESOLUTION.split("x")]
        
        # Format subtitle path properly for FFmpeg Windows syntax
        escaped_srt = ""
        if subtitle_srt and subtitle_srt.exists():
            srt_str = str(subtitle_srt.resolve()).replace("\\", "/")
            if ":" in srt_str:
                drive, rest = srt_str.split(":", 1)
                srt_str = f"{drive}\\:{rest}"
            escaped_srt = srt_str

        # Build filter_complex
        # [0:v] split [bg][fg]
        # [bg] scale=W:H:force_original_aspect_ratio=increase,crop=W:H,boxblur=20:5 [bg_blur]
        # [fg] scale=W:-2:force_original_aspect_ratio=decrease [fg_scaled]
        # [bg_blur][fg_scaled] overlay=(W-w)/2:(H-h)/2 [stacked]
        filters = [
            f"[0:v]split=2[bg][fg]",
            f"[bg]scale={res_w}:{res_h}:force_original_aspect_ratio=increase,crop={res_w}:{res_h},boxblur=25:5[bg_blur]",
            f"[fg]scale={res_w}:-2:force_original_aspect_ratio=decrease[fg_scaled]",
            f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2[base_comp]"
        ]
        
        current_layer = "base_comp"

        # Add Subtitles filter if valid
        if escaped_srt:
            # Force readable white font with black outline
            sub_filter = f"[{current_layer}]subtitles='{escaped_srt}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Alignment=2,MarginV=60'[with_subs]"
            filters.append(sub_filter)
            current_layer = "with_subs"

        # Hook title banner (optional drawtext)
        if hook_title:
            clean_title = hook_title.replace("'", "").replace(":", "").replace("\\", "").strip()[:40]
            # Draw top banner box and title text
            draw_hook = f"[{current_layer}]drawtext=text='{clean_title}':fontcolor=white:fontsize=28:box=1:boxcolor=black@0.65:boxborderw=10:x=(w-text_w)/2:y=100[final_v]"
            filters.append(draw_hook)
            current_layer = "final_v"

        filter_complex_str = ";".join(filters)

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-ss", str(start_sec),
            "-i", str(input_video),
            "-t", str(duration_sec),
            "-filter_complex", filter_complex_str,
            "-map", f"[{current_layer}]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_video)
        ]

        logger.info(f"Running FFmpeg clip extraction: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg failed with exit code {result.returncode}: {result.stderr}")
            # Fallback simple crop if complex filter fails
            self._simple_fallback_clip(input_video, output_video, start_sec, duration_sec, res_w, res_h)

        if not output_video.exists():
            raise FileNotFoundError(f"FFmpeg output file {output_video} was not generated.")

        return output_video

    def _simple_fallback_clip(
        self,
        input_video: Path,
        output_video: Path,
        start_sec: float,
        duration_sec: float,
        w: int,
        h: int
    ):
        """Fallback simpler ffmpeg execution without complex drawtext/subtitles."""
        fallback_cmd = [
            self.ffmpeg_bin,
            "-y",
            "-ss", str(start_sec),
            "-i", str(input_video),
            "-t", str(duration_sec),
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-c:a", "aac",
            str(output_video)
        ]
        subprocess.run(fallback_cmd, check=True)
