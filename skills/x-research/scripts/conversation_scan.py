#!/usr/bin/env python3
"""Analyze an X post, its conversation_id search results, and quote posts."""
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

from trend_scan import analyze, clean_text, collect_posts, collect_users  # noqa: E402
from x_api import (  # noqa: E402
    XApiClient,
    XApiError,
    paginate,
    parse_kv,
    parse_post_ids,
    with_default_tweet_params,
)


def lookup_post(client: XApiClient, post_id: str, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    params = {"ids": post_id}
    with_default_tweet_params(params, no_defaults=args.no_default_fields)
    response = client.request("GET", "/2/tweets", params, auth=args.auth)
    payload = response.get("data", {})
    posts = payload.get("data") if isinstance(payload, dict) else None
    if not posts:
        raise SystemExit(f"Could not look up post: {post_id}")
    users: dict[str, dict[str, Any]] = {}
    includes = payload.get("includes", {}) if isinstance(payload, dict) else {}
    for user in includes.get("users", []) if isinstance(includes, dict) else []:
        if isinstance(user, dict) and user.get("id"):
            users[user["id"]] = user
    return posts[0], users


def post_author(post: dict[str, Any], users: dict[str, dict[str, Any]]) -> str:
    user = users.get(str(post.get("author_id") or ""))
    if user and user.get("username"):
        return f"@{user['username']}"
    return str(post.get("author_id") or "unknown")


def post_link(post: dict[str, Any], users: dict[str, dict[str, Any]]) -> str | None:
    user = users.get(str(post.get("author_id") or ""))
    if user and user.get("username") and post.get("id"):
        return f"https://x.com/{user['username']}/status/{post['id']}"
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    post_ids = parse_post_ids([args.post])
    if not post_ids:
        raise SystemExit("Provide a post ID or URL.")
    post_id = post_ids[0]
    client = XApiClient(auth=args.auth, env_path=args.env)
    original, original_users = lookup_post(client, post_id, args)
    conversation_id = original.get("conversation_id") or post_id
    errors: list[str] = []

    query_parts = [f"conversation_id:{conversation_id}"]
    if args.lang:
        query_parts.append(f"lang:{args.lang}")
    if not args.include_retweets:
        query_parts.append("-is:retweet")
    if args.query_extra:
        query_parts.append(args.query_extra)
    query = " ".join(query_parts)

    max_pages = args.max_pages or max(1, math.ceil(args.max_posts / args.max_results))
    search_endpoint = "/2/tweets/search/all" if args.all else "/2/tweets/search/recent"
    search_params: dict[str, Any] = {
        "query": query,
        "max_results": args.max_results,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "since_id": args.since_id,
        "until_id": args.until_id,
    }
    search_params.update(parse_kv(args.param))
    with_default_tweet_params(search_params, no_defaults=args.no_default_fields)

    conversation_pages: list[dict[str, Any]] = []
    quote_pages: list[dict[str, Any]] = []
    try:
        conversation_pages = paginate(
            client, search_endpoint, search_params, max_pages=max_pages, auth=args.auth
        )
    except XApiError as exc:
        errors.append(f"conversation search failed with status {exc.status}: {exc.data}")

    if not args.skip_quotes:
        try:
            quote_params: dict[str, Any] = {"max_results": args.max_results}
            with_default_tweet_params(quote_params, no_defaults=args.no_default_fields)
            quote_pages = paginate(
                client,
                f"/2/tweets/{post_id}/quote_tweets",
                quote_params,
                max_pages=max_pages,
                auth=args.auth,
            )
        except XApiError as exc:
            errors.append(f"quote posts failed with status {exc.status}: {exc.data}")

    conversation_users = collect_users(conversation_pages)
    conversation_users.update(original_users)
    quote_users = collect_users(quote_pages)
    quote_users.update(original_users)

    return {
        "post_id": post_id,
        "conversation_id": conversation_id,
        "query": query,
        "search_endpoint": search_endpoint,
        "quote_endpoint": f"/2/tweets/{post_id}/quote_tweets",
        "original_post": original,
        "original_users": original_users,
        "conversation_analysis": analyze(
            collect_posts(conversation_pages, args.max_posts), conversation_users
        ),
        "quote_analysis": analyze(collect_posts(quote_pages, args.max_posts), quote_users),
        "errors": errors,
    }


def render_post(post: dict[str, Any], users: dict[str, dict[str, Any]]) -> list[str]:
    lines = []
    lines.append(f"- Author: {post_author(post, users)}")
    lines.append(f"- Created: {post.get('created_at')}")
    lines.append(f"- Conversation ID: {post.get('conversation_id')}")
    lines.append(f"- Metrics: {post.get('public_metrics') or {}}")
    link = post_link(post, users)
    if link:
        lines.append(f"- URL: {link}")
    lines.append("")
    lines.append(clean_text(post.get("text") or "", 500))
    return lines


def render_analysis(title: str, analysis: dict[str, Any]) -> list[str]:
    lines = [f"## {title}"]
    lines.append(f"- Sample size: {analysis['sample_size']} posts")
    lines.append("")
    lines.append("### Top Authors")
    if analysis["authors"]:
        for author in analysis["authors"][:8]:
            handle = f"@{author['username']}" if author.get("username") else author["id"]
            lines.append(
                f"- {handle}: {author['posts_in_sample']} posts, "
                f"sample engagement {author['sample_engagement']}"
            )
    else:
        lines.append("- None found in sample.")
    lines.append("")
    for key, label in [
        ("hashtags", "Top Hashtags"),
        ("mentions", "Top Mentions"),
        ("domains", "Top Domains"),
    ]:
        lines.append(f"### {label}")
        items = analysis.get(key) or []
        if items:
            for item, count in items[:8]:
                lines.append(f"- {item}: {count}")
        else:
            lines.append("- None found in sample.")
        lines.append("")
    lines.append("### Representative Posts")
    if analysis["representative_posts"]:
        for idx, post in enumerate(analysis["representative_posts"][:8], 1):
            handle = f"@{post['username']}" if post.get("username") else post.get("id")
            link = f" {post['url']}" if post.get("url") else ""
            lines.append(f"{idx}. {handle} ({post.get('created_at')}) engagement {post['engagement']}{link}")
            lines.append(f"   {post['text']}")
    else:
        lines.append("- No posts returned.")
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# X Conversation Scan")
    lines.append("")
    lines.append(f"- Post ID: {summary['post_id']}")
    lines.append(f"- Conversation ID: {summary['conversation_id']}")
    lines.append(f"- Search query: `{summary['query']}`")
    lines.append(f"- Search endpoint: `{summary['search_endpoint']}`")
    lines.append(f"- Quote endpoint: `{summary['quote_endpoint']}`")
    lines.append("")
    lines.append("## Original Post")
    lines.extend(render_post(summary["original_post"], summary["original_users"]))
    lines.append("")
    lines.extend(render_analysis("Conversation Search Results", summary["conversation_analysis"]))
    lines.append("")
    lines.extend(render_analysis("Quote Posts", summary["quote_analysis"]))

    if summary.get("errors"):
        lines.append("")
        lines.append("## API Notes")
        for error in summary["errors"]:
            lines.append(f"- {error}")

    lines.append("")
    lines.append("## Caveats")
    lines.append("- Recent search may miss older replies unless full-archive access is used.")
    lines.append("- Quote, reply, and engagement visibility depends on access tier and post availability.")
    lines.append("- Engagement metrics are point-in-time snapshots.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze an X post conversation.")
    parser.add_argument("post", help="Post ID or URL.")
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument("--auth", choices=["bearer", "oauth1"], default="bearer")
    parser.add_argument("--all", action="store_true", help="Use full-archive search for replies.")
    parser.add_argument("--lang")
    parser.add_argument("--query-extra", help="Extra search operators to append.")
    parser.add_argument("--include-retweets", action="store_true", help="Do not append -is:retweet.")
    parser.add_argument("--max-posts", type=int, default=100)
    parser.add_argument("--max-results", type=int, default=100)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--since-id")
    parser.add_argument("--until-id")
    parser.add_argument("--skip-quotes", action="store_true")
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
