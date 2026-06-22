#!/usr/bin/env python3
"""Account, competitor, or creator research using X API user endpoints."""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from trend_scan import analyze, clean_text, collect_posts, collect_users, render_counter  # noqa: E402
from x_api import (  # noqa: E402
    XApiClient,
    XApiError,
    paginate,
    parse_kv,
    with_default_tweet_params,
    with_default_user_params,
)


def lookup_user(client: XApiClient, value: str, auth: str, is_id: bool) -> dict[str, Any]:
    params = with_default_user_params({})
    if is_id or value.isdigit():
        response = client.request("GET", f"/2/users/{value}", params, auth=auth)
    else:
        response = client.request("GET", f"/2/users/by/username/{value.lstrip('@')}", params, auth=auth)
    data = response.get("data", {}).get("data")
    if not isinstance(data, dict) or not data.get("id"):
        raise SystemExit(f"Could not resolve user: {value}")
    return data


def fetch_post_pages(
    client: XApiClient,
    endpoint: str,
    args: argparse.Namespace,
    max_pages: int,
    allow_exclude: bool,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "max_results": args.max_results,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "since_id": args.since_id,
        "until_id": args.until_id,
    }
    if allow_exclude and args.exclude:
        params["exclude"] = args.exclude
    params.update(parse_kv(args.param))
    with_default_tweet_params(params, no_defaults=args.no_default_fields)
    return paginate(client, endpoint, params, max_pages=max_pages, auth=args.auth)


def metric_line(metrics: dict[str, Any]) -> str:
    if not metrics:
        return "No public metrics returned"
    keys = [
        "followers_count",
        "following_count",
        "tweet_count",
        "listed_count",
        "like_count",
        "media_count",
    ]
    return ", ".join(f"{key} {metrics[key]}" for key in keys if key in metrics)


def render_posts_section(title: str, analysis: dict[str, Any], limit: int = 6) -> list[str]:
    lines = [f"## {title}"]
    lines.append(f"- Sample size: {analysis['sample_size']} posts")
    lines.append("")
    lines.extend(render_counter("Top Hashtags", analysis.get("hashtags", []), limit=8))
    lines.append("")
    lines.extend(render_counter("Top Mentions", analysis.get("mentions", []), limit=8))
    lines.append("")
    lines.extend(render_counter("Top Domains", analysis.get("domains", []), limit=8))
    lines.append("")
    lines.append("### Representative Posts")
    if analysis["representative_posts"]:
        for idx, post in enumerate(analysis["representative_posts"][:limit], 1):
            handle = f"@{post['username']}" if post.get("username") else post.get("id")
            link = f" {post['url']}" if post.get("url") else ""
            lines.append(f"{idx}. {handle} ({post.get('created_at')}) engagement {post['engagement']}{link}")
            lines.append(f"   {post['text']}")
    else:
        lines.append("- No posts returned.")
    return lines


def run(args: argparse.Namespace) -> dict[str, Any]:
    client = XApiClient(auth=args.auth, env_path=args.env)
    errors: list[str] = []
    user = lookup_user(client, args.user, args.auth, args.id)
    user_id = user["id"]

    timeline_pages: list[dict[str, Any]] = []
    mentions_pages: list[dict[str, Any]] = []

    try:
        timeline_pages = fetch_post_pages(
            client, f"/2/users/{user_id}/tweets", args, args.timeline_pages, allow_exclude=True
        )
    except XApiError as exc:
        errors.append(f"timeline failed with status {exc.status}: {exc.data}")

    if not args.skip_mentions:
        try:
            mentions_pages = fetch_post_pages(
                client,
                f"/2/users/{user_id}/mentions",
                args,
                args.mentions_pages,
                allow_exclude=False,
            )
        except XApiError as exc:
            errors.append(f"mentions failed with status {exc.status}: {exc.data}")

    timeline_users = collect_users(timeline_pages)
    mentions_users = collect_users(mentions_pages)
    timeline_users[user_id] = user
    mentions_users[user_id] = user

    return {
        "user": user,
        "timeline_endpoint": f"/2/users/{user_id}/tweets",
        "mentions_endpoint": f"/2/users/{user_id}/mentions",
        "timeline_analysis": analyze(collect_posts(timeline_pages, args.max_posts), timeline_users),
        "mentions_analysis": analyze(collect_posts(mentions_pages, args.max_posts), mentions_users),
        "errors": errors,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    user = summary["user"]
    username = user.get("username")
    lines: list[str] = []
    lines.append("# X Account Scan")
    lines.append("")
    lines.append(f"- Account: @{username} ({user.get('name')})")
    lines.append(f"- User ID: {user.get('id')}")
    lines.append(f"- Created: {user.get('created_at')}")
    lines.append(f"- Verified: {user.get('verified')} {user.get('verified_type') or ''}".rstrip())
    lines.append(f"- Public metrics: {metric_line(user.get('public_metrics') or {})}")
    if user.get("description"):
        lines.append(f"- Bio: {clean_text(user['description'], 300)}")
    if user.get("url"):
        lines.append(f"- URL: {user['url']}")
    lines.append("")
    lines.append(f"- Timeline endpoint: `{summary['timeline_endpoint']}`")
    lines.append(f"- Mentions endpoint: `{summary['mentions_endpoint']}`")
    lines.append("")

    lines.extend(render_posts_section("Recent Posts", summary["timeline_analysis"]))
    lines.append("")
    lines.extend(render_posts_section("Recent Mentions", summary["mentions_analysis"]))

    if summary.get("errors"):
        lines.append("")
        lines.append("## API Notes")
        for error in summary["errors"]:
            lines.append(f"- {error}")

    lines.append("")
    lines.append("## Caveats")
    lines.append("- Timeline and mention samples depend on access tier, rate limits, and selected page counts.")
    lines.append("- Public metrics are snapshots at retrieval time.")
    lines.append("- Protected, deleted, or withheld posts may be absent.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze an X account using public API data.")
    parser.add_argument("user", help="Username or user ID.")
    parser.add_argument("--id", action="store_true", help="Treat user argument as a user ID.")
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument("--auth", choices=["bearer", "oauth1"], default="bearer")
    parser.add_argument("--timeline-pages", type=int, default=1)
    parser.add_argument("--mentions-pages", type=int, default=1)
    parser.add_argument("--skip-mentions", action="store_true")
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--max-posts", type=int, default=100)
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--since-id")
    parser.add_argument("--until-id")
    parser.add_argument("--exclude", default="retweets", help="Comma-separated retweets,replies.")
    parser.add_argument("--no-default-fields", action="store_true")
    parser.add_argument("--param", action="append", help="Extra query parameter as KEY=VALUE.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary instead of Markdown.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run(args)
    except XApiError as exc:
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
