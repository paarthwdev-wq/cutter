"""
End-to-end integration test of video clipping, vertical 9:16 aspect ratio conversion,
and subtitle overlay using FFmpeg with synthetic generated test footage.
"""
import subprocess
from pathlib import Path
from telegram_clipper.video_processor.ffmpeg_processor import FfmpegProcessor
from telegram_clipper.captions.subtitle_generator import SubtitleGenerator
from telegram_clipper.config.settings import FFMPEG_PATH

def run_e2e_video_test():
    test_dir = Path("test_e2e_workspace")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    source_video = test_dir / "sample_input.mp4"
    output_clip = test_dir / "sample_vertical_output.mp4"

    print("1. Generating 10-second 16:9 test input video via FFmpeg...")
    # Generate test video with test patterns and synthetic audio tone
    generate_cmd = [
        FFMPEG_PATH,
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=10:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=10",
        "-c:v", "libx264",
        "-c:a", "aac",
        str(source_video)
    ]
    subprocess.run(generate_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert source_video.exists(), "Source test video was not created."

    print("2. Generating test subtitles...")
    sub_gen = SubtitleGenerator(test_dir)
    test_transcript = [
        {"start": 1.0, "end": 4.0, "text": "This is test subtitle line one."},
        {"start": 4.5, "end": 8.0, "text": "Vertical video framing test with hook banner."}
    ]
    srt_path = sub_gen.generate_clip_srt(
        clip_index=1,
        clip_start=0.0,
        clip_end=8.0,
        transcript_segments=test_transcript
    )
    assert srt_path.exists(), "SRT subtitle file was not created."

    print("3. Executing FfmpegProcessor: Vertical 9:16 conversion + blurred background + hook...")
    processor = FfmpegProcessor(FFMPEG_PATH)
    res_path = processor.create_vertical_clip(
        input_video=source_video,
        output_video=output_clip,
        start_sec=0.0,
        duration_sec=7.0,
        subtitle_srt=srt_path,
        hook_title="AI Clipper Test Hook"
    )

    assert res_path.exists(), "Output clip does not exist."
    file_size = res_path.stat().st_size
    print(f"[SUCCESS] Generated output clip successfully! Path: {res_path}, Size: {file_size / 1024:.1f} KB")

    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    print("[SUCCESS] End-to-end video processing test PASSED successfully!")

if __name__ == "__main__":
    run_e2e_video_test()
