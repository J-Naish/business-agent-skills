#!/usr/bin/env python3
"""
Veo 3.1 — generate a video starting from an input image (image-to-video)

Usage:
  python3 image_to_video.py "prompt" input_image_path [output filename] [options...]

Options:
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
    parser = argparse.ArgumentParser(description="Veo 3.1 image-to-video")
    parser.add_argument("prompt", help="Video generation prompt")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("output", nargs="?", default="generated_video.mp4", help="Output filename")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--duration", type=int, default=8)
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--negative-prompt", default=None)
    parser.add_argument("--person-generation", default=None)
    parser.add_argument("--poll-interval", type=int, default=10)
    args = parser.parse_args()


    api_key = load_api_key()

    if not os.path.isfile(args.image):
        print(f"ERROR: image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    model = "veo-3.1-generate-preview"
    image = load_image(args.image)

    print(f"🎬 Veo 3.1 image-to-video — generating...")
    print(f"   Model: {model}")
    print(f"   Input image: {args.image}")
    print(f"   Prompt: {args.prompt}")
    print(f"   Aspect ratio: {args.aspect_ratio}")
    print(f"   Duration: {args.duration}s")
    print(f"   Resolution: {args.resolution}")

    config = types.GenerateVideosConfig(
        aspect_ratio=args.aspect_ratio,
        duration_seconds=args.duration,
        resolution=args.resolution,
    )
    if args.negative_prompt:
        config.negative_prompt = args.negative_prompt
    if args.person_generation:
        config.person_generation = args.person_generation

    operation = client.models.generate_videos(
        model=model,
        prompt=args.prompt,
        image=image,
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
