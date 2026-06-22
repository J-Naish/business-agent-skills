#!/usr/bin/env python3
"""Video and comment-thread research using YouTube Data API endpoints."""
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
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from trend_scan import (  # noqa: E402
    channel_url,
    clean_text,
    domain_from_url,
    extract_hashtags,
    format_duration,
    parse_iso8601_duration,
    to_int,
    video_url,
)
from youtube_api import (  # noqa: E402
    DEFAULT_CHANNEL_PARTS,
    DEFAULT_COMMENT_THREAD_PARTS,
    DEFAULT_VIDEO_PARTS,
    YouTubeApiClient,
    YouTubeApiError,
    collect_items,
    fetch_channels,
    fetch_videos,
    first_page_info,
    paginate,
    parse_kv,
    parse_video_ids,
)


def extract_domains(text: str) -> list[str]:
    domains: list[str] = []
    for match in re.findall(r"https?://[^\s)>\]]+", text):
        domain = domain_from_url(match)
        if domain:
            domains.append(domain)
    return domains


def comment_snippet(thread: dict[str, Any]) -> dict[str, Any]:
    snippet = thread.get("snippet") or {}
    top = snippet.get("topLevelComment") or {}
    return top.get("snippet") or {}


def comment_text(snippet: dict[str, Any]) -> str:
    return snippet.get("textOriginal") or snippet.get("textDisplay") or ""


def analyze_comments(threads: list[dict[str, Any]]) -> dict[str, Any]:
    authors: Counter[str] = Counter()
    hashtags: Counter[str] = Counter()
    domains: Counter[str] = Counter()
    published_days: Counter[str] = Counter()
    reply_counts: Counter[str] = Counter()
    total_likes = 0
    total_replies = 0

    comments: list[dict[str, Any]] = []
    for thread in threads:
        snippet = thread.get("snippet") or {}
        top = comment_snippet(thread)
        text = comment_text(top)
        author = top.get("authorDisplayName") or "unknown"
        authors.update([author])
        hashtags.update(extract_hashtags(text))
        domains.update(extract_domains(text))

        like_count = to_int(top.get("likeCount"))
        reply_count = to_int(snippet.get("totalReplyCount"))
        total_likes += like_count
        total_replies += reply_count
        reply_counts.update([str(reply_count)])

        published_at = top.get("publishedAt")
        if published_at:
            published_days.update([published_at[:10]])

        comments.append(
            {
                "id": (snippet.get("topLevelComment") or {}).get("id"),
                "authorDisplayName": author,
                "publishedAt": published_at,
                "updatedAt": top.get("updatedAt"),
                "likeCount": like_count,
                "replyCount": reply_count,
                "text": clean_text(text, 320),
            }
        )

    representative = sorted(comments, key=lambda item: (item["likeCount"], item["replyCount"]), reverse=True)[:10]
    return {
        "sample_size": len(threads),
        "total_likes_in_sample": total_likes,
        "total_replies_in_sample": total_replies,
        "authors": authors.most_common(20),
        "hashtags": hashtags.most_common(20),
        "domains": domains.most_common(20),
        "published_days": published_days.most_common(20),
        "reply_counts": reply_counts.most_common(20),
        "representative_comments": representative,
    }


def video_summary(video: dict[str, Any], channel: dict[str, Any] | None = None) -> dict[str, Any]:
    snippet = video.get("snippet") or {}
    content = video.get("contentDetails") or {}
    stats = video.get("statistics") or {}
    seconds = parse_iso8601_duration(content.get("duration"))
    return {
        "id": video.get("id"),
        "url": video_url(video.get("id")),
        "title": snippet.get("title"),
        "description": clean_text(snippet.get("description") or "", 500),
        "publishedAt": snippet.get("publishedAt"),
        "channelId": snippet.get("channelId"),
        "channelTitle": snippet.get("channelTitle"),
        "channelUrl": channel_url(snippet.get("channelId")),
        "channelSubscriberCount": ((channel or {}).get("statistics") or {}).get("subscriberCount"),
        "channelHiddenSubscriberCount": ((channel or {}).get("statistics") or {}).get("hiddenSubscriberCount"),
        "categoryId": snippet.get("categoryId"),
        "duration": content.get("duration"),
        "durationText": format_duration(seconds),
        "definition": content.get("definition"),
        "caption": content.get("caption"),
        "licensedContent": content.get("licensedContent"),
        "privacyStatus": (video.get("status") or {}).get("privacyStatus"),
        "madeForKids": (video.get("status") or {}).get("madeForKids"),
        "tags": snippet.get("tags", [])[:20] if isinstance(snippet.get("tags"), list) else [],
        "statistics": stats,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    video_ids = parse_video_ids([args.video])
    if not video_ids:
        raise SystemExit("Provide a video ID or URL.")
    video_id = video_ids[0]
    client = YouTubeApiClient(env_path=args.env)
    errors: list[str] = []

    videos = fetch_videos(client, [video_id], part=DEFAULT_VIDEO_PARTS)
    if not videos:
        raise SystemExit(f"Could not look up video: {video_id}")
    video = videos[0]

    channel: dict[str, Any] | None = None
    channel_id = (video.get("snippet") or {}).get("channelId")
    if channel_id and not args.skip_channel:
        try:
            channels = fetch_channels(client, [channel_id], part=DEFAULT_CHANNEL_PARTS)
            channel = channels[0] if channels else None
        except YouTubeApiError as exc:
            errors.append(f"channel lookup failed with status {exc.status}: {exc.data}")

    comment_pages: list[dict[str, Any]] = []
    comment_threads: list[dict[str, Any]] = []
    if not args.skip_comments:
        try:
            max_pages = args.max_pages or max(1, math.ceil(args.max_comments / args.max_results))
            params: dict[str, Any] = {
                "part": DEFAULT_COMMENT_THREAD_PARTS,
                "videoId": video_id,
                "maxResults": args.max_results,
                "order": args.comment_order,
                "textFormat": args.text_format,
            }
            params.update(parse_kv(args.param))
            comment_pages = paginate(client, "/commentThreads", params, max_pages=max_pages)
            comment_threads = collect_items(comment_pages)[: args.max_comments]
        except YouTubeApiError as exc:
            errors.append(f"comment threads failed with status {exc.status}: {exc.data}")

    return {
        "video_id": video_id,
        "video_endpoint": "/youtube/v3/videos",
        "channel_endpoint": "/youtube/v3/channels",
        "comment_endpoint": "/youtube/v3/commentThreads",
        "comment_filters": {
            "order": args.comment_order,
            "textFormat": args.text_format,
            "maxComments": args.max_comments,
            "maxPages": args.max_pages,
        },
        "comment_page_info": first_page_info(comment_pages),
        "video": video_summary(video, channel),
        "comment_analysis": analyze_comments(comment_threads),
        "errors": errors,
    }


def render_counter(title: str, items: list[tuple[str, int]], limit: int = 10) -> list[str]:
    lines = [f"### {title}"]
    if not items:
        lines.append("- None found in sample.")
        return lines
    for item, count in items[:limit]:
        lines.append(f"- {item}: {count}")
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    video = summary["video"]
    stats = video.get("statistics") or {}
    comments = summary["comment_analysis"]

    lines: list[str] = []
    lines.append("# YouTube Video Scan")
    lines.append("")
    lines.append(f"- Video: {video.get('title')} ({summary['video_id']})")
    lines.append(f"- URL: {video.get('url')}")
    lines.append(f"- Channel: {video.get('channelTitle')} ({video.get('channelId')}) {video.get('channelUrl')}")
    if video.get("channelSubscriberCount") is not None:
        lines.append(f"- Channel subscribers: {video.get('channelSubscriberCount')}")
    elif video.get("channelHiddenSubscriberCount"):
        lines.append("- Channel subscribers: hidden")
    lines.append(f"- Published: {video.get('publishedAt')}")
    lines.append(f"- Duration: {video.get('durationText')} ({video.get('duration')})")
    lines.append(f"- Category ID: {video.get('categoryId')}")
    lines.append(f"- Definition: {video.get('definition')}, captions {video.get('caption')}")
    lines.append(
        f"- Metrics: views {stats.get('viewCount', 'n/a')}, "
        f"likes {stats.get('likeCount', 'n/a')}, comments {stats.get('commentCount', 'n/a')}"
    )
    if video.get("tags"):
        lines.append(f"- Tags: {', '.join(video['tags'][:12])}")
    if video.get("description"):
        lines.append(f"- Description: {video['description']}")
    lines.append("")
    lines.append(f"- Video endpoint: `{summary['video_endpoint']}`")
    lines.append(f"- Channel endpoint: `{summary['channel_endpoint']}`")
    lines.append(f"- Comment endpoint: `{summary['comment_endpoint']}`")
    lines.append(f"- Comment filters: {summary.get('comment_filters')}")
    if summary.get("comment_page_info"):
        lines.append(f"- Comment page info: {summary['comment_page_info']}")
    lines.append("")

    lines.append("## Comment Sample")
    lines.append(f"- Sample size: {comments['sample_size']} top-level comment threads")
    lines.append(f"- Likes in comment sample: {comments['total_likes_in_sample']}")
    lines.append(f"- Replies in comment sample: {comments['total_replies_in_sample']}")
    lines.append("")
    for key, title in [
        ("authors", "Top Comment Authors"),
        ("hashtags", "Top Comment Hashtags"),
        ("domains", "Linked Domains In Comments"),
        ("published_days", "Comment Published Days"),
        ("reply_counts", "Reply Count Distribution"),
    ]:
        lines.extend(render_counter(title, comments.get(key, [])))
        lines.append("")

    lines.append("### Representative Comments")
    if comments["representative_comments"]:
        for idx, comment in enumerate(comments["representative_comments"][:8], 1):
            lines.append(
                f"{idx}. {comment.get('authorDisplayName')} ({comment.get('publishedAt')}) "
                f"likes {comment.get('likeCount')} replies {comment.get('replyCount')}"
            )
            lines.append(f"   {comment.get('text')}")
    else:
        lines.append("- No comments returned.")

    if summary.get("errors"):
        lines.append("")
        lines.append("## API Notes")
        for error in summary["errors"]:
            lines.append(f"- {error}")

    lines.append("")
    lines.append("## Caveats")
    lines.append("- Video and comment metrics are point-in-time snapshots.")
    lines.append("- Comment samples depend on comments being enabled, public, and accessible through the API.")
    lines.append("- Returned comment order depends on the requested API order, not necessarily the visible web UI order.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a YouTube video and comment-thread sample.")
    parser.add_argument("video", help="Video ID or URL.")
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument("--skip-channel", action="store_true")
    parser.add_argument("--skip-comments", action="store_true")
    parser.add_argument("--max-comments", type=int, default=50)
    parser.add_argument("--max-results", type=int, default=50, help="Comments per page, 1-100.")
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--comment-order", choices=["time", "relevance"], default="relevance")
    parser.add_argument("--text-format", choices=["html", "plainText"], default="plainText")
    parser.add_argument("--param", action="append", help="Extra commentThreads parameter as KEY=VALUE.")
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
