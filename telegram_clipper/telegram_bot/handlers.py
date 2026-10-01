"""
Telegram command handlers and pipeline dispatch.
"""
import os
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from telegram_clipper.config.settings import (
    MIN_CLIP_DURATION,
    MAX_CLIP_DURATION,
    MAX_CLIPS_COUNT,
    AUTO_CLEANUP,
    FFMPEG_PATH,
    GEMINI_API_KEY
)
from telegram_clipper.storage.manager import StorageManager
from telegram_clipper.downloader.ytdlp_downloader import (
    YtDlpDownloader,
    validate_youtube_url,
    extract_video_id
)
from telegram_clipper.analyzer.transcriber import VideoTranscriber
from telegram_clipper.analyzer.gemini_analyzer import GeminiAnalyzer
from telegram_clipper.clip_selector.selector import ClipSelector
from telegram_clipper.captions.subtitle_generator import SubtitleGenerator
from telegram_clipper.video_processor.ffmpeg_processor import FfmpegProcessor

logger = logging.getLogger(__name__)
storage_mgr = StorageManager()

COPYRIGHT_NOTICE = (
    "\n\n⚖️ *Notice*: This bot is an automated video editing tool. "
    "Transforming, cropping, or adding captions to videos does *not* alter, remove, or grant copyright ownership. "
    "Please only process and publish content you own or have explicit permission to use."
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_text = (
        "👋 *Welcome to the Free AI Video Clipper Bot!*\n\n"
        "Send me any public YouTube video link, and I will automatically:\n"
        "1. 🧠 Analyze the video to find the best viral standalone moments\n"
        "2. ✂️ Cut the top 3–5 short clips (15–60s)\n"
        "3. 📱 Convert them into vertical 9:16 format with centered speaker framing\n"
        "4. 📝 Generate and burn subtitles + hook headlines\n"
        "5. 📤 Deliver the ready-to-post short videos right here in Telegram!\n\n"
        "*Usage:*\n"
        "• Send: `/clip <YouTube URL>`\n"
        "• Or simply paste any YouTube URL directly\n"
        "• `/status` - Check server/engine health\n"
        "• `/help` - Help & guidelines"
        + COPYRIGHT_NOTICE
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "ℹ️ *How to use AI Video Clipper:*\n\n"
        "1. Paste a valid YouTube video link (e.g. podcasts, interviews, speeches, tutorials).\n"
        "2. The bot downloads the audio/video streams.\n"
        "3. Moments are identified using the Gemini Free Tier or local speech-density engine.\n"
        "4. Clips are rendered in vertical (9:16) format with burned captions.\n"
        "5. Clips are sent one-by-one with duration timestamps.\n\n"
        "*Commands:*\n"
        "/clip `<url>` - Clip a YouTube video\n"
        "/status - View system status & active settings\n"
        "/help - Display this manual"
        + COPYRIGHT_NOTICE
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    gemini_status = "✅ Configured (Free Tier)" if GEMINI_API_KEY else "⚠️ Not configured (Using Local Heuristic)"
    ffmpeg_ok = "✅ Available" if Path(FFMPEG_PATH).exists() or FFMPEG_PATH == "ffmpeg" else "❌ Missing"
    
    status_text = (
        "🤖 *System Status & Engine Diagnostics*\n\n"
        f"• *FFmpeg Engine*: {ffmpeg_ok} (`{Path(FFMPEG_PATH).name}`)\n"
        f"• *AI Analyzer*: {gemini_status}\n"
        f"• *Clip Duration*: {MIN_CLIP_DURATION}s – {MAX_CLIP_DURATION}s\n"
        f"• *Max Clips*: {MAX_CLIPS_COUNT}\n"
        f"• *Aspect Ratio*: 9:16 Vertical\n"
        f"• *Auto Cleanup*: {'Enabled' if AUTO_CLEANUP else 'Disabled'}\n"
        f"• *Server Platform*: Windows Self-Hosted"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")

async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages containing YouTube URLs directly or via /clip."""
    text = update.message.text.strip()
    if text.startswith("/clip"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("❌ Please specify a YouTube URL: `/clip <URL>`", parse_mode="Markdown")
            return
        url = parts[1].strip()
    else:
        url = text

    if not validate_youtube_url(url):
        await update.message.reply_text(
            "❌ *Invalid YouTube URL*\n\nPlease provide a valid YouTube video link (e.g. `https://youtube.com/watch?v=...` or `https://youtu.be/...`).",
            parse_mode="Markdown"
        )
        return

    # Acknowledge and create job
    status_msg = await update.message.reply_text("⬇️ Downloading video...")
    
    # Run the pipeline in background thread to keep bot responsive
    asyncio.create_task(
        _process_video_pipeline(update, status_msg, url)
    )

async def _process_video_pipeline(update: Update, status_msg, url: str):
    """Core video processing pipeline execution."""
    workspace = storage_mgr.create_job_workspace()
    try:
        # Step 1: Download video
        downloader = YtDlpDownloader(workspace)
        try:
            download_result = await asyncio.to_thread(downloader.download_video, url)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            await status_msg.edit_text(f"❌ *Download Failed*: {str(e)}", parse_mode="Markdown")
            return

        video_file = download_result['video_file']
        video_title = download_result['title']
        video_duration = download_result['duration']
        video_id = extract_video_id(url)

        # Step 2: Transcribe
        await status_msg.edit_text("🧠 Analyzing video...")
        transcriber = VideoTranscriber(workspace)
        transcript = await asyncio.to_thread(transcriber.get_transcript, video_id, video_file)

        # Step 3: Find best moments (Gemini AI + Selector)
        await status_msg.edit_text("⭐ Finding best moments...")
        gemini_clips = []
        if GEMINI_API_KEY:
            analyzer = GeminiAnalyzer(api_key=GEMINI_API_KEY)
            gemini_clips = await asyncio.to_thread(
                analyzer.analyze_transcript,
                transcript,
                video_title,
                MIN_CLIP_DURATION,
                MAX_CLIP_DURATION,
                MAX_CLIPS_COUNT
            )

        selector = ClipSelector(
            min_duration=MIN_CLIP_DURATION,
            max_duration=MAX_CLIP_DURATION,
            max_clips=MAX_CLIPS_COUNT
        )
        final_clips = selector.select_clips(gemini_clips, transcript, video_duration)

        if not final_clips:
            await status_msg.edit_text("❌ Could not identify suitable standalone moments in this video.")
            return

        # Step 4: Video Processing & Subtitle Generation
        await status_msg.edit_text(f"✂️ Creating {len(final_clips)} clips in 9:16 format...")
        subtitle_gen = SubtitleGenerator(workspace)
        processor = FfmpegProcessor()
        
        rendered_clips = []
        for idx, clip in enumerate(final_clips, 1):
            await status_msg.edit_text(f"✂️ Creating clip {idx}/{len(final_clips)}: *{clip.get('hook_title', '')}*...", parse_mode="Markdown")
            
            # Subtitle SRT
            srt_path = subtitle_gen.generate_clip_srt(
                clip_index=idx,
                clip_start=clip['start'],
                clip_end=clip['end'],
                transcript_segments=transcript
            )

            out_clip_path = workspace / f"clip_{idx}.mp4"
            await asyncio.to_thread(
                processor.create_vertical_clip,
                input_video=video_file,
                output_video=out_clip_path,
                start_sec=clip['start'],
                duration_sec=clip['duration'],
                subtitle_srt=srt_path,
                hook_title=clip.get('hook_title')
            )

            if out_clip_path.exists():
                rendered_clips.append({
                    'index': idx,
                    'file': out_clip_path,
                    'duration': clip['duration'],
                    'title': clip.get('hook_title', f"Clip {idx}")
                })

        # Step 5: Deliver clips to user
        await status_msg.edit_text("📤 Sending clips...")
        for c in rendered_clips:
            caption_text = (
                f"🎬 *Clip {c['index']} — {int(c['duration'])} seconds*\n"
                f"📌 *Hook*: {c['title']}"
            )
            # Check file size (Telegram bot free limit is 50MB)
            file_size_mb = c['file'].stat().st_size / (1024 * 1024)
            if file_size_mb > 49.5:
                await update.message.reply_text(f"⚠️ Clip {c['index']} is {file_size_mb:.1f}MB, which exceeds Telegram's 50MB bot upload limit.")
                continue

            with open(c['file'], "rb") as video_fh:
                await update.message.reply_video(
                    video=video_fh,
                    caption=caption_text,
                    supports_streaming=True,
                    parse_mode="Markdown"
                )

        await status_msg.edit_text(f"✅ *All {len(rendered_clips)} clips generated and delivered successfully!*", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in pipeline: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ *Processing Error*: {str(e)}", parse_mode="Markdown")
    finally:
        if AUTO_CLEANUP:
            storage_mgr.cleanup_workspace(workspace)
