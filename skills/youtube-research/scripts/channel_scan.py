#!/usr/bin/env python3
"""Channel, creator, or competitor research using YouTube Data API endpoints."""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from trend_scan import analyze_videos, channel_url, clean_text, fetch_video_categories, search_video_ids  # noqa: E402
from youtube_api import (  # noqa: E402
    DEFAULT_CHANNEL_PARTS,
    DEFAULT_VIDEO_PARTS,
    YouTubeApiClient,
    YouTubeApiError,
    collect_items,
    fetch_videos,
    first_page_info,
    item_id,
    paginate,
    parse_kv,
)


def first_channel(response: dict[str, Any]) -> dict[str, Any] | None:
    data = response.get("data", {})
    items = data.get("items", []) if isinstance(data, dict) else []
    if items and isinstance(items[0], dict):
        return items[0]
    return None


def lookup_channel(client: YouTubeApiClient, value: str, is_id: bool) -> tuple[dict[str, Any], str, str]:
    raw = value.strip()
    candidates: list[tuple[str, dict[str, Any], str]] = []
    if is_id or raw.startswith("UC"):
        candidates.append(("/channels", {"part": DEFAULT_CHANNEL_PARTS, "id": raw}, "id"))
    elif raw.startswith("@"):
        candidates.append(("/channels", {"part": DEFAULT_CHANNEL_PARTS, "forHandle": raw}, "handle"))
    else:
        candidates.append(("/channels", {"part": DEFAULT_CHANNEL_PARTS, "forUsername": raw}, "username"))
        candidates.append(("/channels", {"part": DEFAULT_CHANNEL_PARTS, "forHandle": "@" + raw}, "handle"))

    for endpoint, params, mode in candidates:
        response = client.request("GET", endpoint, params)
        channel = first_channel(response)
        if channel:
            return channel, endpoint, mode

    search = client.request(
        "GET",
        "/search",
        {"part": "snippet", "q": raw, "type": "channel", "maxResults": 1},
    )
    search_items = collect_items([search])
    channel_id = item_id(search_items[0]) if search_items else None
    if channel_id:
        response = client.request("GET", "/channels", {"part": DEFAULT_CHANNEL_PARTS, "id": channel_id})
        channel = first_channel(response)
        if channel:
            return channel, "/search -> /channels", "search"
    raise SystemExit(f"Could not resolve YouTube channel: {value}")


def uploads_playlist_id(channel: dict[str, Any]) -> str | None:
    content = channel.get("contentDetails") or {}
    related = content.get("relatedPlaylists") or {}
    return related.get("uploads")


def fetch_upload_video_ids(client: YouTubeApiClient, playlist_id: str, args: argparse.Namespace) -> tuple[list[str], list[dict[str, Any]]]:
    max_pages = args.max_pages or max(1, math.ceil(args.max_videos / args.max_results))
    pages = paginate(
        client,
        "/playlistItems",
        {
            "part": "snippet,contentDetails,status",
            "playlistId": playlist_id,
            "maxResults": args.max_results,
        },
        max_pages=max_pages,
    )
    ids: list[str] = []
    for item in collect_items(pages):
        content = item.get("contentDetails") or {}
        snippet = item.get("snippet") or {}
        video_id = content.get("videoId") or ((snippet.get("resourceId") or {}).get("videoId"))
        if video_id:
            ids.append(video_id)
    return ids[: args.max_videos], pages


def fetch_channel_search_video_ids(client: YouTubeApiClient, channel_id: str, args: argparse.Namespace) -> tuple[list[str], list[dict[str, Any]]]:
    max_pages = args.max_pages or max(1, math.ceil(args.max_videos / args.max_results))
    params: dict[str, Any] = {
        "part": "snippet",
        "type": "video",
        "channelId": channel_id,
        "q": args.query,
        "order": args.order,
        "maxResults": args.max_results,
        "publishedAfter": args.published_after,
        "publishedBefore": args.published_before,
        "safeSearch": args.safe_search,
    }
    params.update(parse_kv(args.param))
    pages = paginate(client, "/search", params, max_pages=max_pages)
    return search_video_ids(collect_items(pages))[: args.max_videos], pages


def metric_line(metrics: dict[str, Any]) -> str:
    if not metrics:
        return "No public metrics returned"
    keys = ["subscriberCount", "viewCount", "videoCount", "hiddenSubscriberCount"]
    return ", ".join(f"{key} {metrics[key]}" for key in keys if key in metrics)


def render_recent_videos(analysis: dict[str, Any], limit: int = 8) -> list[str]:
    lines = ["## Recent Video Sample"]
    lines.append(f"- Sample size: {analysis['sample_size']} videos")
    lines.append(f"- Views in sample: {analysis['total_views_in_sample']}")
    lines.append(f"- Likes in sample: {analysis['total_likes_in_sample']}")
    lines.append(f"- Comments in sample: {analysis['total_comments_in_sample']}")
    lines.append("")

    for key, title in [
        ("categories", "Top Categories"),
        ("tags", "Top Tags"),
        ("hashtags", "Top Hashtags"),
        ("duration_buckets", "Duration Buckets"),
        ("published_days", "Published Days"),
    ]:
        lines.append(f"### {title}")
        items = analysis.get(key) or []
        if items:
            for item, count in items[:8]:
                lines.append(f"- {item}: {count}")
        else:
            lines.append("- None found in sample.")
        lines.append("")

    lines.append("### Representative Videos")
    if analysis["representative_videos"]:
        for idx, video in enumerate(analysis["representative_videos"][:limit], 1):
            stats = video.get("statistics") or {}
            lines.append(
                f"{idx}. {video.get('title')} ({video.get('publishedAt')}) "
                f"views {stats.get('viewCount', 'n/a')} likes {stats.get('likeCount', 'n/a')} "
                f"comments {stats.get('commentCount', 'n/a')} [{video.get('url')}]"
            )
            lines.append(f"   Duration: {video.get('durationText')} | Category: {video.get('category')}")
    else:
        lines.append("- No videos returned.")
    return lines


def run(args: argparse.Namespace) -> dict[str, Any]:
    client = YouTubeApiClient(env_path=args.env)
    channel, lookup_endpoint, lookup_mode = lookup_channel(client, args.channel, args.id)
    channel_id = channel["id"]
    errors: list[str] = []

    use_search = bool(args.query or args.published_after or args.published_before or args.use_search)
    source_endpoint = "/youtube/v3/search" if use_search else "/youtube/v3/playlistItems"
    pages: list[dict[str, Any]] = []
    video_ids: list[str] = []

    if use_search:
        video_ids, pages = fetch_channel_search_video_ids(client, channel_id, args)
    else:
        playlist_id = uploads_playlist_id(channel)
        if playlist_id:
            video_ids, pages = fetch_upload_video_ids(client, playlist_id, args)
        else:
            errors.append("uploads playlist was unavailable; falling back to channel search")
            video_ids, pages = fetch_channel_search_video_ids(client, channel_id, args)
            source_endpoint = "/youtube/v3/search"

    videos = fetch_videos(client, video_ids, part=DEFAULT_VIDEO_PARTS) if video_ids else []
    channels = {channel_id: channel}
    categories = {} if args.skip_categories else fetch_video_categories(client, args.region_code, args.hl)
    analysis = analyze_videos(videos, channels, categories)

    return {
        "channel": channel,
        "lookup_endpoint": lookup_endpoint,
        "lookup_mode": lookup_mode,
        "source_endpoint": source_endpoint,
        "video_endpoint": "/youtube/v3/videos",
        "page_info": first_page_info(pages),
        "video_ids": video_ids,
        "analysis": analysis,
        "filters": {
            "query": args.query,
            "order": args.order,
            "publishedAfter": args.published_after,
            "publishedBefore": args.published_before,
            "maxVideos": args.max_videos,
            "maxPages": args.max_pages,
            "regionCode": args.region_code,
        },
        "errors": errors,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    channel = summary["channel"]
    snippet = channel.get("snippet") or {}
    stats = channel.get("statistics") or {}
    branding = channel.get("brandingSettings") or {}
    channel_branding = branding.get("channel") or {}

    lines: list[str] = []
    lines.append("# YouTube Channel Scan")
    lines.append("")
    lines.append(f"- Channel: {snippet.get('title')} ({channel.get('id')})")
    lines.append(f"- URL: {channel_url(channel.get('id'))}")
    if snippet.get("customUrl"):
        lines.append(f"- Custom URL: {snippet.get('customUrl')}")
    if snippet.get("publishedAt"):
        lines.append(f"- Created: {snippet.get('publishedAt')}")
    if snippet.get("country"):
        lines.append(f"- Country: {snippet.get('country')}")
    lines.append(f"- Public metrics: {metric_line(stats)}")
    if channel_branding.get("keywords"):
        lines.append(f"- Branding keywords: {clean_text(channel_branding['keywords'], 300)}")
    if snippet.get("description"):
        lines.append(f"- Description: {clean_text(snippet['description'], 360)}")
    lines.append("")
    lines.append(f"- Lookup endpoint: `{summary['lookup_endpoint']}` ({summary['lookup_mode']})")
    lines.append(f"- Source endpoint: `{summary['source_endpoint']}`")
    lines.append(f"- Video details endpoint: `{summary['video_endpoint']}`")
    filters = {key: value for key, value in summary.get("filters", {}).items() if value}
    if filters:
        lines.append(f"- Filters: {filters}")
    page_info = summary.get("page_info") or {}
    if page_info:
        lines.append(f"- Page info: {page_info}")
    lines.append("")

    lines.extend(render_recent_videos(summary["analysis"]))

    if summary.get("errors"):
        lines.append("")
        lines.append("## API Notes")
        for error in summary["errors"]:
            lines.append(f"- {error}")

    lines.append("")
    lines.append("## Caveats")
    lines.append("- Channel metrics and video metrics are point-in-time snapshots.")
    lines.append("- Recent upload samples are bounded by the requested page count and max video count.")
    lines.append("- Hidden subscriber counts, private videos, deleted videos, or unavailable uploads may be absent.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a YouTube channel and recent uploads.")
    parser.add_argument("channel", help="Channel ID, @handle, legacy username, or search text.")
    parser.add_argument("--id", action="store_true", help="Treat channel argument as a channel ID.")
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument("--max-videos", type=int, default=25)
    parser.add_argument("--max-results", type=int, default=25, help="Items per page, 1-50.")
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--use-search", action="store_true", help="Use search.list instead of uploads playlist.")
    parser.add_argument("--query", help="Optional query within the channel; uses search.list.")
    parser.add_argument("--order", choices=["date", "rating", "relevance", "title", "videoCount", "viewCount"], default="date")
    parser.add_argument("--published-after")
    parser.add_argument("--published-before")
    parser.add_argument("--region-code", default="US", help="Region used for category names.")
    parser.add_argument("--hl", help="Language for category names.")
    parser.add_argument("--skip-categories", action="store_true")
    parser.add_argument("--safe-search", choices=["moderate", "none", "strict"])
    parser.add_argument("--param", action="append", help="Extra search parameter as KEY=VALUE.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary instead of Markdown.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run(args)
    except YouTubeApiError as exc:
        print(
            json.dumps(
                {"ok": False, "status": exc.status, "error": exc.data},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
