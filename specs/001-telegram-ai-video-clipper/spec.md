# Feature Specification: Telegram AI Video Clipping Bot

**Feature Branch**: `001-telegram-ai-video-clipper`
**Created**: 2026-10-02
**Status**: Ready for Implementation
**Input**: Build a completely free, self-hosted Telegram AI video clipping bot using the existing Spec Kit setup on this laptop.

## Summary

A self-hosted, 100% free Telegram bot that allows users to send a YouTube link (either directly or via `/clip <YouTube URL>`) and automatically produces 3–5 high-engagement vertical short clips (9:16 aspect ratio, 15–60s duration) with burned-in subtitles, hook headlines, and centered speaker framing, returning each video directly in the Telegram chat.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit YouTube Video & Receive Viral Short Clips (Priority: P1) 🎯 MVP

As a Telegram user and video creator, I want to send a YouTube video link to the bot so that I automatically receive 3 to 5 vertical (9:16) MP4 video clips with burned-in captions and smart hooks without leaving Telegram.

**Why this priority**:
This is the core end-to-end pipeline and primary value proposition of the system.

**Independent Test**:
Send a YouTube URL or `/clip https://www.youtube.com/watch?v=...` to the bot. The bot validates the URL, downloads video & audio, transcribes/analyzes the segments, clips 3–5 parts (15-60s), crops to 9:16, burns subtitles, and uploads the clips to Telegram with duration labels.

**Acceptance Scenarios**:
1. **Given** a valid public YouTube URL sent with `/clip <url>` or just `<url>`, **When** the bot receives the message, **Then** it replies with progress updates (`⬇️ Downloading video...`, `🧠 Analyzing video...`, `⭐ Finding best moments...`, `✂️ Creating clips...`, `📝 Generating captions...`, `📤 Sending clips...`) and delivers 3–5 MP4 video files directly in the chat.
2. **Given** the downloaded clip, **When** rendered, **Then** the output is vertical 9:16 (1080x1920 or 720x1280), H.264 video + AAC audio, with burned-in readable subtitles and hook title banner.

---

### User Story 2 - Intelligent Free AI & Local Fallback Clip Selection (Priority: P2)

As a system runner who wants zero API bills, I want the bot to use the Gemini Free Tier or local transcript-based NLP heuristic fallbacks to select meaningful standalone segments (hook, narrative completeness, emotion) without crashing or requiring paid APIs.

**Why this priority**:
Zero-cost operation is mandatory. Video clipping must be resilient even if the user has no Gemini API key set or hits quota limits.

**Independent Test**:
Run clipping with `GEMINI_API_KEY` present: AI selects viral moments with hooks. Run clipping with `GEMINI_API_KEY` absent/empty: local transcript NLP analyzer extracts highest-density speech segments with complete sentences.

**Acceptance Scenarios**:
1. **Given** a video transcript and metadata, **When** Gemini Free API is available, **Then** Gemini evaluates hook strength, dialogue completeness, and interest scores, outputting 3–5 `[start, end, hook_title]` timestamps.
2. **Given** Gemini API is absent or unavailable, **When** analysis runs, **Then** local transcript analyzer calculates speech density and sentence boundaries, generating valid 15–60s candidate windows without failing.

---

### User Story 3 - Telegram Commands & Operational Feedback (Priority: P3)

As a Telegram user, I want clear interactive commands (`/start`, `/help`, `/status`) and comprehensive error notifications if a URL is invalid, private, or exceeds Telegram upload limits.

**Why this priority**:
Ensures smooth UX and prevents the bot from crashing or leaving the user hanging silently when errors occur.

**Independent Test**:
Send `/start`, `/help`, `/status` and test error scenarios (invalid URL, unreachably long video, telegram file size checks).

**Acceptance Scenarios**:
1. **Given** `/start` or `/help`, **When** executed, **Then** bot explains usage instructions, supported commands, and explicit copyright disclaimer.
2. **Given** an invalid or restricted YouTube video (private, deleted, age-restricted without auth), **When** submitted, **Then** bot sends a descriptive error message explaining why download failed.
3. **Given** `/status`, **When** executed, **Then** bot displays system status (disk space, ffmpeg availability, active jobs).

---

## Edge Cases

- **No Subtitles / Captions Available on YouTube**: Local `faster-whisper` (or speech recognition/transcript API) transcribes audio locally at zero cost.
- **Videos Exceeding Telegram Free Upload Limit (50MB)**: FFmpeg dynamic two-pass / CRF bitrate clamp keeps clips under 45MB so Telegram Bot API accepts them without error.
- **Vertical / Already 9:16 Video**: Intelligent crop detection leaves already-vertical videos intact and centers horizontal (16:9) footage with blurred background or speaker crop.
- **Rapid Concurrent Requests**: Job queue/lock prevents memory exhaustion or CPU thrashing on self-hosted laptops.
- **Copyright Disclaimer**: Bot strictly states it is an editing utility and does not alter or grant copyright ownership.

---

## Functional Requirements

- **FR-001**: Validate YouTube URLs (youtube.com, youtu.be, shorts).
- **FR-002**: Download video & audio streams using `yt-dlp` python engine.
- **FR-003**: Transcribe speech via YouTube subtitles or local Whisper fallback.
- **FR-004**: Evaluate moments with Gemini API (free tier) or local speech-density NLP heuristic.
- **FR-005**: Select 3–5 segments of 15–60 seconds, ensuring sentences are not cut off.
- **FR-006**: Execute FFmpeg processing to produce 9:16 vertical MP4 (H.264 / AAC) with face/subject centered and blurred background bars or smart center crop.
- **FR-007**: Burn synchronized styled subtitles and hook headlines into each clip.
- **FR-008**: Send completed clips directly to Telegram user chat with duration metadata.
- **FR-009**: Implement `/start`, `/help`, `/status`, and `/clip` commands.
- **FR-010**: Store temporary media in a managed `storage/` cache with auto-cleanup of completed jobs.
- **FR-011**: Zero hard-coded credentials; load all secrets from `.env`.

---

## Success Criteria

- **SC-001**: Successfully processes standard public YouTube videos into 3–5 vertical short clips without manual intervention.
- **SC-002**: 100% free of paid APIs, paid SaaS, and subscription fees.
- **SC-003**: Self-contained on the local machine with bundled/local FFmpeg and Python libraries.
- **SC-004**: Zero crashes on invalid input or network interruptions; graceful user notifications.
