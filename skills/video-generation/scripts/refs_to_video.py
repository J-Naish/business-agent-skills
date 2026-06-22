#!/usr/bin/env python3
"""
Veo 3.1 — generate a video using reference images (Ingredients to Video)

Usage:
  python3 refs_to_video.py "prompt" --images image1 [image2] [image3] [options...]

Options:
  --images <paths...>               Reference images (1–3 required)
  --output <filename>               Output filename (default: generated_video.mp4)
  --aspect-ratio <16:9|9:16>        Aspect ratio (default: 16:9)
  --duration <4|6|8>                Length in seconds (default: 8)
  --resolution <720p|1080p|4k>      Resolution (default: 720p)
  --negative-prompt <text>          Elements to exclude
  --person-generation <allow_all|allow_adult>  Permission for generating people
  --poll-interval <seconds>         Status polling interval (default: 10)
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai",
#     "python-dotenv",
# ]
# ///

import argparse
import os
import sys
import time

from google import genai
from google.genai import types

SUPPORTED_EXTENSIONS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def load_api_key():
    """Resolve GEMINI_API_KEY from os.environ or the nearest .env file."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key

    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:
        pass
    else:
        env_path = find_dotenv(usecwd=True)
        if env_path:
            load_dotenv(env_path)
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                return api_key

    print(
        "ERROR: GEMINI_API_KEY is not set. Define it in the OS environment or a nearby .env file.",
        file=sys.stderr,
    )
    sys.exit(1)


def load_image(path: str) -> types.Image:
    ext = os.path.splitext(path)[1].lower()
    mime = SUPPORTED_EXTENSIONS.get(ext)
    if not mime:
        print(f"ERROR: unsupported image format: {ext}", file=sys.stderr)
        print(f"  Supported formats: {', '.join(SUPPORTED_EXTENSIONS.keys())}", file=sys.stderr)
        sys.exit(1)
    with open(path, "rb") as f:
        data = f.read()
    return types.Image(image_bytes=data, mime_type=mime)


def main():
    parser = argparse.ArgumentParser(description="Veo 3.1 ingredients to video")
    parser.add_argument("prompt", help="Video generation prompt")
    parser.add_argument("--images", nargs="+", required=True, help="Reference images (1–3)")
    parser.add_argument("--output", default="generated_video.mp4", help="Output filename")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--duration", type=int, default=8)
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--negative-prompt", default=None)
    parser.add_argument("--person-generation", default=None)
    parser.add_argument("--poll-interval", type=int, default=10)
    args = parser.parse_args()

    if len(args.images) > 3:
        print(f"ERROR: at most 3 reference images are supported (got {len(args.images)}).", file=sys.stderr)
        sys.exit(1)


    api_key = load_api_key()

    for path in args.images:
        if not os.path.isfile(path):
            print(f"ERROR: image not found: {path}", file=sys.stderr)
            sys.exit(1)

    client = genai.Client(api_key=api_key)
    model = "veo-3.1-generate-preview"

    print(f"🎬 Veo 3.1 ingredients to video — generating...")
    print(f"   Model: {model}")
    print(f"   Reference images: {len(args.images)}")
    for i, img in enumerate(args.images):
        print(f"     [{i+1}] {img}")
    print(f"   Prompt: {args.prompt}")
    print(f"   Aspect ratio: {args.aspect_ratio}")
    print(f"   Duration: {args.duration}s")
    print(f"   Resolution: {args.resolution}")

    reference_images = []
    for path in args.images:
        image = load_image(path)
        ref = types.VideoGenerationReferenceImage(
            image=image,
            reference_type="asset",
        )
        reference_images.append(ref)

    config = types.GenerateVideosConfig(
        aspect_ratio=args.aspect_ratio,
        duration_seconds=args.duration,
        resolution=args.resolution,
        reference_images=reference_images,
    )
    if args.negative_prompt:
        config.negative_prompt = args.negative_prompt
    if args.person_generation:
        config.person_generation = args.person_generation

    operation = client.models.generate_videos(
        model=model,
        prompt=args.prompt,
        config=config,
    )

    print(f"\n⏳ Waiting for generation to finish (polling every {args.poll_interval}s)")

    while not operation.done:
        time.sleep(args.poll_interval)
        operation = client.operations.get(operation)
        print(".", end="", flush=True)
    print()

    if not operation.response or not operation.response.generated_videos:
        print("❌ Video generation failed.", file=sys.stderr)
        sys.exit(1)

    video = operation.response.generated_videos[0]

    print("📥 Downloading video...")
    client.files.download(file=video.video)
    video.video.save(args.output)

    print(f"\n✅ Video saved to: {args.output}")


if __name__ == "__main__":
    main()
