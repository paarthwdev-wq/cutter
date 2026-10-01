# Implementation Plan: Telegram AI Video Clipping Bot

**Branch**: `001-telegram-ai-video-clipper` | **Date**: 2026-10-02 | **Spec**: [spec.md](./spec.md)

## Summary

Build a self-hosted, modular Telegram bot in Python that accepts YouTube URLs, downloads videos with `yt-dlp`, transcribes/analyzes the content with Gemini 2.5/Flash (free tier) or local speech-density NLP, selects 3–5 viral segments (15–60s), formats them into 9:16 vertical videos with smart framing, generates and burns subtitles + hook titles with FFmpeg, and uploads them directly to Telegram.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `python-telegram-bot`, `yt-dlp`, `google-genai`, `imageio-ffmpeg`, `faster-whisper`, `python-dotenv`
- **FFmpeg Engine**: Bundled binary via `imageio-ffmpeg` / system ffmpeg fallback
- **AI / LLM**: Google Gemini API (Free Tier `gemini-2.5-flash` or `gemini-1.5-flash`) with local fallback heuristic
- **Target Platform**: Windows 11 / Self-hosted PC / laptop
- **Project Structure**: Modular architecture under `telegram_clipper/` with clear responsibility separation
- **Storage**: Local temporary working directory with automatic cleanup post-delivery

## Project Architecture & Directory Layout

```text
telegram_clipper/
├── __init__.py
├── main.py                  # Entrypoint to start the Telegram bot
├── config/                  # Configuration & Environment loading
│   ├── __init__.py
│   └── settings.py
├── telegram_bot/            # Telegram command handlers & progress dispatch
│   ├── __init__.py
│   ├── bot.py
│   └── handlers.py
├── downloader/              # yt-dlp wrapper & metadata extraction
│   ├── __init__.py
│   └── ytdlp_downloader.py
├── analyzer/                # Video transcript extraction & AI segment evaluator
│   ├── __init__.py
│   ├── transcriber.py
│   └── gemini_analyzer.py
├── clip_selector/           # Segment boundary validation & selection logic
│   ├── __init__.py
│   └── selector.py
├── video_processor/         # FFmpeg vertical 9:16 conversion & framing
│   ├── __init__.py
│   └── ffmpeg_processor.py
├── captions/                # Subtitle (SRT/ASS) generation & styling
│   ├── __init__.py
│   └── subtitle_generator.py
└── storage/                 # Workspace file lifecycle management & cleanup
    ├── __init__.py
    └── manager.py
```

## Step-by-Step Execution Plan

1. **Configuration & Storage**: Setup `.env` loader, configuration defaults (clip lengths, max size, Gemini model), and temp workspace manager.
2. **Downloader**: Build `ytdlp_downloader.py` to extract video metadata, transcripts, and download compressed video streams under Telegram limits.
3. **Analyzer & Selector**: Build transcript extraction (`youtube-transcript-api` / `faster-whisper`), Gemini prompt evaluator for hooks/moments, and local NLP sentence-boundary fallback.
4. **Video Processor & Subtitles**: Build 9:16 vertical conversion with FFmpeg (blurred top/bottom background or smart speaker crop), generate subtitle files (SRT / ASS), and burn subtitles + hook headers into output MP4s.
5. **Telegram Bot**: Assemble `python-telegram-bot` application with `/start`, `/help`, `/status`, `/clip`, and bare URL detection. Include stage-by-stage Telegram progress message editing.
6. **Tests & Verification**: Write unit and integration tests verifying each module independently and end-to-end with sample videos.
