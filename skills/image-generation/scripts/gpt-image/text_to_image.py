#!/usr/bin/env python3
"""
OpenAI Image Generation — generate an image from a text prompt with gpt-image-2

Usage:
  python3 text_to_image.py "prompt" [output filename] [options...]

Options:
  --model <model_id>           Model ID (default: gpt-image-2)
  --size <WxH>                 Image size (default: auto). Both edges multiples of 16,
                               max 3840, max aspect ratio 3:1. Common presets:
                               1024x1024, 1024x1536, 1536x1024, 2048x2048.
  --quality <level>            Quality: low | medium | high | auto (default: auto)
  --output-format <fmt>        Output format: png | jpeg | webp (default: png)
  --output-compression <0-100> Compression for jpeg/webp
  --n <int>                    Number of images to generate (default: 1)
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai",
#     "python-dotenv",
# ]
# ///

import argparse
import base64
import os
import sys

from openai import OpenAI


def load_api_key():
    """Resolve OPENAI_API_KEY from os.environ or the nearest .env file."""
    api_key = os.environ.get("OPENAI_API_KEY")
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
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                return api_key

    print(
        "ERROR: OPENAI_API_KEY is not set. Define it in the OS environment or a nearby .env file.",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="OpenAI image generation (text-to-image)")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("output", nargs="?", default="generated_image.png", help="Output filename")
    parser.add_argument("--model", default="gpt-image-2", help="Model ID")
    parser.add_argument(
        "--size",
        default="auto",
        help="Image size (e.g. 1024x1024, 1024x1536, 1536x1024, 2048x2048) or 'auto'",
    )
    parser.add_argument(
        "--quality",
        default="auto",
        choices=["low", "medium", "high", "auto"],
        help="Quality level",
    )
    parser.add_argument(
        "--output-format",
        default="png",
        choices=["png", "jpeg", "webp"],
        help="Output image format",
    )
    parser.add_argument(
        "--output-compression",
        type=int,
        default=None,
        help="Compression 0-100 (only used for jpeg or webp)",
    )
    parser.add_argument("--n", type=int, default=1, help="Number of images to generate")
    args = parser.parse_args()

    api_key = load_api_key()
    client = OpenAI(api_key=api_key)

    print("🎨 OpenAI — generating image...")
    print(f"   Model: {args.model}")
    print(f"   Prompt: {args.prompt}")
    print(f"   Size: {args.size}, Quality: {args.quality}, Format: {args.output_format}")

    kwargs = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": args.n,
        "output_format": args.output_format,
    }
    if args.output_compression is not None and args.output_format in ("jpeg", "webp"):
        kwargs["output_compression"] = args.output_compression

    try:
        response = client.images.generate(**kwargs)
    except Exception as e:
        print(f"❌ API error: {e}", file=sys.stderr)
        sys.exit(1)

    if not response.data:
        print("❌ Response had no data.", file=sys.stderr)
        sys.exit(1)

    saved = []
    for i, item in enumerate(response.data):
        b64 = getattr(item, "b64_json", None)
        url = getattr(item, "url", None)
        if b64:
            data = base64.b64decode(b64)
            filename = args.output
            if args.n > 1:
                base, ext = os.path.splitext(args.output)
                filename = f"{base}_{i}{ext}"
            with open(filename, "wb") as f:
                f.write(data)
            saved.append(filename)
        elif url:
            print(f"⚠️  Image returned as URL (not saved locally): {url}", file=sys.stderr)

    for path in saved:
        print(f"✅ Image saved to: {path}")

    if not saved:
        print("⚠️  No images saved.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
