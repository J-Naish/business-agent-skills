#!/usr/bin/env python3
"""
Gemini Image Generation — generate an image from a text prompt

Usage:
  python3 text_to_image.py "prompt" [output filename] [options...]

Options:
  --model <model_id>           Model ID (default: gemini-3.1-flash-image-preview)
  --aspect-ratio <ratio>       Aspect ratio (e.g. 16:9, 1:1, 9:16)
  --image-size <size>          Image size (e.g. 1K, 2K, 4K)
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


def main():
    parser = argparse.ArgumentParser(description="Gemini image generation (text-to-image)")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("output", nargs="?", default="generated_image.png", help="Output filename")
    parser.add_argument("--model", default="gemini-3.1-flash-image-preview", help="Model ID")
    parser.add_argument("--aspect-ratio", default=None, help="Aspect ratio (e.g. 16:9, 1:1, 9:16)")
    parser.add_argument("--image-size", default=None, help="Image size (e.g. 1K, 2K, 4K)")
    args = parser.parse_args()


    api_key = load_api_key()

    client = genai.Client(api_key=api_key)

    print("🍌 Nano Banana — generating image...")
    print(f"   Model: {args.model}")
    print(f"   Prompt: {args.prompt}")

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
            contents=args.prompt,
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
            print(f"\n✅ Image saved to: {args.output}")

    if not image_saved:
        print("\n⚠️  No image was generated — only text was returned.", file=sys.stderr)
        print("   Try adjusting the prompt or switching models.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
