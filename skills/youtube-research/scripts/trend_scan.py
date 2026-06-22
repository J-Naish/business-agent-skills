#!/usr/bin/env python3
"""Topic/query research for YouTube using search results plus video details."""
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
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from youtube_api import (  # noqa: E402
    DEFAULT_CHANNEL_PARTS,
    DEFAULT_VIDEO_PARTS,
    YouTubeApiClient,
    YouTubeApiError,
    collect_items,
    fetch_channels,
    fetch_videos,
    first_page_info,
    paginate,
    parse_kv,
)


def to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def clean_text(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def parse_iso8601_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?",
        value,
    )
    if not match:
        return None
    parts = {key: int(val or 0) for key, val in match.groupdict().items()}
    return parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def duration_bucket(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    if seconds <= 60:
        return "shorts_or_under_60s"
    if seconds <= 4 * 60:
        return "1_to_4_min"
    if seconds <= 20 * 60:
        return "4_to_20_min"
    return "over_20_min"


def video_url(video_id: str | None) -> str | None:
    if not video_id:
        return None
    return f"https://www.youtube.com/watch?v={video_id}"


def channel_url(channel_id: str | None) -> str | None:
    if not channel_id:
        return None
    return f"https://www.youtube.com/channel/{channel_id}"


def domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception:
        return ""
    return parsed.netloc.lower().removeprefix("www.")


def extract_domains(text: str) -> list[str]:
    domains: list[str] = []
    for match in re.findall(r"https?://[^\s)>\]]+", text):
        domain = domain_from_url(match)
        if domain:
            domains.append(domain)
    return domains


def extract_hashtags(text: str) -> list[str]:
    return [tag.lower() for tag in re.findall(r"(?<!\w)#([\w\-]+)", text, flags=re.UNICODE)]


def video_metric(video: dict[str, Any], key: str) -> int:
    return to_int((video.get("statistics") or {}).get(key))


def engagement(video: dict[str, Any]) -> int:
    return sum(video_metric(video, key) for key in ("viewCount", "likeCount", "commentCount"))


def search_video_ids(search_items: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for item in search_items:
        raw = item.get("id")
        if isinstance(raw, dict) and raw.get("videoId"):
            ids.append(raw["videoId"])
    return ids


def fetch_video_categories(client: YouTubeApiClient, region_code: str | None, hl: str | None = None) -> dict[str, str]:
    params = {"part": "snippet", "regionCode": region_code or "US", "hl": hl}
    try:
        response = client.request("GET", "/videoCategories", params)
    except YouTubeApiError:
        return {}
    data = response.get("data", {})
    categories: dict[str, str] = {}
    for item in data.get("items", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and item.get("id"):
            categories[item["id"]] = (item.get("snippet") or {}).get("title") or item["id"]
    return categories


def analyze_videos(
    videos: list[dict[str, Any]],
    channels: dict[str, dict[str, Any]] | None = None,
    categories: dict[str, str] | None = None,
) -> dict[str, Any]:
    channels = channels or {}
    categories = categories or {}
    channel_counts: Counter[str] = Counter()
    channel_views: defaultdict[str, int] = defaultdict(int)
    channel_likes: defaultdict[str, int] = defaultdict(int)
    channel_comments: defaultdict[str, int] = defaultdict(int)
    category_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    hashtag_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    duration_counts: Counter[str] = Counter()
    published_days: Counter[str] = Counter()

    total_views = 0
    total_likes = 0
    total_comments = 0

    for video in videos:
        snippet = video.get("snippet") or {}
        content = video.get("contentDetails") or {}
        video_id = video.get("id")
        channel_id = snippet.get("channelId") or "unknown"
        channel_counts.update([channel_id])

        views = video_metric(video, "viewCount")
        likes = video_metric(video, "likeCount")
        comments = video_metric(video, "commentCount")
        total_views += views
        total_likes += likes
        total_comments += comments
        channel_views[channel_id] += views
        channel_likes[channel_id] += likes
        channel_comments[channel_id] += comments

        category_id = snippet.get("categoryId") or "unknown"
        category_counts.update([categories.get(category_id, category_id)])

        text_blob = " ".join([snippet.get("title") or "", snippet.get("description") or ""])
        hashtag_counts.update(extract_hashtags(text_blob))
        domain_counts.update(extract_domains(text_blob))

        for tag in snippet.get("tags", []) if isinstance(snippet.get("tags"), list) else []:
            tag_counts.update([str(tag).lower()])

        language = snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage") or "unknown"
        language_counts.update([language])

        seconds = parse_iso8601_duration(content.get("duration"))
        duration_counts.update([duration_bucket(seconds)])

        published_at = snippet.get("publishedAt")
        if published_at:
            published_days.update([published_at[:10]])

    top_channels = []
    for channel_id, count in channel_counts.most_common(20):
        channel = channels.get(channel_id) or {}
        snippet = channel.get("snippet") or {}
        stats = channel.get("statistics") or {}
        top_channels.append(
            {
                "id": channel_id,
                "title": snippet.get("title") or channel_id,
                "url": channel_url(channel_id if channel_id != "unknown" else None),
                "videos_in_sample": count,
                "sample_views": channel_views[channel_id],
                "sample_likes": channel_likes[channel_id],
                "sample_comments": channel_comments[channel_id],
                "subscriberCount": stats.get("subscriberCount"),
                "viewCount": stats.get("viewCount"),
                "videoCount": stats.get("videoCount"),
                "hiddenSubscriberCount": stats.get("hiddenSubscriberCount"),
            }
        )

    representative = sorted(videos, key=lambda item: (video_metric(item, "viewCount"), engagement(item)), reverse=True)[:10]
    representative_videos = []
    for video in representative:
        snippet = video.get("snippet") or {}
        content = video.get("contentDetails") or {}
        category_id = snippet.get("categoryId")
        seconds = parse_iso8601_duration(content.get("duration"))
        representative_videos.append(
            {
                "id": video.get("id"),
                "url": video_url(video.get("id")),
                "title": snippet.get("title"),
                "publishedAt": snippet.get("publishedAt"),
                "channelId": snippet.get("channelId"),
                "channelTitle": snippet.get("channelTitle"),
                "category": categories.get(category_id or "", category_id),
                "duration": content.get("duration"),
                "durationText": format_duration(seconds),
                "statistics": video.get("statistics") or {},
                "description": clean_text(snippet.get("description") or "", 260),
            }
        )

    return {
        "sample_size": len(videos),
        "total_views_in_sample": total_views,
        "total_likes_in_sample": total_likes,
        "total_comments_in_sample": total_comments,
        "channels": top_channels,
        "categories": category_counts.most_common(20),
        "tags": tag_counts.most_common(20),
        "hashtags": hashtag_counts.most_common(20),
        "domains": domain_counts.most_common(20),
        "languages": language_counts.most_common(20),
        "duration_buckets": duration_counts.most_common(20),
        "published_days": published_days.most_common(20),
        "representative_videos": representative_videos,
    }


def render_counter(title: str, items: list[tuple[str, int]], limit: int = 10) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        lines.append("- None found in sample.")
        return lines
    for key, count in items[:limit]:
        lines.append(f"- {key}: {count}")
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# YouTube Topic Scan")
    lines.append("")
    lines.append(f"- Query: `{summary['query']}`")
    lines.append(f"- Search endpoint: `{summary['search_endpoint']}`")
    lines.append(f"- Video details endpoint: `{summary['video_endpoint']}`")
    lines.append(f"- Channel details endpoint: `{summary['channel_endpoint']}`")
    lines.append(f"- Sample size: {summary['analysis']['sample_size']} videos")
    if summary.get("filters"):
        lines.append(f"- Filters: {summary['filters']}")
    page_info = summary.get("page_info") or {}
    if page_info:
        total = page_info.get("totalResults")
        per_page = page_info.get("resultsPerPage")
        lines.append(f"- Search result estimate: {total} total, {per_page} per page")
    if summary.get("errors"):
        lines.append(f"- Partial errors: {len(summary['errors'])}")
    lines.append("")

    analysis = summary["analysis"]
    lines.append("## Sample Totals")
    lines.append(f"- Views in sample: {analysis['total_views_in_sample']}")
    lines.append(f"- Likes in sample: {analysis['total_likes_in_sample']}")
    lines.append(f"- Comments in sample: {analysis['total_comments_in_sample']}")
    lines.append("")

    lines.append("## Top Channels In Sample")
    if analysis["channels"]:
        for channel in analysis["channels"][:10]:
            hidden = " hidden_subscribers" if channel.get("hiddenSubscriberCount") else ""
            subs = channel.get("subscriberCount")
            subs_text = f", subscribers {subs}" if subs is not None and not hidden else hidden
            url_text = f" {channel['url']}" if channel.get("url") else ""
            lines.append(
                f"- {channel['title']}: {channel['videos_in_sample']} videos, "
                f"sample views {channel['sample_views']}{subs_text}{url_text}"
            )
    else:
        lines.append("- None found in sample.")
    lines.append("")

    for key, title in [
        ("categories", "Top Categories"),
        ("tags", "Top Tags"),
        ("hashtags", "Top Hashtags"),
        ("domains", "Linked Domains In Descriptions"),
        ("languages", "Languages"),
        ("duration_buckets", "Duration Buckets"),
        ("published_days", "Published Days"),
    ]:
        lines.extend(render_counter(title, analysis.get(key, [])))
        lines.append("")

    lines.append("## Representative Videos")
    if analysis["representative_videos"]:
        for idx, video in enumerate(analysis["representative_videos"][:8], 1):
            stats = video.get("statistics") or {}
            lines.append(
                f"{idx}. {video.get('title')} ({video.get('publishedAt')}) "
                f"views {stats.get('viewCount', 'n/a')} likes {stats.get('likeCount', 'n/a')} "
                f"comments {stats.get('commentCount', 'n/a')} [{video.get('url')}]"
            )
            lines.append(
                f"   Channel: {video.get('channelTitle')} | Duration: {video.get('durationText')} | "
                f"Category: {video.get('category')}"
            )
            if video.get("description"):
                lines.append(f"   {video['description']}")
    else:
        lines.append("- No videos returned.")

    if summary.get("errors"):
        lines.append("")
        lines.append("## API Notes")
        for error in summary["errors"]:
            lines.append(f"- {error}")

    lines.append("")
    lines.append("## Caveats")
    lines.append("- YouTube search is ranked and sampled; it is not a complete census.")
    lines.append("- `pageInfo.totalResults` is an estimate and can change between calls.")
    lines.append("- Public metrics are point-in-time snapshots and may omit hidden or unavailable fields.")
    lines.append("- Private, deleted, region-blocked, age-restricted, or otherwise unavailable videos may be absent.")
    return "\n".join(lines)


def build_filter_text(args: argparse.Namespace) -> str:
    pairs = [
        ("order", args.order),
        ("publishedAfter", args.published_after),
        ("publishedBefore", args.published_before),
        ("regionCode", args.region_code),
        ("relevanceLanguage", args.relevance_language),
        ("channelId", args.channel_id),
        ("safeSearch", args.safe_search),
        ("videoDuration", args.video_duration),
        ("videoDefinition", args.video_definition),
        ("videoCategoryId", args.video_category_id),
        ("eventType", args.event_type),
        ("topicId", args.topic_id),
    ]
    return ", ".join(f"{key}={value}" for key, value in pairs if value)


def run(args: argparse.Namespace) -> dict[str, Any]:
    client = YouTubeApiClient(env_path=args.env)
    errors: list[str] = []
    max_pages = args.max_pages or max(1, math.ceil(args.max_videos / args.max_results))
    search_params: dict[str, Any] = {
        "part": "snippet",
        "q": args.query,
        "type": "video",
        "order": args.order,
        "maxResults": args.max_results,
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
    }
    search_params.update(parse_kv(args.param))
    search_pages = paginate(client, "/search", search_params, max_pages=max_pages)
    search_items = collect_items(search_pages)[: args.max_videos]
    video_ids = search_video_ids(search_items)

    videos: list[dict[str, Any]] = []
    if video_ids:
        videos = fetch_videos(client, video_ids, part=DEFAULT_VIDEO_PARTS)

    channel_ids = sorted(
        {
            (video.get("snippet") or {}).get("channelId")
            for video in videos
            if (video.get("snippet") or {}).get("channelId")
        }
    )
    channels: dict[str, dict[str, Any]] = {}
    if channel_ids and not args.skip_channel_details:
        try:
            channel_items = fetch_channels(client, channel_ids, part=DEFAULT_CHANNEL_PARTS)
            channels = {item["id"]: item for item in channel_items if item.get("id")}
        except YouTubeApiError as exc:
            errors.append(f"channel details failed with status {exc.status}: {exc.data}")

    categories: dict[str, str] = {}
    if not args.skip_categories:
        categories = fetch_video_categories(client, args.region_code, args.hl)

    return {
        "query": args.query,
        "search_endpoint": "/youtube/v3/search",
        "video_endpoint": "/youtube/v3/videos",
        "channel_endpoint": "/youtube/v3/channels",
        "filters": build_filter_text(args),
        "page_info": first_page_info(search_pages),
        "search_pages_returned": len(search_pages),
        "search_items_returned": len(search_items),
        "analysis": analyze_videos(videos, channels, categories),
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan a YouTube topic/query for video sample themes.")
    parser.add_argument("query", help="YouTube search query.")
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument("--max-videos", type=int, default=50)
    parser.add_argument("--max-results", type=int, default=25, help="Videos per search page, 1-50.")
    parser.add_argument("--max-pages", type=int, help="Override page count.")
    parser.add_argument("--order", choices=["date", "rating", "relevance", "title", "videoCount", "viewCount"], default="relevance")
    parser.add_argument("--published-after")
    parser.add_argument("--published-before")
    parser.add_argument("--region-code")
    parser.add_argument("--relevance-language")
    parser.add_argument("--channel-id")
    parser.add_argument("--safe-search", choices=["moderate", "none", "strict"])
    parser.add_argument("--video-duration", choices=["any", "short", "medium", "long"])
    parser.add_argument("--video-definition", choices=["any", "high", "standard"])
    parser.add_argument("--video-category-id")
    parser.add_argument("--event-type", choices=["completed", "live", "upcoming"])
    parser.add_argument("--topic-id")
    parser.add_argument("--hl", help="Language for video category names.")
    parser.add_argument("--skip-channel-details", action="store_true")
    parser.add_argument("--skip-categories", action="store_true")
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
