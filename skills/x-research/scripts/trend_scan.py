#!/usr/bin/env python3
"""Topic/query research for X using counts plus sampled posts."""
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

from x_api import (  # noqa: E402
    XApiClient,
    XApiError,
    paginate,
    parse_kv,
    with_default_tweet_params,
)


def build_query(args: argparse.Namespace) -> str:
    query = args.query.strip()
    additions: list[str] = []
    if args.lang and "lang:" not in query:
        additions.append(f"lang:{args.lang}")
    if args.exclude_retweets and "-is:retweet" not in query and "is:retweet" not in query:
        additions.append("-is:retweet")
    if args.exclude_replies and "-is:reply" not in query and "is:reply" not in query:
        additions.append("-is:reply")
    return " ".join([query, *additions]).strip()


def page_payloads(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [page.get("data", {}) for page in pages if isinstance(page.get("data"), dict)]


def collect_posts(pages: list[dict[str, Any]], max_posts: int) -> list[dict[str, Any]]:
    posts: list[dict[str, Any]] = []
    for payload in page_payloads(pages):
        data = payload.get("data")
        if isinstance(data, list):
            posts.extend(data)
    return posts[:max_posts]


def collect_users(pages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    users: dict[str, dict[str, Any]] = {}
    for payload in page_payloads(pages):
        includes = payload.get("includes", {})
        for user in includes.get("users", []) if isinstance(includes, dict) else []:
            if isinstance(user, dict) and user.get("id"):
                users[user["id"]] = user
    return users


def collect_count_buckets(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    for payload in page_payloads(pages):
        data = payload.get("data")
        if isinstance(data, list):
            buckets.extend(data)
    return buckets


def engagement(post: dict[str, Any]) -> int:
    metrics = post.get("public_metrics") or {}
    keys = ["like_count", "retweet_count", "reply_count", "quote_count", "bookmark_count"]
    return sum(int(metrics.get(key) or 0) for key in keys)


def clean_text(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception:
        return ""
    return parsed.netloc.lower().removeprefix("www.")


def post_url(post: dict[str, Any], users: dict[str, dict[str, Any]]) -> str | None:
    author = users.get(str(post.get("author_id") or ""))
    if not author or not author.get("username") or not post.get("id"):
        return None
    return f"https://x.com/{author['username']}/status/{post['id']}"


def analyze(posts: list[dict[str, Any]], users: dict[str, dict[str, Any]]) -> dict[str, Any]:
    hashtags: Counter[str] = Counter()
    mentions: Counter[str] = Counter()
    domains: Counter[str] = Counter()
    urls: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    contexts: Counter[str] = Counter()
    author_counts: Counter[str] = Counter()
    author_engagement: defaultdict[str, int] = defaultdict(int)

    for post in posts:
        languages.update([post.get("lang") or "unknown"])
        author_id = str(post.get("author_id") or "")
        if author_id:
            author_counts.update([author_id])
            author_engagement[author_id] += engagement(post)

        entities = post.get("entities") or {}
        for item in entities.get("hashtags", []) if isinstance(entities, dict) else []:
            tag = item.get("tag") if isinstance(item, dict) else None
            if tag:
                hashtags.update([tag.lower()])
        for item in entities.get("mentions", []) if isinstance(entities, dict) else []:
            username = item.get("username") if isinstance(item, dict) else None
            if username:
                mentions.update([username.lower()])
        for item in entities.get("urls", []) if isinstance(entities, dict) else []:
            if not isinstance(item, dict):
                continue
            expanded = item.get("expanded_url") or item.get("unwound_url") or item.get("url")
            if expanded:
                urls.update([expanded])
                domain = domain_from_url(expanded)
                if domain:
                    domains.update([domain])

        for item in post.get("context_annotations", []) or []:
            if not isinstance(item, dict):
                continue
            domain_name = (item.get("domain") or {}).get("name")
            entity_name = (item.get("entity") or {}).get("name")
            if domain_name and entity_name:
                contexts.update([f"{domain_name}: {entity_name}"])

    top_authors = []
    for author_id, count in author_counts.most_common(20):
        user = users.get(author_id, {})
        top_authors.append(
            {
                "id": author_id,
                "username": user.get("username"),
                "name": user.get("name"),
                "posts_in_sample": count,
                "sample_engagement": author_engagement[author_id],
                "followers": (user.get("public_metrics") or {}).get("followers_count"),
            }
        )

    representative = sorted(posts, key=engagement, reverse=True)[:10]
    representative_posts = []
    for post in representative:
        author = users.get(str(post.get("author_id") or ""), {})
        representative_posts.append(
            {
                "id": post.get("id"),
                "created_at": post.get("created_at"),
                "username": author.get("username"),
                "name": author.get("name"),
                "engagement": engagement(post),
                "public_metrics": post.get("public_metrics") or {},
                "url": post_url(post, users),
                "text": clean_text(post.get("text") or ""),
            }
        )

    return {
        "sample_size": len(posts),
        "hashtags": hashtags.most_common(20),
        "mentions": mentions.most_common(20),
        "domains": domains.most_common(20),
        "urls": urls.most_common(20),
        "languages": languages.most_common(20),
        "contexts": contexts.most_common(20),
        "authors": top_authors,
        "representative_posts": representative_posts,
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
    lines.append("# X Topic Scan")
    lines.append("")
    lines.append(f"- Query: `{summary['query']}`")
    lines.append(f"- Search endpoint: `{summary['search_endpoint']}`")
    lines.append(f"- Count endpoint: `{summary['count_endpoint']}`")
    lines.append(f"- Sample size: {summary['analysis']['sample_size']} posts")
    if summary.get("time_window"):
        lines.append(f"- Time window: {summary['time_window']}")
    if summary.get("errors"):
        lines.append(f"- Partial errors: {len(summary['errors'])}")
    lines.append("")

    buckets = summary.get("count_buckets") or []
    total = sum(int(bucket.get("tweet_count") or 0) for bucket in buckets)
    lines.append("## Volume")
    if buckets:
        lines.append(f"- Counted posts in returned buckets: {total}")
        lines.append(f"- Buckets returned: {len(buckets)}")
        top_buckets = sorted(buckets, key=lambda item: int(item.get("tweet_count") or 0), reverse=True)[:10]
        for bucket in top_buckets:
            lines.append(
                f"- {bucket.get('start')} to {bucket.get('end')}: {bucket.get('tweet_count')}"
            )
    else:
        lines.append("- Counts unavailable or not returned for this query.")
    lines.append("")

    analysis = summary["analysis"]
    for section, title in [
        ("hashtags", "Top Hashtags"),
        ("mentions", "Top Mentions"),
        ("domains", "Top Domains"),
        ("languages", "Languages"),
        ("contexts", "Context Annotations"),
    ]:
        lines.extend(render_counter(title, analysis.get(section, [])))
        lines.append("")

    lines.append("## Top Authors In Sample")
    if analysis["authors"]:
        for author in analysis["authors"][:10]:
            handle = f"@{author['username']}" if author.get("username") else author["id"]
            followers = author.get("followers")
            follower_text = f", followers {followers}" if followers is not None else ""
            lines.append(
                f"- {handle}: {author['posts_in_sample']} posts, "
                f"sample engagement {author['sample_engagement']}{follower_text}"
            )
    else:
        lines.append("- None found in sample.")
    lines.append("")

    lines.append("## Representative Posts")
    if analysis["representative_posts"]:
        for idx, post in enumerate(analysis["representative_posts"][:8], 1):
            handle = f"@{post['username']}" if post.get("username") else post.get("id")
            link = f" [{post['url']}]" if post.get("url") else ""
            lines.append(f"{idx}. {handle} ({post.get('created_at')}) engagement {post['engagement']}{link}")
            lines.append(f"   {post['text']}")
    else:
        lines.append("- No posts returned.")

    if summary.get("errors"):
        lines.append("")
        lines.append("## API Notes")
        for error in summary["errors"]:
            lines.append(f"- {error}")

    lines.append("")
    lines.append("## Caveats")
    lines.append("- Results depend on X API access tier, rate limits, query design, and the selected time window.")
    lines.append("- Sample analysis is not a full census unless the endpoint and paging cover the full result set.")
    lines.append("- Engagement metrics are point-in-time snapshots.")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    query = build_query(args)
    client = XApiClient(auth=args.auth, env_path=args.env)
    errors: list[str] = []
    max_pages = args.max_pages or max(1, math.ceil(args.max_posts / args.max_results))
    search_endpoint = "/2/tweets/search/all" if args.all else "/2/tweets/search/recent"
    count_endpoint = "/2/tweets/counts/all" if args.all else "/2/tweets/counts/recent"

    base_params: dict[str, Any] = {
        "query": query,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "since_id": args.since_id,
        "until_id": args.until_id,
    }
    base_params.update(parse_kv(args.param))

    count_pages: list[dict[str, Any]] = []
    if not args.skip_counts:
        try:
            count_params = dict(base_params)
            count_params["granularity"] = args.granularity
            count_pages = paginate(client, count_endpoint, count_params, max_pages=1, auth=args.auth)
        except XApiError as exc:
            errors.append(f"counts failed with status {exc.status}: {exc.data}")

    search_params = dict(base_params)
    search_params["max_results"] = args.max_results
    if args.sort_order:
        search_params["sort_order"] = args.sort_order
    with_default_tweet_params(search_params, no_defaults=args.no_default_fields)
    search_pages = paginate(client, search_endpoint, search_params, max_pages=max_pages, auth=args.auth)
    posts = collect_posts(search_pages, args.max_posts)
    users = collect_users(search_pages)

    time_bits = []
    if args.start_time:
        time_bits.append(f"start={args.start_time}")
    if args.end_time:
        time_bits.append(f"end={args.end_time}")
    if args.since_id:
        time_bits.append(f"since_id={args.since_id}")
    if args.until_id:
        time_bits.append(f"until_id={args.until_id}")

    return {
        "query": query,
        "search_endpoint": search_endpoint,
        "count_endpoint": count_endpoint,
        "time_window": ", ".join(time_bits),
        "count_buckets": collect_count_buckets(count_pages),
        "analysis": analyze(posts, users),
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan an X topic/query for volume and themes.")
    parser.add_argument("query", help="X search query. Operators are supported.")
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument("--auth", choices=["bearer", "oauth1"], default="bearer")
    parser.add_argument("--all", action="store_true", help="Use full-archive endpoints.")
    parser.add_argument("--lang", help="Append lang:<value> if the query has no lang operator.")
    parser.add_argument("--exclude-retweets", action="store_true")
    parser.add_argument("--exclude-replies", action="store_true")
    parser.add_argument("--max-posts", type=int, default=100)
    parser.add_argument("--max-results", type=int, default=100, help="Posts per page, usually 10-100.")
    parser.add_argument("--max-pages", type=int, help="Override page count.")
    parser.add_argument("--granularity", choices=["minute", "hour", "day"], default="hour")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--since-id")
    parser.add_argument("--until-id")
    parser.add_argument("--sort-order", choices=["recency", "relevancy"])
    parser.add_argument("--skip-counts", action="store_true")
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
