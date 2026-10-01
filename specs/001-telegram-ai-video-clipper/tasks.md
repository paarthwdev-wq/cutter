# Tasks: Telegram AI Video Clipping Bot

**Branch**: `001-telegram-ai-video-clipper`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 1: Setup & Foundational Infrastructure

- [x] T001 Verify Python dependencies (`python-telegram-bot`, `yt-dlp`, `google-genai`, `imageio-ffmpeg`, `faster-whisper`)
- [x] T002 Create modular directory structure: `telegram_clipper/{config,telegram_bot,downloader,analyzer,clip_selector,video_processor,captions,storage}`
- [x] T003 Implement `config/settings.py` for `.env` parsing, default parameters, and token verification
- [x] T004 Implement `storage/manager.py` for per-job temp folders and automatic file cleanup
- [x] T005 Create `.env.example` template with `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, etc.

## Phase 2: Downloader & Audio/Transcript Pipeline

- [x] T006 Implement `downloader/ytdlp_downloader.py` for URL validation, metadata fetching, and optimized video download
- [x] T007 Implement `analyzer/transcriber.py` with multi-source fallback: (1) YouTube auto-captions via yt-dlp / youtube-transcript-api, (2) local faster-whisper audio transcription

## Phase 3: AI Analysis & Clip Selection

- [x] T008 Implement `analyzer/gemini_analyzer.py` using Google Gemini free tier (`gemini-2.5-flash` / `gemini-1.5-flash`) for evaluating hook score, story completeness, and standalone value
- [x] T009 Implement `clip_selector/selector.py` with rule-based fallback when Gemini API is unavailable (sentence boundary alignment, duration clamping 15–60s)

## Phase 4: Video Processing & Subtitle Generation

- [x] T010 Implement `captions/subtitle_generator.py` to produce synchronized SRT subtitle files and hook headers for selected intervals
- [x] T011 Implement `video_processor/ffmpeg_processor.py` for 9:16 vertical conversion (centered crop + blurred background stack), subtitle burn-in, and H.264/AAC encoding under Telegram limits

## Phase 5: Telegram Bot Interface & Orchestration

- [x] T012 Implement `telegram_bot/handlers.py` with `/start`, `/help`, `/status`, `/clip`, and direct YouTube URL handling
- [x] T013 Implement live progress message dispatcher (`⬇️ Downloading`, `🧠 Analyzing`, `⭐ Finding moments`, `✂️ Creating clips`, `📝 Generating captions`, `📤 Sending clips`)
- [x] T014 Implement clip sender with Telegram size checks and error handling
- [x] T015 Implement `telegram_clipper/main.py` entrypoint and bot execution loop

## Phase 6: Verification & Testing

- [x] T016 Write automated component tests verifying downloader, transcriber, selector, and ffmpeg processor (`test_components.py`: 4/4 passing)
- [x] T017 Execute end-to-end integration test with synthetic test video (`test_e2e_video.py`: PASSED)
- [x] T018 Document exact installation commands, startup command, folder structure, and future extensibility guide
