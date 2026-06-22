---
name: media-understanding
description: Analyze and understand local video and audio files using Gemini's multimodal capabilities. Supports video summarization, scene description with timestamps, audio transcription, likely speaker labels, emotion/tone estimation, music and ambient-sound interpretation, Q&A, and structured-data extraction. Use this skill whenever the user mentions video analysis, "what's in this video," "summarize this video," extracting information from a video, video transcription, audio analysis, audio transcription, recording content, podcast content, audio summarization, recording analysis, or "analyze this clip." Trigger eagerly when a video or audio file path is provided.
---

# Media Understanding

Use Gemini's multimodal capabilities to analyze local video and audio files. Video covers both the picture and the audio track; audio covers speech, music, and ambient sound.

## Directory layout

```
media-understanding/
├── SKILL.md                        # This file
└── scripts/
    ├── analyze_video.py            # Local video file → analysis
    └── analyze_audio.py            # Local audio file → analysis
```

## What this skill can do

### Video
- **Summarization** — Concise summaries of the content.
- **Scene description** — Detailed walkthroughs combining picture and audio (with timestamps).
- **Transcription** — Transcribe the spoken audio in the video.
- **Q&A** — Answer questions about the video content.
- **Structured extraction** — Pull information out as JSON.
- **Spot analysis** — Inspect specific timestamps.
- **Clipping** — Analyze only a specified time range.

### Audio
- **Transcription** — Transcribe standalone audio (multilingual).
- **Summarization** — Summarize recordings, podcasts, meeting captures.
- **Speaker / emotion estimation** — Label likely speakers when distinguishable and estimate tone or emotional shifts.
- **Music and ambient interpretation** — Analyze non-speech audio (music, sound effects, environment).
- **Q&A** — Answer questions about the audio content.
- **Structured extraction** — Pull information out as JSON.
- **Region analysis** — Inspect a specific time range via `MM:SS` references in the prompt.

---

## Prerequisites

- **Python 3.10+** must be installed.
- `GEMINI_API_KEY` is assumed to already be available from the OS environment or a nearby `.env` file.
- Do not print, inspect, edit, or commit secret values.

### How to run the scripts

The scripts are written as [PEP 723](https://peps.python.org/pep-0723/) inline scripts — their dependencies (`google-genai`, `python-dotenv`) are declared at the top of each file. Any of the following invocation styles works:

```bash
# Option A: uv (recommended — fastest, auto-resolves dependencies)
uv run <skill-dir>/scripts/analyze_video.py "prompt" video.mp4

# Option B: pipx (when uv isn't available)
pipx run <skill-dir>/scripts/analyze_video.py "prompt" video.mp4

# Option C: pip + plain python (most universal — install dependencies once)
pip install google-genai python-dotenv
python3 <skill-dir>/scripts/analyze_video.py "prompt" video.mp4
```

The command examples below use the shortest form, `uv run`, but Options B and C run the same scripts identically.

---

## Workflow

### Picking the right script

| Input file | Script |
|---|---|
| Video file (`.mp4`, `.mov`, `.webm`, etc.) | `analyze_video.py` |
| Audio file (`.mp3`, `.wav`, `.flac`, etc.) | `analyze_audio.py` |

### Before analyzing

Confirm the following with the user. If anything is missing, ask:

1. **What do they want?** — Summary, transcript, scene description, structured extraction, etc.
2. **Output format** — Plain text, or structured JSON?
3. **Scope** — The whole file, or a specific time range?

> In the command examples below, replace `<skill-dir>` with the actual path where this skill is installed. Scripts live under `<skill-dir>/scripts/`.

---

## Video analysis (`analyze_video.py`)

```bash
uv run <skill-dir>/scripts/analyze_video.py "prompt" video_file_path [options...]
```

Examples:

```bash
# Quick summary
uv run <skill-dir>/scripts/analyze_video.py \
  "Summarize this video in 3 sentences." \
  presentation.mp4

# Detailed timestamped breakdown
uv run <skill-dir>/scripts/analyze_video.py \
  "Describe the key events in this video with timestamps. Include both audio and visual details." \
  meeting_recording.mp4

# Transcribe the spoken audio in a video
uv run <skill-dir>/scripts/analyze_video.py \
  "Transcribe the audio. If there are multiple speakers, label likely speakers when distinguishable." \
  interview.mp4

# Structured JSON extraction
uv run <skill-dir>/scripts/analyze_video.py \
  "List every product that appears in this video. Include name, color, and notable features for each." \
  product_review.mp4 --json

# Analyze only a specific range (30s–90s)
uv run <skill-dir>/scripts/analyze_video.py \
  "Describe what's happening in this segment in detail." \
  long_video.mp4 --start 30 --end 90

# Lower resolution for fast / cheap analysis of large videos
uv run <skill-dir>/scripts/analyze_video.py \
  "Give me an overview of this video." \
  large_video.mp4 --media-resolution low

# Higher fps for fast-moving content
uv run <skill-dir>/scripts/analyze_video.py \
  "Identify all the text and numbers visible on screen." \
  sports_highlight.mp4 --fps 5
```

### Video options

| Option | Values | Default | Description |
|---|---|---|---|
| `--model` | model ID | `gemini-3-flash-preview` | Gemini model to use |
| `--json` | flag | off | Structured JSON output (uses API `response_mime_type`) |
| `--schema` | inline JSON or `.json` path | none | Output JSON schema (auto-enables `--json`) |
| `--fps` | number | `1` | Frame sampling rate (frames per second) |
| `--start` | seconds | none | Clip start offset |
| `--end` | seconds | none | Clip end offset |
| `--media-resolution` | `low`, `medium`, `high` | none | Media resolution (affects token usage) |

---

## Audio analysis (`analyze_audio.py`)

```bash
uv run <skill-dir>/scripts/analyze_audio.py "prompt" audio_file_path [options...]
```

Examples:

```bash
# Verbatim transcription
uv run <skill-dir>/scripts/analyze_audio.py \
  "Transcribe this audio verbatim. If there are multiple speakers, label likely speakers when distinguishable." \
  interview.mp3

# Meeting recording summary
uv run <skill-dir>/scripts/analyze_audio.py \
  "Summarize this meeting recording in 3–5 sentences. Then list the decisions made and the action items as bullet points." \
  meeting.mp3

# Region analysis (timestamps go in the prompt as MM:SS)
uv run <skill-dir>/scripts/analyze_audio.py \
  "Transcribe what is said between 02:30 and 03:29." \
  podcast.mp3

# Speaker and emotion estimation
uv run <skill-dir>/scripts/analyze_audio.py \
  "For this call recording, estimate each distinguishable speaker's speaking style, tone, and emotional shifts over time." \
  call_recording.wav

# Music and ambient sound interpretation
uv run <skill-dir>/scripts/analyze_audio.py \
  "Describe every sound in this audio (music, sound effects, ambient noise) chronologically." \
  ambient.flac

# Structured JSON output (extract meeting minutes)
uv run <skill-dir>/scripts/analyze_audio.py \
  "Extract the agenda items, decisions, and action items from this meeting audio." \
  meeting.mp3 --json
```

### Audio options

| Option | Values | Default | Description |
|---|---|---|---|
| `--model` | model ID | `gemini-3-flash-preview` | Gemini model to use |
| `--json` | flag | off | Structured JSON output (uses API `response_mime_type`) |
| `--schema` | inline JSON or `.json` path | none | Output JSON schema (auto-enables `--json`) |

> Audio doesn't have video-only flags (`--fps`, `--start`, `--end`, `--media-resolution`). Specify a time range inside the prompt itself using `MM:SS` (e.g. `from 00:30 to 02:00`).

---

## Available models

Any Gemini model with multimodal video / audio input support can be passed via `--model`.

| Model ID | Name | Context | Notes |
|---|---|---|---|
| `gemini-3-flash-preview` | Gemini 3 Flash | 1M | **Default.** Top multimodal understanding. |
| `gemini-3.1-flash-lite-preview` | Gemini 3.1 Flash-Lite | 1M | High cost-performance for high-volume / low-latency work. |
| `gemini-3.1-pro-preview` | Gemini 3.1 Pro | 1M | Highest reasoning and agentic capability. |

Do not use `gemini-3-pro-preview`; the Gemini models page marks it as deprecated and shut down. Use `gemini-3.1-pro-preview` for the Pro tier.

---

## Prompting tips

### Timestamp references

Refer to specific moments using `MM:SS`:

```
Describe the diagrams shown at 00:05 and 01:30.
Transcribe what is said between 02:30 and 03:29.
```

### Use both picture and audio (video)

Gemini processes the visual frames and the audio track. Make this explicit when it matters:

```
Describe both what is shown on screen and what is being said.
```

### Non-speech audio interpretation

Gemini understands music, sound effects, and ambient noise — not just speech. Ask for it deliberately:

```
Identify the genre, tempo, and instrumentation of the music in this audio.
Estimate the location and time of day from the ambient sound in the background.
```

### Structured extraction (Structured Output)

Pass `--schema` to get strictly-typed JSON back via the API's `response_mime_type` + `response_json_schema`. Unlike prompt-based JSON output, types and required fields are guaranteed at the API level.

```bash
# Video — scene-analysis schema
uv run <skill-dir>/scripts/analyze_video.py \
  "Analyze the scenes in this video." \
  video.mp4 \
  --schema '{"type":"object","properties":{"scenes":{"type":"array","items":{"type":"object","properties":{"timestamp":{"type":"string"},"visual":{"type":"string"},"audio":{"type":"string"},"objects":{"type":"array","items":{"type":"string"}}},"required":["timestamp","visual","audio","objects"]}}},"required":["scenes"]}'

# Audio — meeting-minutes schema
uv run <skill-dir>/scripts/analyze_audio.py \
  "Extract minutes from this meeting recording." \
  meeting.mp3 \
  --schema '{"type":"object","properties":{"agenda_items":{"type":"array","items":{"type":"string"}},"decisions":{"type":"array","items":{"type":"string"}},"action_items":{"type":"array","items":{"type":"object","properties":{"task":{"type":"string"},"owner":{"type":"string"},"due":{"type":"string"}}}}},"required":["agenda_items","decisions","action_items"]}'

# Schema in a .json file
uv run <skill-dir>/scripts/analyze_video.py \
  "Extract action items from this meeting video." \
  meeting.mp4 \
  --schema action_items_schema.json

# Loose JSON output (no schema constraint, format only)
uv run <skill-dir>/scripts/analyze_audio.py \
  "List every likely speaker's utterances in chronological order." \
  audio.mp3 --json
```

---

## Token-usage rough numbers

### Video

| Setting | Tokens / sec | Per minute | Per 10 minutes |
|---|---|---|---|
| Default resolution (1 fps) | ~300 | ~18,000 | ~180,000 |
| Low resolution (1 fps) | ~100 | ~6,000 | ~60,000 |

### Audio

| Setting | Tokens / sec | Per minute | Per 10 minutes | Per hour |
|---|---|---|---|---|
| Standard | 32 | ~1,920 | ~19,200 | ~115,200 |

Audio is dramatically cheaper than video. Even multi-hour recordings stay reasonable.

For long video that you analyze repeatedly, narrow the range with `--start` / `--end`. For long audio, narrow it inside the prompt (`from 02:30 to 03:29`).

---

## Supported formats

### Video
`.mp4`, `.mpeg`, `.mov`, `.avi`, `.flv`, `.mpg`, `.webm`, `.wmv`, `.3gp`

### Audio
`.mp3`, `.wav`, `.aac`, `.m4a`, `.ogg`, `.flac`, `.aiff`

---

## Inline vs Files API behavior

### Video

| Size | Behavior |
|---|---|
| ≤20 MB total request size | Sent inline (faster) |
| >20 MB total request size, long videos, or repeated analysis | Uploaded via the Files API first |

### Audio

| Size | Behavior |
|---|---|
| ≤20 MB | Sent inline (faster) |
| >20 MB | Uploaded via the Files API first |

> The 20 MB ceiling for audio comes from the Gemini API's per-request total-size limit. Going through the Files API allows audio of up to 9.5 hours per request.

The Files API limit is 20 GB on paid tiers and 2 GB on free tiers.

---

## Limitations

- **Video** — Per-request video length is bounded by the model context window in practice.
- **Audio** — Up to 9.5 hours per prompt (combined across multiple files if you pass several).
- Audio is downsampled to 16 kbps and multichannel is collapsed to a single channel.
- Safety filters apply.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GEMINI_API_KEY` is unset | Define it in the OS environment or a nearby `.env` file. |
| `google-genai` not found | If running with `uv run` or `pipx run`, dependencies auto-resolve. If using plain `python3`, run `pip install google-genai python-dotenv` first. |
| Empty response | Likely blocked by a safety filter. Adjust the prompt. |
| Upload is slow | Video files >20 MB total request size, long videos, repeated video analyses, and audio files >20 MB go through the Files API. Narrow the range with `--start` / `--end` (video) or inside the prompt (audio). |
| Fast motion missed in video | Increase `--fps` (e.g. `--fps 5`). Token usage rises accordingly. |
| Hitting token limits | For video, drop `--media-resolution low` and/or use `--start` / `--end`. For audio, narrow the time range inside the prompt. |
| Audio transcription accuracy is low | State the language and number of speakers in the prompt (e.g. "two-person Japanese conversation"). For long recordings, analyze in chunks. |

---

## Common patterns

### Video

| Use case | Example prompt |
|---|---|
| Meeting minutes | "Transcribe this meeting video and organize it by agenda item. Also extract the decisions and action items." |
| Product-review analysis | "List the positive points and negative points mentioned about the product in this review video." |
| Lecture summary | "Summarize the key points of this lecture and write 5 review questions for study." |
| Competitor ad analysis | "Analyze the target audience, value proposition, CTA, and creative techniques used in this ad video." |
| QC inspection | "In this manufacturing-line video, identify any anomalies or issues with timestamps." |
| Social-video transcription | "Transcribe everything that's said in this video." |

### Audio

| Use case | Example prompt |
|---|---|
| Meeting recording → minutes | "Transcribe this meeting recording and organize it by agenda. Extract decisions and action items." |
| Podcast summary | "Summarize the main topics and the speakers' arguments in this podcast episode." |
| Customer-call quality review | "For this call recording, analyze the customer's pain points, the agent's response quality, and concrete improvement opportunities." |
| Interview transcription | "Transcribe this interview audio with speakers labeled. Pull out 5 quotable lines." |
| Lecture / seminar summary | "Organize the main points of this seminar audio into chapters with a summary per chapter." |
| Multilingual translation | "Transcribe this audio and translate it to English. Show original and translation side by side." |
| Music / ambient analysis | "From the music (genre, tempo, instrumentation) and ambient sound, infer the scene and location." |
