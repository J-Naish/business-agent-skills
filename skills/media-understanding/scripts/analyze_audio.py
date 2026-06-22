#!/usr/bin/env python3
"""
Gemini Audio Understanding — analyze a local audio file.

Usage:
  python3 analyze_audio.py "prompt" audio_file_path [options...]

Options:
  --model <model_id>         Model ID (default: gemini-3-flash-preview)
  --json                     Structured JSON output (uses response_mime_type=application/json)
  --schema <json|file>       JSON schema (inline JSON string or .json file path; auto-enables --json)
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
    "audio/mp3", "audio/mpeg", "audio/wav", "audio/x-wav",
    "audio/aac", "audio/ogg", "audio/flac", "audio/aiff", "audio/x-aiff",
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
    """Infer the MIME type for the given audio file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type in SUPPORTED_MIME_TYPES:
        # Gemini expects audio/mp3 (not audio/mpeg) and audio/wav (not audio/x-wav)
        if mime_type == "audio/mpeg":
            return "audio/mp3"
        if mime_type == "audio/x-wav":
            return "audio/wav"
        if mime_type == "audio/x-aiff":
            return "audio/aiff"
        return mime_type
    ext = os.path.splitext(file_path)[1].lower()
    ext_map = {
        ".mp3": "audio/mp3", ".wav": "audio/wav", ".aac": "audio/aac",
        ".ogg": "audio/ogg", ".flac": "audio/flac", ".aiff": "audio/aiff",
        ".aif": "audio/aiff", ".m4a": "audio/aac",
    }
    return ext_map.get(ext, "audio/mp3")


def get_file_size_mb(file_path: str) -> float:
    return os.path.getsize(file_path) / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description="Gemini audio understanding")
    parser.add_argument("prompt", help="Question or instruction about the audio")
    parser.add_argument("audio", help="Path to the audio file")
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Model ID")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Structured JSON output (uses API response_mime_type)")
    parser.add_argument("--schema", default=None,
                        help="JSON schema (inline JSON string or .json file path; auto-enables --json)")
    args = parser.parse_args()

    if not os.path.isfile(args.audio):
        print(f"ERROR: file not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    api_key = load_api_key()

    client = genai.Client(api_key=api_key)
    file_size_mb = get_file_size_mb(args.audio)
    mime_type = get_mime_type(args.audio)

    print(f"🎙  Gemini Audio Understanding")
    print(f"   Model: {args.model}")
    print(f"   File: {args.audio} ({file_size_mb:.1f} MB)")
    print(f"   MIME: {mime_type}")

    # Files >20MB go through the Files API (the inline limit comes from the
    # 20 MB total request-size cap); smaller files are sent inline.
    use_file_api = file_size_mb > 20

    if use_file_api:
        print(f"\n📤 Uploading via Files API ({file_size_mb:.1f} MB)...")
        uploaded_file = client.files.upload(file=args.audio)

        while uploaded_file.state.name == "PROCESSING":
            time.sleep(5)
            uploaded_file = client.files.get(name=uploaded_file.name)
            print(".", end="", flush=True)
        print()

        if uploaded_file.state.name == "FAILED":
            print(f"❌ Upload failed: {uploaded_file.state}", file=sys.stderr)
            sys.exit(1)

        print(f"   Upload complete: {uploaded_file.name}")
        audio_part = types.Part(file_data=types.FileData(
            file_uri=uploaded_file.uri,
            mime_type=mime_type,
        ))
    else:
        print(f"\n📦 Sending as inline data...")
        audio_bytes = open(args.audio, "rb").read()
        audio_part = types.Part(
            inline_data=types.Blob(data=audio_bytes, mime_type=mime_type)
        )

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
                parts=[audio_part, types.Part(text=prompt)]
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
