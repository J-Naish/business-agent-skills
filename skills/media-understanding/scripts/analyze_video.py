#!/usr/bin/env python3
"""
Gemini Video Understanding — analyze a local video file.

Usage:
  python3 analyze_video.py "prompt" video_file_path [options...]

Options:
  --model <model_id>         Model ID (default: gemini-3-flash-preview)
  --json                     Structured JSON output (uses response_mime_type=application/json)
  --schema <json|file>       JSON schema (inline JSON string or .json file path; auto-enables --json)
  --fps <number>             Frame sampling rate (default: 1 fps)
  --start <seconds>          Clip start offset (seconds)
  --end <seconds>            Clip end offset (seconds)
  --media-resolution <res>   Media resolution (low, medium, high)
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai",
#     "python-dotenv",
# ]
# ///

import argparse
import json
import mimetypes
import os
import sys
import time

from google import genai
from google.genai import types


SUPPORTED_MIME_TYPES = {
    "video/mp4", "video/mpeg", "video/mov", "video/avi",
    "video/x-flv", "video/mpg", "video/webm", "video/wmv",
    "video/3gpp", "video/quicktime",
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


def get_mime_type(file_path: str) -> str:
    """Infer the MIME type for the given video file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type in SUPPORTED_MIME_TYPES:
        return mime_type
    ext = os.path.splitext(file_path)[1].lower()
    ext_map = {
        ".mp4": "video/mp4", ".mpeg": "video/mpeg", ".mpg": "video/mpg",
        ".mov": "video/quicktime", ".avi": "video/avi", ".flv": "video/x-flv",
        ".webm": "video/webm", ".wmv": "video/wmv", ".3gp": "video/3gpp",
    }
    return ext_map.get(ext, "video/mp4")


def get_file_size_mb(file_path: str) -> float:
    return os.path.getsize(file_path) / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description="Gemini video understanding")
    parser.add_argument("prompt", help="Question or instruction about the video")
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Model ID")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Structured JSON output (uses API response_mime_type)")
    parser.add_argument("--schema", default=None,
                        help="JSON schema (inline JSON string or .json file path; auto-enables --json)")
    parser.add_argument("--fps", type=float, default=None, help="Frame sampling rate (default: 1 fps)")
    parser.add_argument("--start", type=float, default=None, help="Clip start offset (seconds)")
    parser.add_argument("--end", type=float, default=None, help="Clip end offset (seconds)")
    parser.add_argument("--media-resolution", default=None, choices=["low", "medium", "high"],
                        help="Media resolution (low/medium/high) — affects token usage")
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        print(f"ERROR: file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    api_key = load_api_key()

    client = genai.Client(api_key=api_key)
    file_size_mb = get_file_size_mb(args.video)
    mime_type = get_mime_type(args.video)

    print(f"🎥 Gemini Video Understanding")
    print(f"   Model: {args.model}")
    print(f"   File: {args.video} ({file_size_mb:.1f} MB)")
    print(f"   MIME: {mime_type}")

    # The Gemini API recommends the Files API when total request size exceeds
    # 20 MB, video duration is significant, or the same video will be reused.
    use_file_api = file_size_mb > 20

    if use_file_api:
        print(f"\n📤 Uploading via Files API ({file_size_mb:.1f} MB)...")
        uploaded_file = client.files.upload(file=args.video)

        while uploaded_file.state.name == "PROCESSING":
            time.sleep(5)
            uploaded_file = client.files.get(name=uploaded_file.name)
            print(".", end="", flush=True)
        print()

        if uploaded_file.state.name == "FAILED":
            print(f"❌ Upload failed: {uploaded_file.state}", file=sys.stderr)
            sys.exit(1)

        print(f"   Upload complete: {uploaded_file.name}")
        video_part = types.Part(file_data=types.FileData(
            file_uri=uploaded_file.uri,
            mime_type=mime_type,
        ))
    else:
        print(f"\n📦 Sending as inline data...")
        video_bytes = open(args.video, "rb").read()
        video_part = types.Part(
            inline_data=types.Blob(data=video_bytes, mime_type=mime_type)
        )

    # VideoMetadata: fps, start/end clipping
    video_metadata_kwargs = {}
    if args.fps is not None:
        video_metadata_kwargs["fps"] = args.fps
    if args.start is not None:
        video_metadata_kwargs["start_offset"] = f"{args.start}s"
    if args.end is not None:
        video_metadata_kwargs["end_offset"] = f"{args.end}s"

    if video_metadata_kwargs:
        video_part.video_metadata = types.VideoMetadata(**video_metadata_kwargs)

    # --schema implies --json
    if args.schema:
        args.json_output = True

    # Load JSON schema (file or inline)
    json_schema = None
    if args.schema:
        schema_str = args.schema
        if os.path.isfile(schema_str):
            with open(schema_str, "r", encoding="utf-8") as f:
                json_schema = json.load(f)
            print(f"   Schema: {schema_str} (file)")
        else:
            json_schema = json.loads(schema_str)
            print(f"   Schema: inline")

    # Build GenerateContentConfig
    config_kwargs = {}
    if args.media_resolution:
        resolution_map = {
            "low": "MEDIA_RESOLUTION_LOW",
            "medium": "MEDIA_RESOLUTION_MEDIUM",
            "high": "MEDIA_RESOLUTION_HIGH",
        }
        config_kwargs["media_resolution"] = resolution_map[args.media_resolution]

    if args.json_output:
        config_kwargs["response_mime_type"] = "application/json"
    if json_schema:
        config_kwargs["response_json_schema"] = json_schema

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    prompt = args.prompt

    print(f"\n🔍 Analyzing...")

    try:
        response = client.models.generate_content(
            model=args.model,
            contents=types.Content(
                parts=[video_part, types.Part(text=prompt)]
            ),
            config=config,
        )
    except Exception as e:
        print(f"❌ API error: {e}", file=sys.stderr)
        sys.exit(1)

    if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
        print("❌ Response was empty.", file=sys.stderr)
        if response.prompt_feedback:
            print(f"   Feedback: {response.prompt_feedback}", file=sys.stderr)
        sys.exit(1)

    result_text = ""
    for part in response.candidates[0].content.parts:
        if part.text:
            result_text += part.text

    if args.json_output:
        try:
            parsed = json.loads(result_text)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(result_text)
    else:
        print(f"\n📋 Result:\n")
        print(result_text)

    # Clean up Files API uploads
    if use_file_api:
        try:
            client.files.delete(name=uploaded_file.name)
            print(f"\n🗑️  Deleted uploaded file")
        except Exception:
            pass

    print(f"\n✅ Done")


if __name__ == "__main__":
    main()
