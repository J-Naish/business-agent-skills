---
name: image-generation
description: Generate or edit images using Google's Nano Banana / Nano Banana Pro (Gemini Image) or OpenAI's gpt-image-2. Use this skill whenever the user mentions image generation, AI images, thumbnails, banners, posters, hero images, infographics, diagrams, product photos, mockups, illustrations, photo generation, image editing, Nano Banana, gpt-image, or generating images with Gemini or OpenAI. Strong at rendering text accurately inside images (including non-Latin scripts) and equally suitable for purely visual content.
---

# Image Generation & Editing

This skill supports two providers — pick whichever fits the task at hand. Both can do text-to-image generation and image editing (including multi-reference composition).

| Provider | Models | Best for |
|---|---|---|
| **Google Gemini** (Nano Banana) | `gemini-3.1-flash-image-preview`, `gemini-3-pro-image-preview` | Aspect-ratio based output, text-in-image (especially non-Latin scripts), composition with up to 11–14 reference images. |
| **OpenAI** (gpt-image-2) | `gpt-image-2` | Pixel-precise sizing, mask-based localized editing, generating multiple variants in one call (`--n`), output formats beyond PNG (jpeg/webp). |

If the user doesn't specify, default to **Gemini Nano Banana (`gemini-3.1-flash-image-preview`)** — fastest and cheapest for everyday tasks.

---

## Prerequisites

- **Python 3.10+** must be installed.
- The relevant API key is assumed to already be available from the OS environment or a nearby `.env` file:
  - `GEMINI_API_KEY` for Google Gemini scripts
  - `OPENAI_API_KEY` for OpenAI scripts

Do not print, inspect, edit, or commit secret values.

### How to run the scripts

The scripts are written as [PEP 723](https://peps.python.org/pep-0723/) inline scripts — their dependencies are declared at the top of each file. Any of the following invocation styles works:

```bash
# Option A: uv (recommended — fastest, auto-resolves dependencies)
uv run <skill-dir>/scripts/<provider>/text_to_image.py "prompt"

# Option B: pipx (when uv isn't available)
pipx run <skill-dir>/scripts/<provider>/text_to_image.py "prompt"

# Option C: pip + plain python (most universal — install dependencies once)
pip install google-genai openai python-dotenv
python3 <skill-dir>/scripts/<provider>/text_to_image.py "prompt"
```

The command examples below use the shortest form, `uv run`, but Options B and C run the same scripts identically.

---

## Models

### Gemini

| Model | Model ID | Use for |
|---|---|---|
| **Nano Banana** | `gemini-3.1-flash-image-preview` | Fast and inexpensive (default). Use for everyday tasks. |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | Highest quality. Reserve for production work where text fidelity or photo quality is critical. |

Switch from Flash to Pro only when quality is decisive — for example: accurate text rendering inside the image is required, a high-quality photographic look is needed (ads, production landing pages), or information-dense infographics demand fine detail.

| Spec | Nano Banana Pro | Nano Banana |
|---|---|---|
| **Aspect ratios** | `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` | All of the above plus `1:4`, `1:8`, `4:1`, `8:1` |
| **Image size** | `1K` (default), `2K`, `4K` | `512px`, `1K`, `2K`, `4K` |
| **Reference image limit** | Up to 11 (6 object + 5 character) | Up to 14 (10 object + 4 character) |

### GPT Image

| Model | Model ID | Use for |
|---|---|---|
| **GPT Image 2** | `gpt-image-2` | High-quality generation and editing with pixel-precise sizing, mask-based local edits, and multi-variant output. |

| Spec | gpt-image-2 |
|---|---|
| **Sizing** | Absolute pixel sizes — both edges multiples of 16, max 3840, max aspect ratio 3:1. Common presets: `1024x1024`, `1024x1536`, `1536x1024`, `2048x2048`. Pass `auto` to let the model pick. |
| **Quality** | `low`, `medium`, `high`, `auto` (default) |
| **Output format** | `png` (default), `jpeg`, `webp` (with `--output-compression 0–100` for jpeg/webp) |
| **Multiple variants** | `--n` to generate several images in a single call |
| **Mask-based editing** | `--mask` with an alpha-channel PNG matching the primary image's dimensions |

---

## Pricing (approximate, Standard tier)

Pricing changes — always check the live pricing pages before relying on these numbers.

### Gemini

Per-image output cost by resolution. Input is billed separately at $0.50/1M tokens (Flash) or $2/1M tokens (Pro).

| Model | 512px | 1K | 2K | 4K |
|---|---|---|---|---|
| Nano Banana Flash (`gemini-3.1-flash-image-preview`) | ~$0.045 | ~$0.067 | ~$0.101 | ~$0.15 |
| Nano Banana Pro (`gemini-3-pro-image-preview`) | — | ~$0.134 | ~$0.134 | ~$0.24 |

Source: [Vertex AI generative AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing).

### OpenAI gpt-image-2

Per-image cost by quality and aspect. Input is billed separately at $5/1M text-input tokens, $8/1M image-input tokens, $30/1M image-output tokens.

| Quality | 1024×1024 | Non-square (e.g. 1024×1536, 1536×1024) |
|---|---|---|
| Low | ~$0.006 | ~$0.005 |
| Medium | ~$0.053 | ~$0.041 |
| High | ~$0.211 | ~$0.165 |

For exact estimates, use OpenAI's [image generation calculator](https://developers.openai.com/api/docs/guides/image-generation#calculating-costs). Source: [OpenAI pricing](https://developers.openai.com/api/docs/pricing).

---

## Workflow

### Before generating

Collect the following from the user. If anything is missing, ask:

1. **Use case** — Thumbnail, banner, product photo, social post, etc.?
2. **Subject** — What's being depicted?
3. **Style** — Photographic, illustration, 3D?
4. **Text** — Any text to render inside the image?
5. **Size / aspect ratio** — Landscape (16:9), square (1:1), portrait (9:16)?
6. **Reference images** — Anything to edit, or images to use as a style or composition reference?
7. **Provider preference** — Gemini (default) or OpenAI?

### Picking the right script

| Situation | Script |
|---|---|
| No reference image — generate from scratch | `<provider>/text_to_image.py` |
| Reference image — edit it (change background, add text, retouch a region) | `<provider>/image_to_image.py` |
| Reference image — use it as style or composition reference for a new image | `<provider>/image_to_image.py` |
| Combine multiple images into one | `<provider>/image_to_image.py` (pass extras with `--images`) |
| Localized edit limited to a specific region | `gpt-image/image_to_image.py --mask <mask.png>` |
| Generate multiple variants in one call | `gpt-image/text_to_image.py --n N` |

If in doubt: do you have a reference image? Yes → `image_to_image.py`. No → `text_to_image.py`. Default provider → `gemini/`. Switch to `gpt-image/` when its specific strengths apply.

> In the command examples below, replace `<skill-dir>` with the actual path where this skill is installed. Scripts live under `<skill-dir>/scripts/gemini/` and `<skill-dir>/scripts/gpt-image/`.

---

## Gemini commands

### Text-to-image

```bash
uv run <skill-dir>/scripts/gemini/text_to_image.py "prompt" [output filename] [options...]
```

| Option | Default | Description |
|---|---|---|
| `--model` | `gemini-3.1-flash-image-preview` | Model ID |
| `--aspect-ratio` | none | Aspect ratio (e.g. `16:9`, `1:1`, `9:16`) |
| `--image-size` | none | Image size (`512px`, `1K`, `2K`, `4K`) |

Examples:

```bash
# Basic generation (default model: Nano Banana Flash)
uv run <skill-dir>/scripts/gemini/text_to_image.py "A cute cat sitting on a windowsill at sunset"

# With output filename, aspect ratio, and image size
uv run <skill-dir>/scripts/gemini/text_to_image.py "Product package mockup on white background, studio lighting, soft shadows" mockup.png --aspect-ratio 1:1 --image-size 2K

# Switch to the high-quality Pro model
uv run <skill-dir>/scripts/gemini/text_to_image.py "Premium product photo with precise typographic overlay" hero.png --model gemini-3-pro-image-preview
```

### Image-to-image

```bash
uv run <skill-dir>/scripts/gemini/image_to_image.py "edit instruction" reference_image_path [output filename] [options...]
```

| Option | Default | Description |
|---|---|---|
| `--model` | `gemini-3.1-flash-image-preview` | Model ID |
| `--aspect-ratio` | none | Aspect ratio |
| `--image-size` | none | Image size |
| `--images` | none | Additional reference images (multiple allowed) |

Examples:

```bash
# Replace the background
uv run <skill-dir>/scripts/gemini/image_to_image.py "Change the background to a cherry blossom avenue in full bloom, blend edges naturally" input.png edited.png

# Add a text overlay on top of an image
uv run <skill-dir>/scripts/gemini/image_to_image.py 'Add "SPRING SALE NOW ON" in large white sans-serif bold text at the top center, with a subtle drop shadow' product.png sale_banner.png

# Combine multiple reference images into a unified composition
uv run <skill-dir>/scripts/gemini/image_to_image.py "Combine all products into a unified catalog-style image on white background, consistent lighting" product1.png catalog.png --images product2.png product3.png
```

---

## GPT Image commands

### Text-to-image

```bash
uv run <skill-dir>/scripts/gpt-image/text_to_image.py "prompt" [output filename] [options...]
```

| Option | Default | Description |
|---|---|---|
| `--model` | `gpt-image-2` | Model ID |
| `--size` | `auto` | Image size, e.g. `1024x1024`, `1536x1024`, `2048x2048`, or `auto` |
| `--quality` | `auto` | `low`, `medium`, `high`, `auto` |
| `--output-format` | `png` | `png`, `jpeg`, `webp` |
| `--output-compression` | none | 0–100 (jpeg/webp only) |
| `--n` | `1` | Number of images to generate in one call |

Examples:

```bash
# Basic generation
uv run <skill-dir>/scripts/gpt-image/text_to_image.py "Studio product shot of a ceramic teapot on a marble counter, soft daylight"

# Specific size and high quality, JPEG output
uv run <skill-dir>/scripts/gpt-image/text_to_image.py "Hero banner: minimalist mountain landscape at dawn" hero.jpg --size 1536x1024 --quality high --output-format jpeg --output-compression 85

# Generate four variants in one call
uv run <skill-dir>/scripts/gpt-image/text_to_image.py "App icon concept, geometric, vibrant gradient" icon.png --n 4
```

### Image-to-image

```bash
uv run <skill-dir>/scripts/gpt-image/image_to_image.py "edit instruction" reference_image_path [output filename] [options...]
```

| Option | Default | Description |
|---|---|---|
| `--model` | `gpt-image-2` | Model ID |
| `--size` | `auto` | Output size |
| `--quality` | `auto` | `low`, `medium`, `high`, `auto` |
| `--output-format` | `png` | `png`, `jpeg`, `webp` |
| `--output-compression` | none | 0–100 (jpeg/webp only) |
| `--mask` | none | Alpha-channel PNG limiting the edit to a specific region |
| `--images` | none | Additional reference images (multiple allowed) |
| `--n` | `1` | Number of variants to generate |

Examples:

```bash
# Background replacement
uv run <skill-dir>/scripts/gpt-image/image_to_image.py "Replace the background with a soft beige studio backdrop" product.png edited.png

# Mask-based localized edit (only the masked region changes)
uv run <skill-dir>/scripts/gpt-image/image_to_image.py "Add a flamingo standing in the pool" lounge.png composition.png --mask lounge_mask.png

# Combine four reference images into one composition
uv run <skill-dir>/scripts/gpt-image/image_to_image.py "Arrange these as a flat-lay product set on a wooden table" body-lotion.png set.png --images bath-bomb.png incense.png soap.png
```

---

## Prompt-writing fundamentals

**Write the instruction in English.** The model produces stronger results when the surrounding instruction is in English. The text strings to be rendered *inside* the image can be in any language.

Provider-specific prompt guides live under `references/`:
- Gemini: [references/gemini.md](references/gemini.md) — photography vocabulary, aspect-ratio output, text in non-Latin scripts.
- OpenAI: [references/gpt-image.md](references/gpt-image.md) — director-style art direction, mask-based edits, multi-image composition.

Read the one matching the provider you're using.

### Quick reference

1. **Write the instruction in English.** Text to be rendered inside the image can be in any language.
2. **Be specific.** Spell out the subject, composition, style, color, and mood.
3. **Use camera vocabulary.** `low angle`, `telephoto lens`, `bokeh`, `natural light` are highly effective.
4. **Quote rendered text.** `Place "GRAND OPENING" in large bold text at the top`.
5. **Use negatives.** `no text, no watermark`.

### Prompt structure template

```
[Detailed description of the subject].
[Camera setup: lens, angle, depth of field].
[Lighting: type and direction of light source].
[Color tone and mood].
[Additional instructions: text placement, exclusions, etc.]
```

---

## Common business patterns

| Use case | Example prompt |
|---|---|
| Thumbnail | `YouTube thumbnail, landscape 16:9. Surprised person on the left, "WHAT HAPPENED NEXT" in large bold white text on the right. Gradient background, high contrast` |
| Product mockup | `Minimal product photography on white background. Glass perfume bottle with "AURORA" label. Soft studio lighting, natural shadow` |
| Social banner | `Square image for Instagram post. Cozy cafe interior photo with "GRAND OPENING" text overlay in elegant serif font. Brand accent color` |
| Infographic | `Business flow infographic on white background. 3 steps arranged left to right, each with an icon and a short caption underneath` |
| Real-estate ad | `Luxury apartment exterior photo. Semi-transparent banner at bottom with "South-facing units, 3 min from station" in white text. Professional real estate photography` |

For per-use-case prompt templates, see the prompt guide for your provider:
- [references/gemini.md](references/gemini.md)
- [references/gpt-image.md](references/gpt-image.md)

---

## Limitations

- **Watermarks**: Gemini-generated images carry an invisible SynthID watermark. OpenAI-generated images include C2PA provenance metadata.
- **Safety filters**: Both providers may block or modify generation involving real people, violence, or other restricted content.
- **Rate limits**: Both APIs have per-minute and per-day quotas — see each provider's docs for details.
- **Backgrounds (gpt-image-2)**: Transparent backgrounds aren't currently supported; the API returns opaque backgrounds.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GEMINI_API_KEY` / `OPENAI_API_KEY` is unset | Define the relevant variable in the OS environment or a nearby `.env` file. |
| `google-genai` or `openai` not found | If running with `uv run` or `pipx run`, dependencies auto-resolve. If using plain `python3`, run `pip install google-genai openai python-dotenv` first. |
| Only text comes back, no image (Gemini) | Adjust the prompt or switch models. |
| Safety filter blocks the request | Adjust the prompt — avoid people-heavy or violent imagery. |
| Empty response | Verify the API key's validity and quota in the provider's console. |
| Text inside the image renders incorrectly | Reduce the amount of text and/or switch to a higher-quality model (`gemini-3-pro-image-preview` or `gpt-image-2 --quality high`). |
| Image doesn't match the intent | Structure the prompt more clearly and lean on negative instructions. Use `--mask` (OpenAI) for region-limited edits. |
| OpenAI: aspect ratio rejected | Both edges must be multiples of 16, max 3840, max ratio 3:1. |

---

## Task-specific questions to ask

1. What's the use case for the image? (Thumbnail, banner, product photo, social post, etc.)
2. Should there be text inside the image? If so, what should it say?
3. Any style preference — photographic, illustration, 3D?
4. Aspect ratio or specific pixel size?
5. Any reference images, or an existing image to edit?
6. Provider preference — Gemini (default) or OpenAI? Any reason for the choice (e.g. need mask-based editing, multiple variants, specific output format)?
7. Brand colors or design guidelines to follow?
