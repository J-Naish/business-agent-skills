#!/usr/bin/env python3
"""
Gemini Image Edit — edit an existing image with a reference

Usage:
  python3 image_to_image.py "edit instruction" reference_image_path [output filename] [options...]

Options:
  --model <model_id>           Model ID (default: gemini-3.1-flash-image-preview)
  --aspect-ratio <ratio>       Aspect ratio (e.g. 16:9, 1:1, 9:16)
  --image-size <size>          Image size (e.g. 1K, 2K, 4K)
  --images <path> [<path>...]  Additional reference images beyond the primary.
                               Total references (primary + additional) cannot exceed
                               Pro: 11 (6 object + 5 character),
                               Flash: 14 (10 object + 4 character).
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

from google import genai
from google.genai import types


MIME_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
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


def load_image(path):
    """Load an image file and return it as a types.Part."""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime_type = MIME_TYPES.get(ext)
    if not mime_type:
        print(f"ERROR: unsupported image format: .{ext}", file=sys.stderr)
        print(f"  Supported formats: {', '.join(MIME_TYPES.keys())}", file=sys.stderr)
        sys.exit(1)

    with open(path, "rb") as f:
        image_data = f.read()

    return types.Part(inline_data=types.Blob(data=image_data, mime_type=mime_type)), mime_type


def main():
    parser = argparse.ArgumentParser(description="Gemini image editing (image-to-image)")
    parser.add_argument("prompt", help="Edit instruction prompt")
    parser.add_argument("image", help="Path to the reference image")
    parser.add_argument("output", nargs="?", default="edited_image.png", help="Output filename")
    parser.add_argument("--model", default="gemini-3.1-flash-image-preview", help="Model ID")
    parser.add_argument("--aspect-ratio", default=None, help="Aspect ratio (e.g. 16:9, 1:1, 9:16)")
    parser.add_argument("--image-size", default=None, help="Image size (e.g. 1K, 2K, 4K)")
    parser.add_argument("--images", nargs="+", default=[], help="Additional reference images (multiple allowed)")
    args = parser.parse_args()

    all_image_paths = [args.image] + args.images
    for img_path in all_image_paths:
        if not os.path.isfile(img_path):
            print(f"ERROR: reference image not found: {img_path}", file=sys.stderr)
            sys.exit(1)


    api_key = load_api_key()

    client = genai.Client(api_key=api_key)

    image_parts = []
    for img_path in all_image_paths:
        part, _ = load_image(img_path)
        image_parts.append(part)

    print("🍌 Nano Banana — editing image...")
    print(f"   Model: {args.model}")
    print(f"   Reference images: {', '.join(all_image_paths)} ({len(all_image_paths)} total)")
    print(f"   Edit instruction: {args.prompt}")

    image_config_kwargs = {}
    if args.aspect_ratio:
        image_config_kwargs["aspect_ratio"] = args.aspect_ratio
    if args.image_size:
        image_config_kwargs["image_size"] = args.image_size

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    )
    if image_config_kwargs:
        config.image_config = types.ImageConfig(**image_config_kwargs)

    try:
        response = client.models.generate_content(
            model=args.model,
            contents=[args.prompt] + image_parts,
            config=config,
        )
    except Exception as e:
        print(f"❌ API error: {e}", file=sys.stderr)
        sys.exit(1)

    if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
        print("❌ Response had no parts.", file=sys.stderr)
        print("   The request may have been blocked by a safety filter.", file=sys.stderr)
        sys.exit(1)

    image_saved = False
    for part in response.candidates[0].content.parts:
        if part.text:
            print(f"\n📝 Model text:")
            print(f"   {part.text}")
        elif part.inline_data:
            with open(args.output, "wb") as f:
                f.write(part.inline_data.data)
            image_saved = True
            print(f"\n✅ Edited image saved to: {args.output}")

    if not image_saved:
        print("\n⚠️  No image was returned.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
