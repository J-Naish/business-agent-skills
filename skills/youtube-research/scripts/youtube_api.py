#!/usr/bin/env python3
"""Read-only YouTube Data API helper for research workflows.

Loads API credentials from environment variables or a nearby .env file.
Credential values and request URLs containing keys are never printed.
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


API_BASE = "https://www.googleapis.com/youtube/v3"
USER_AGENT = "codex-youtube-research/1.0"
ENV_KEY = "YOUTUBE_API_KEY"

DEFAULT_VIDEO_PARTS = (
    "snippet,statistics,contentDetails,status,topicDetails,recordingDetails,"
    "liveStreamingDetails"
)
DEFAULT_CHANNEL_PARTS = "snippet,statistics,contentDetails,brandingSettings,topicDetails,status"
DEFAULT_COMMENT_THREAD_PARTS = "snippet,replies"
DEFAULT_COMMENT_PARTS = "snippet"
DEFAULT_PLAYLIST_ITEM_PARTS = "snippet,contentDetails,status"


class YouTubeApiError(Exception):
    def __init__(self, status: int | None, data: Any, headers: dict[str, str] | None = None):
        super().__init__(f"YouTube API request failed with status {status}")
        self.status = status
        self.data = data
        self.headers = headers or {}


def find_dotenv(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for path in [current, *current.parents]:
        candidate = path / ".env"
        if candidate.exists():
            return candidate
    return None


def parse_env_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export ") :].strip()
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def load_env(env_path: str | None = None) -> Path | None:
    """Load API credentials from os.environ or the nearest .env file."""
    path: Path | None = None
    if env_path:
        path = Path(env_path).expanduser()
    else:
        try:
            from dotenv import find_dotenv as dotenv_find_dotenv
            from dotenv import load_dotenv
        except ImportError:
            path = find_dotenv()
        else:
            found = dotenv_find_dotenv(usecwd=True)
            if found:
                load_dotenv(found, override=False)
                return Path(found)
            return None

    if not path or not path.exists():
        return None
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass
    else:
        load_dotenv(path, override=False)
        return path

    for raw in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_env_line(raw)
        if not parsed:
            continue
        key, value = parsed
        os.environ.setdefault(key, value)
    return path


def missing_credentials_message() -> str:
    return (
        "ERROR: Required YouTube API credential variable is not set.\n"
        f"Missing:\n  - {ENV_KEY}\n"
        "Define it in the OS environment or a nearby .env file. Do not print or commit secret values."
    )


def parse_kv(items: list[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def parse_video_ids(values: Iterable[str]) -> list[str]:
    ids: list[str] = []
    for raw in values:
        value = raw.strip()
        if not value:
            continue
        parsed = urllib.parse.urlsplit(value)
        if parsed.netloc:
            query = urllib.parse.parse_qs(parsed.query)
            if "v" in query and query["v"]:
                ids.append(query["v"][0])
                continue
            match = re.search(r"/(?:shorts|embed|live)/([^/?#]+)", parsed.path)
            if match:
                ids.append(match.group(1))
                continue
            if parsed.netloc.endswith("youtu.be"):
                candidate = parsed.path.strip("/").split("/", 1)[0]
                if candidate:
                    ids.append(candidate)
                    continue
        match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{6,})", value)
        if match:
            ids.append(match.group(1))
        else:
            ids.append(value)
    return ids


def clean_id(value: str) -> str:
    return value.strip().strip("/")


def batched(values: list[str], size: int = 50) -> Iterable[list[str]]:
    for idx in range(0, len(values), size):
        yield values[idx : idx + size]


def rate_limit_headers(headers: dict[str, str]) -> dict[str, str]:
    wanted = {
        "retry-after",
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-goog-quota-project",
    }
    return {k: v for k, v in headers.items() if k.lower() in wanted}


def sanitize_error(data: Any) -> Any:
    return data


class YouTubeApiClient:
    def __init__(self, env_path: str | None = None, base_url: str = API_BASE):
        load_env(env_path)
        self.base_url = base_url.rstrip("/")

    def require_api_key(self) -> str:
        key = os.environ.get(ENV_KEY)
        if not key:
            raise SystemExit(missing_credentials_message())
        return key

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        method = method.upper()
        if method != "GET":
            raise SystemExit("This research helper only allows GET requests.")
        key = self.require_api_key()
        params = {name: value for name, value in (params or {}).items() if value is not None}
        params.setdefault("key", key)

        if path.startswith("http://") or path.startswith("https://"):
            raw_url = path
        else:
            root = (base_url or self.base_url).rstrip("/")
            raw_url = root + (path if path.startswith("/") else "/" + path)

        parts = urllib.parse.urlsplit(raw_url)
        existing_items = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)]
        param_items = existing_items + [(str(k), str(v)) for k, v in params.items()]
        query = urllib.parse.urlencode(param_items)
        final_url = urllib.parse.urlunsplit(
            (parts.scheme, parts.netloc, parts.path, query, parts.fragment)
        )

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        req = urllib.request.Request(final_url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8", "replace")
                data = json.loads(text) if text else {}
                headers_out = {k.lower(): v for k, v in resp.headers.items()}
                return {
                    "status": resp.status,
                    "data": data,
                    "rate_limit": rate_limit_headers(headers_out),
                }
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace")
            try:
                data = json.loads(text) if text else {}
            except json.JSONDecodeError:
                data = {"raw": text[:2000]}
            headers_out = {k.lower(): v for k, v in exc.headers.items()}
            raise YouTubeApiError(exc.code, sanitize_error(data), headers_out) from exc
        except urllib.error.URLError as exc:
            raise YouTubeApiError(None, {"error": str(exc.reason)}) from exc


def paginate(
    client: YouTubeApiClient,
    path: str,
    params: dict[str, Any],
    max_pages: int,
    base_url: str | None = None,
) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    next_token: str | None = None
    for _ in range(max_pages):
        page_params = dict(params)
        if next_token:
            page_params["pageToken"] = next_token
        response = client.request("GET", path, page_params, base_url=base_url)
        pages.append(response)
        data = response.get("data", {})
        next_token = data.get("nextPageToken") if isinstance(data, dict) else None
        if not next_token:
            break
    return pages


def collect_items(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in pages:
        data = page.get("data", {})
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            items.extend(item for item in data["items"] if isinstance(item, dict))
    return items


def first_page_info(pages: list[dict[str, Any]]) -> dict[str, Any]:
    if not pages:
        return {}
    data = pages[0].get("data", {})
    if isinstance(data, dict) and isinstance(data.get("pageInfo"), dict):
        return data["pageInfo"]
    return {}


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def print_jsonl(items: Iterable[Any]) -> None:
    for item in items:
        print(json.dumps(item, ensure_ascii=False, sort_keys=False))


def client_from_args(args: argparse.Namespace) -> YouTubeApiClient:
    return YouTubeApiClient(env_path=getattr(args, "env", None), base_url=getattr(args, "base_url", API_BASE))


def fetch_videos(
    client: YouTubeApiClient,
    video_ids: list[str],
    part: str = DEFAULT_VIDEO_PARTS,
) -> list[dict[str, Any]]:
    videos: list[dict[str, Any]] = []
    for chunk in batched(video_ids, 50):
        response = client.request("GET", "/videos", {"part": part, "id": ",".join(chunk)})
        data = response.get("data", {})
        videos.extend(data.get("items", []) if isinstance(data, dict) else [])
    return videos


def fetch_channels(
    client: YouTubeApiClient,
    channel_ids: list[str],
    part: str = DEFAULT_CHANNEL_PARTS,
) -> list[dict[str, Any]]:
    channels: list[dict[str, Any]] = []
    for chunk in batched(channel_ids, 50):
        response = client.request("GET", "/channels", {"part": part, "id": ",".join(chunk)})
        data = response.get("data", {})
        channels.extend(data.get("items", []) if isinstance(data, dict) else [])
    return channels


def item_id(item: dict[str, Any]) -> str | None:
    value = item.get("id")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("videoId", "channelId", "playlistId"):
            if value.get(key):
                return value[key]
    return None


def command_check_auth(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    try:
        response = client.request(
            "GET",
            "/videos",
            {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": args.region,
                "maxResults": 1,
            },
        )
        items = response.get("data", {}).get("items", [])
        sample = None
        if items:
            snippet = items[0].get("snippet") or {}
            statistics = items[0].get("statistics") or {}
            sample = {
                "id": items[0].get("id"),
                "title": snippet.get("title"),
                "channelTitle": snippet.get("channelTitle"),
                "viewCount": statistics.get("viewCount"),
            }
        print_json(
            {
                "checks": [
                    {
                        "auth": "api_key",
                        "endpoint": "/youtube/v3/videos",
                        "ok": True,
                        "status": response["status"],
                        "region": args.region,
                        "items": len(items),
                        "sample": sample,
                    }
                ]
            }
        )
    except YouTubeApiError as exc:
        print_json(
            {
                "checks": [
                    {
                        "auth": "api_key",
                        "endpoint": "/youtube/v3/videos",
                        "ok": False,
                        "status": exc.status,
                        "error": exc.data,
                    }
                ]
            }
        )


def command_request(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = parse_kv(args.param)
    if args.paginate:
        pages = paginate(client, args.path, params, args.max_pages, base_url=args.base_url)
        if args.jsonl:
            print_jsonl(collect_items(pages))
        else:
            print_json({"endpoint": args.path, "pages": pages})
        return
    response = client.request("GET", args.path, params, base_url=args.base_url)
    print_json(response if args.include_status else response["data"])


def command_search(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params: dict[str, Any] = {
        "part": "snippet",
        "q": args.query,
        "type": args.type,
        "maxResults": args.max_results,
        "order": args.order,
        "publishedAfter": args.published_after,
        "publishedBefore": args.published_before,
        "regionCode": args.region_code,
        "relevanceLanguage": args.relevance_language,
        "channelId": args.channel_id,
        "safeSearch": args.safe_search,
        "videoDuration": args.video_duration,
        "videoDefinition": args.video_definition,
        "videoCategoryId": args.video_category_id,
        "eventType": args.event_type,
        "topicId": args.topic_id,
        "location": args.location,
        "locationRadius": args.location_radius,
    }
    params.update(parse_kv(args.param))
    pages = paginate(client, "/search", params, args.max_pages)
    if args.jsonl:
        print_jsonl(collect_items(pages))
    else:
        print_json(
            {
                "endpoint": "/youtube/v3/search",
                "query": args.query,
                "pageInfo": first_page_info(pages),
                "pages": pages,
            }
        )


def command_videos(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    ids = parse_video_ids(args.values)
    if not ids:
        raise SystemExit("Provide at least one video ID or URL.")
    videos = fetch_videos(client, ids, part=args.part)
    if args.jsonl:
        print_jsonl(videos)
    else:
        print_json({"endpoint": "/youtube/v3/videos", "ids": ids, "items": videos})


def resolve_channel_request(value: str, by: str) -> tuple[str, dict[str, Any]]:
    value = clean_id(value)
    if by == "id" or value.startswith("UC"):
        return "/channels", {"part": DEFAULT_CHANNEL_PARTS, "id": value}
    if by == "handle" or value.startswith("@"):
        return "/channels", {"part": DEFAULT_CHANNEL_PARTS, "forHandle": value if value.startswith("@") else "@" + value}
    if by in {"auto", "username"}:
        return "/channels", {"part": DEFAULT_CHANNEL_PARTS, "forUsername": value}
    raise SystemExit(f"Unknown channel lookup mode: {by}")


def command_channels(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    items: list[dict[str, Any]] = []
    for value in args.values:
        path, params = resolve_channel_request(value, args.by)
        response = client.request("GET", path, params)
        data = response.get("data", {})
        found = data.get("items", []) if isinstance(data, dict) else []
        if not found and args.fallback_search:
            search = client.request(
                "GET",
                "/search",
                {"part": "snippet", "q": value, "type": "channel", "maxResults": 1},
            )
            search_items = search.get("data", {}).get("items", [])
            channel_id = item_id(search_items[0]) if search_items else None
            if channel_id:
                response = client.request("GET", "/channels", {"part": DEFAULT_CHANNEL_PARTS, "id": channel_id})
                found = response.get("data", {}).get("items", [])
        items.extend(found)
    if args.jsonl:
        print_jsonl(items)
    else:
        print_json({"endpoint": "/youtube/v3/channels", "items": items})


def command_popular(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = {
        "part": args.part,
        "chart": "mostPopular",
        "regionCode": args.region_code,
        "videoCategoryId": args.video_category_id,
        "maxResults": args.max_results,
        "pageToken": args.page_token,
    }
    response = client.request("GET", "/videos", params)
    print_json(response if args.include_status else response["data"])


def command_comment_threads(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    ids = parse_video_ids([args.video])
    if not ids:
        raise SystemExit("Provide a video ID or URL.")
    params = {
        "part": args.part,
        "videoId": ids[0],
        "maxResults": args.max_results,
        "order": args.order,
        "textFormat": args.text_format,
    }
    params.update(parse_kv(args.param))
    pages = paginate(client, "/commentThreads", params, args.max_pages)
    if args.jsonl:
        print_jsonl(collect_items(pages))
    else:
        print_json({"endpoint": "/youtube/v3/commentThreads", "videoId": ids[0], "pages": pages})


def command_comments(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = {
        "part": args.part,
        "parentId": args.parent_id,
        "maxResults": args.max_results,
        "textFormat": args.text_format,
    }
    params.update(parse_kv(args.param))
    pages = paginate(client, "/comments", params, args.max_pages)
    if args.jsonl:
        print_jsonl(collect_items(pages))
    else:
        print_json({"endpoint": "/youtube/v3/comments", "parentId": args.parent_id, "pages": pages})


def command_playlist_items(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = {
        "part": args.part,
        "playlistId": args.playlist_id,
        "maxResults": args.max_results,
    }
    params.update(parse_kv(args.param))
    pages = paginate(client, "/playlistItems", params, args.max_pages)
    if args.jsonl:
        print_jsonl(collect_items(pages))
    else:
        print_json({"endpoint": "/youtube/v3/playlistItems", "playlistId": args.playlist_id, "pages": pages})


def command_video_categories(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = {"part": "snippet", "regionCode": args.region_code, "hl": args.hl}
    response = client.request("GET", "/videoCategories", params)
    print_json(response if args.include_status else response["data"])


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument("--include-status", action="store_true", help="Include HTTP status metadata in output.")


def add_param_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--param", action="append", help="Extra query parameter as KEY=VALUE. May be repeated.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only YouTube Data API research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check API key with a minimal public request.")
    p.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    p.add_argument("--region", default="JP")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("request", help="Call any read-only YouTube Data API GET endpoint.")
    add_common(p)
    p.add_argument("method", choices=["GET"])
    p.add_argument("path", help="Endpoint path such as /search or full URL.")
    add_param_options(p)
    p.add_argument("--base-url", default=API_BASE)
    p.add_argument("--paginate", action="store_true")
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--jsonl", action="store_true", help="Print page items as JSONL.")
    p.set_defaults(func=command_request)

    p = sub.add_parser("search", help="Search videos, channels, or playlists.")
    add_common(p)
    p.add_argument("query")
    p.add_argument("--type", choices=["video", "channel", "playlist"], default="video")
    p.add_argument("--order", choices=["date", "rating", "relevance", "title", "videoCount", "viewCount"], default="relevance")
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--published-after")
    p.add_argument("--published-before")
    p.add_argument("--region-code")
    p.add_argument("--relevance-language")
    p.add_argument("--channel-id")
    p.add_argument("--safe-search", choices=["moderate", "none", "strict"], default=None)
    p.add_argument("--video-duration", choices=["any", "short", "medium", "long"])
    p.add_argument("--video-definition", choices=["any", "high", "standard"])
    p.add_argument("--video-category-id")
    p.add_argument("--event-type", choices=["completed", "live", "upcoming"])
    p.add_argument("--topic-id")
    p.add_argument("--location")
    p.add_argument("--location-radius")
    p.add_argument("--jsonl", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_search)

    p = sub.add_parser("videos", help="Look up videos by ID or URL.")
    add_common(p)
    p.add_argument("values", nargs="+")
    p.add_argument("--part", default=DEFAULT_VIDEO_PARTS)
    p.add_argument("--jsonl", action="store_true")
    p.set_defaults(func=command_videos)

    p = sub.add_parser("channels", help="Look up channels by ID, handle, or username.")
    add_common(p)
    p.add_argument("values", nargs="+")
    p.add_argument("--by", choices=["auto", "id", "handle", "username"], default="auto")
    p.add_argument("--fallback-search", action="store_true", default=True)
    p.add_argument("--jsonl", action="store_true")
    p.set_defaults(func=command_channels)

    p = sub.add_parser("popular", help="Fetch most popular videos for a region/category.")
    add_common(p)
    p.add_argument("--part", default=DEFAULT_VIDEO_PARTS)
    p.add_argument("--region-code", default="JP")
    p.add_argument("--video-category-id")
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--page-token")
    p.set_defaults(func=command_popular)

    p = sub.add_parser("comment-threads", help="Fetch comment threads for a video.")
    add_common(p)
    p.add_argument("video", help="Video ID or URL.")
    p.add_argument("--part", default=DEFAULT_COMMENT_THREAD_PARTS)
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--order", choices=["time", "relevance"], default="relevance")
    p.add_argument("--text-format", choices=["html", "plainText"], default="plainText")
    p.add_argument("--jsonl", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_comment_threads)

    p = sub.add_parser("comments", help="Fetch replies for a parent comment.")
    add_common(p)
    p.add_argument("parent_id")
    p.add_argument("--part", default=DEFAULT_COMMENT_PARTS)
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--text-format", choices=["html", "plainText"], default="plainText")
    p.add_argument("--jsonl", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_comments)

    p = sub.add_parser("playlist-items", help="Fetch items from a playlist.")
    add_common(p)
    p.add_argument("playlist_id")
    p.add_argument("--part", default=DEFAULT_PLAYLIST_ITEM_PARTS)
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--jsonl", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_playlist_items)

    p = sub.add_parser("video-categories", help="Fetch video category names for a region.")
    add_common(p)
    p.add_argument("--region-code", default="JP")
    p.add_argument("--hl")
    p.set_defaults(func=command_video_categories)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except YouTubeApiError as exc:
        print_json(
            {
                "ok": False,
                "status": exc.status,
                "error": exc.data,
                "rate_limit": rate_limit_headers(exc.headers),
            }
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
