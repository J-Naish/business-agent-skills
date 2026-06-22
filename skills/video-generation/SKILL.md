---
name: video-generation
description: Generate or edit AI video using Google's Veo 3.1. Supports text-to-video, image-to-video, first-and-last-frame interpolation, and ingredients-to-video (reference images for consistent characters or products). Synchronized audio — dialogue, sound effects, ambient — is generated alongside the video. Use this skill whenever the user mentions video generation, AI video, Veo, motion graphics, animated clips, social video shorts, product video, or generating a movie clip with Gemini.
---

# Video Generation (Veo 3.1)

Generate high-quality short-form video with Google's Veo 3.1 API. The skill bundles four scripts covering the four input shapes Veo supports: text-only, single image, first/last frame interpolation, and reference ingredients.

## Directory layout

```
video-generation/
├── SKILL.md                        # This file (workflow, script usage, options)
├── references/
│   └── prompt-guide.md             # Detailed prompt reference (5-element formula, cinematography vocabulary, audio direction, templates)
└── scripts/
    ├── text_to_video.py            # Text → video (default)
    ├── image_to_video.py           # Image → video (animate from a starting frame)
    ├── keyframes_to_video.py       # First + last image → video (frame interpolation)
    └── refs_to_video.py            # Reference images → video (preserve characters / products)
```

## What Veo 3.1 is good at

- **Synchronized audio** — Include dialogue, sound effects, or ambient direction in the prompt and the model produces matching audio for the video.
- **High-quality output** — Up to 4K resolution, up to 8 seconds per clip.
- **Image-to-video** — Use a still image as the opening frame and animate from there.
- **First & Last Frame** — Provide a start image and an end image; Veo interpolates the motion between them.
- **Ingredients to Video** — Pass up to three reference images (people, objects, style) and Veo preserves their look in the generated clip.
- **Multi-shot sequences** — Place several shots within a single 8-second clip via timestamp prompting (`[00:00-00:02]` … `[00:06-00:08]`).
- **Negative prompts** — Explicitly exclude unwanted elements.

> Veo 2 additionally supports adding or removing objects in an existing video, but without audio. This skill targets Veo 3.1; reach for Veo 2 directly when the object add/remove capability is needed.

---

## Prerequisites

- **Python 3.10+** must be installed.
- `GEMINI_API_KEY` is assumed to already be available from the OS environment or a nearby `.env` file.
- Do not print, inspect, edit, or commit secret values.

### How to run the scripts

The scripts are written as [PEP 723](https://peps.python.org/pep-0723/) inline scripts — their dependencies (`google-genai`, `python-dotenv`) are declared at the top of each file. Any of the following invocation styles works:

```bash
# Option A: uv (recommended — fastest, auto-resolves dependencies)
uv run <skill-dir>/scripts/text_to_video.py "prompt"

# Option B: pipx (when uv isn't available)
pipx run <skill-dir>/scripts/text_to_video.py "prompt"

# Option C: pip + plain python (most universal — install dependencies once)
pip install google-genai python-dotenv
python3 <skill-dir>/scripts/text_to_video.py "prompt"
```

The command examples below use the shortest form, `uv run`, but Options B and C run the same scripts identically.

---

## Workflow

### Before generating

Collect the following from the user. If anything is missing, ask:

1. **Use case** — Social post, product showcase, ad, slide-deck visual, etc.?
2. **Scene** — What's being shown? What's moving?
3. **Audio** — Any dialogue or sound effects required? If so, what should they say or sound like?
4. **Aspect ratio** — Landscape (16:9) or vertical (9:16)?
5. **Length** — 4, 6, or 8 seconds?
6. **Reference images** — Anything to use as a starting frame, end frame, or character/style reference?

### Recommended workflow: still image → confirm → video

Video generation is expensive and slow to iterate on. The recommended pattern is to **first produce a still image of the intended look, confirm direction with the user, and only then generate video**. The image step is fast and cheap; it lets you lock the composition and subject before paying for a video pass.

Three patterns cover most needs:

#### Pattern A: Starting frame → Image-to-Video (default)

The most general pattern. The starting frame fixes composition and subject up front.

1. Produce the starting-frame still (e.g. with an image-generation tool).
2. Show it to the user and **confirm: "is this the direction you want for the video?"**
3. Once approved, run `image_to_video.py`.

#### Pattern B: Start + end frame → First & Last Frame (camera moves, transformations)

Useful for big camera moves, day-to-night transitions, morphs, or anything that's defined by where you start and where you end.

1. Produce both the start and end stills.
2. Confirm with the user: "is this the start and end you want Veo to interpolate between?"
3. Once approved, run `keyframes_to_video.py`.

#### Pattern C: Reference assets → Ingredients to Video (consistent characters / products)

Useful when a specific character, product, or styled asset must appear unchanged across the clip — common for ad spots and series content.

1. Produce 1–3 reference images (character, product, environment).
2. Confirm with the user: "should the video use these as the source of truth for look?"
3. Once approved, run `refs_to_video.py`.

#### Pattern selection

| Use case | Pattern |
|---|---|
| General clips (landscape, product showcase, social) | A: starting frame → Image-to-Video |
| Camera moves, viewpoint shifts, time-lapses | B: start + end frame → First & Last Frame |
| Multiple cuts that need a consistent character or product | C: reference assets → Ingredients to Video |
| Quick test or throwaway clip | Direct text-to-video (skip the image step) |

If the user already has the reference images they want, skip the still-generation step and go straight to the matching script.

> In the command examples below, replace `<skill-dir>` with the actual path where this skill is installed. Scripts live under `<skill-dir>/scripts/`.

### Text-to-video

```bash
uv run <skill-dir>/scripts/text_to_video.py "prompt" [output filename] [options...]
```

Examples:

```bash
# Basic generation
uv run <skill-dir>/scripts/text_to_video.py \
  "A golden retriever running through a sunlit meadow in slow motion. Cinematic look."

# Vertical short-form clip
uv run <skill-dir>/scripts/text_to_video.py \
  "A barista making latte art in a cozy cafe. Close-up shot." \
  cafe_short.mp4 \
  --aspect-ratio 9:16 --duration 6

# With dialogue + ambient audio
uv run <skill-dir>/scripts/text_to_video.py \
  "A woman standing in front of a whiteboard, speaking to the camera: 'Today we'll learn about solar energy.' The room has soft ambient sounds." \
  presentation.mp4

# With a negative prompt
uv run <skill-dir>/scripts/text_to_video.py \
  "Aerial view of a coastal city at sunset. Cinematic drone footage." \
  city_aerial.mp4 \
  --negative-prompt "text, watermark, blurry, low quality"
```

### Image-to-video

Use a still as the opening frame and animate from there:

```bash
uv run <skill-dir>/scripts/image_to_video.py "prompt" input_image_path [output filename] [options...]
```

Examples:

```bash
# Animate a product still
uv run <skill-dir>/scripts/image_to_video.py \
  "The product slowly rotates on a turntable. Soft studio lighting." \
  product.png product_video.mp4

# Animate a landscape photo
uv run <skill-dir>/scripts/image_to_video.py \
  "Clouds slowly move across the sky. A gentle breeze rustles the leaves." \
  landscape.jpg landscape_animated.mp4
```

### First & Last Frame (interpolation)

Provide a start image and an end image; Veo interpolates between them. **Duration is fixed at 8 seconds for this mode.**

```bash
uv run <skill-dir>/scripts/keyframes_to_video.py "prompt" first_image_path last_image_path [output filename] [options...]
```

Examples:

```bash
# 180° arc shot from front to back of the singer
uv run <skill-dir>/scripts/keyframes_to_video.py \
  "The camera performs a smooth 180-degree arc shot, starting with the front-facing view of the singer and circling around her." \
  singer_front.png singer_back.png singer_arc.mp4

# Day → night time lapse
uv run <skill-dir>/scripts/keyframes_to_video.py \
  "Time-lapse of a city skyline transitioning from day to night. Lights gradually turn on." \
  city_day.jpg city_night.jpg timelapse.mp4
```

### Ingredients to Video (reference assets)

Up to 3 reference images (people, objects, environments) are used to keep the look consistent. Useful for series content where a character or product needs to stay on-model.

```bash
uv run <skill-dir>/scripts/refs_to_video.py "prompt" --images image1 [image2] [image3] [options...]
```

Examples:

```bash
# Dialogue scene with character + setting references
uv run <skill-dir>/scripts/refs_to_video.py \
  "The detective behind his desk looks up and says in a weary voice, 'Of all the offices in this town, you had to walk into mine.'" \
  --images detective.png office_setting.png \
  --output detective_scene.mp4

# Product ad referencing two product angles
uv run <skill-dir>/scripts/refs_to_video.py \
  "A sleek product showcase with soft studio lighting. The headphone rotates slowly on a reflective surface." \
  --images headphone_front.png headphone_side.png \
  --output product_ad.mp4 --aspect-ratio 9:16
```

---

## Options

| Option | Values | Default | Description |
|---|---|---|---|
| `--aspect-ratio` | `16:9`, `9:16` | `16:9` | Landscape or vertical |
| `--duration` | `4`, `6`, `8` | `8` | Clip length in seconds |
| `--resolution` | `720p`, `1080p`, `4k` | `720p` | Output resolution (1080p / 4k require an 8-second clip) |
| `--negative-prompt` | text | none | Elements to exclude (not supported by Ingredients to Video) |
| `--person-generation` | `allow_all` | none | Permission for generating people (`allow_adult` is not supported) |
| `--poll-interval` | seconds | `10` | Seconds between status polls while waiting for generation |

---

## Prompt-writing fundamentals

Write prompts in English. Compose around the **5-element formula**: `[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]`. Quote dialogue, prefix sound effects with `SFX:`, and prefix ambient with `Ambient:`.

For the cinematography vocabulary, audio-direction patterns, timestamp prompting (multiple shots in one 8-second clip), and per-use-case templates, see [references/prompt-guide.md](references/prompt-guide.md).

---

## Limitations

- Video generation is asynchronous; expect several minutes per request.
- Maximum clip length per request is 8 seconds.
- 1080p and 4K resolutions require an 8-second clip.
- People generation is subject to safety filters and may be restricted by region.
- The API has rate limits.
- Generated videos include an invisible SynthID watermark.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GEMINI_API_KEY` is unset | Define it in the OS environment or a nearby `.env` file. |
| `google-genai` not found | If running with `uv run` or `pipx run`, dependencies auto-resolve. If using plain `python3`, run `pip install google-genai python-dotenv` first. |
| Generation takes a long time | A few minutes is normal. Adjust `--poll-interval` if needed. |
| Safety filter blocks the request | Adjust the prompt. Try `--person-generation allow_all` if you need people. |
| Resolution `1080p` / `4k` errors | These require `--duration 8`; specify it explicitly. |
| Clip is the wrong length | Specify `--duration 4`, `6`, or `8` explicitly. |
| Output doesn't match intent | Make the prompt more specific — describe camera motion, lighting, and action in detail. |

---

## Combining with other tools

- **Still-image generation upstream** — Producing the starting frame, end frame, or reference assets as stills first lets you lock direction cheaply before committing to a video pass. The Pattern A / B / C workflow above assumes this.
- **Post-processing downstream** — When you need text overlays, captions, transitions, music mixing, multi-clip stitching, or animated charts that exceed what generation alone can produce, render the Veo clips out and finish them in a dedicated video-editing tool.
