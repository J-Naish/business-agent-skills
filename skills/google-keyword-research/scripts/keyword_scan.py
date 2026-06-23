#!/usr/bin/env python3
"""Keyword Planner topic scan for search demand research."""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-ads",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import os
from statistics import mean
from typing import Any

from google_keyword_api import (
    clean_customer_id,
    generate_historical_metrics,
    generate_keyword_ideas,
    google_ads_error_to_dict,
    load_env,
    load_google_ads_client,
    print_json,
    resolve_geo_ids,
    resolve_language_id,
)


def metric_value(item: dict[str, Any], key: str) -> int | float:
    metrics = item.get("metrics") or {}
    value = metrics.get(key)
    return value if isinstance(value, (int, float)) else 0


def top_items(items: list[dict[str, Any]], key: str, limit: int) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: metric_value(item, key), reverse=True)[:limit]


def trend_delta(item: dict[str, Any]) -> dict[str, Any] | None:
    metrics = item.get("metrics") or {}
    months = metrics.get("monthly_search_volumes") or []
    if len(months) < 6:
        return None
    recent = months[:3]
    prior = months[3:6]
    recent_values = [month.get("monthly_searches") or 0 for month in recent]
    prior_values = [month.get("monthly_searches") or 0 for month in prior]
    recent_avg = mean(recent_values)
    prior_avg = mean(prior_values)
    if prior_avg <= 0:
        pct_change = None
    else:
        pct_change = round(((recent_avg - prior_avg) / prior_avg) * 100, 2)
    return {
        "text": item.get("text"),
        "recent_3_month_avg": round(recent_avg, 2),
        "prior_3_month_avg": round(prior_avg, 2),
        "pct_change": pct_change,
        "recent_months": [month.get("iso_month") for month in recent],
        "prior_months": [month.get("iso_month") for month in prior],
    }


def low_competition_candidates(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    candidates = []
    for item in items:
        metrics = item.get("metrics") or {}
        competition = metrics.get("competition")
        competition_index = metrics.get("competition_index") or 0
        volume = metrics.get("avg_monthly_searches") or 0
        if volume <= 0:
            continue
        if competition == "LOW" or (competition_index and competition_index <= 35):
            candidates.append(item)
    return sorted(
        candidates,
        key=lambda item: (
            metric_value(item, "avg_monthly_searches"),
            -metric_value(item, "competition_index"),
        ),
        reverse=True,
    )[:limit]


def summarize(historical_items: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    trend_items = [trend_delta(item) for item in historical_items]
    trend_items = [item for item in trend_items if item]
    rising = sorted(
        [item for item in trend_items if (item.get("pct_change") or 0) > 0],
        key=lambda item: item.get("pct_change") if item.get("pct_change") is not None else -10**9,
        reverse=True,
    )[:limit]
    declining = sorted(
        [item for item in trend_items if item.get("pct_change") is not None and item["pct_change"] < 0],
        key=lambda item: item.get("pct_change") if item.get("pct_change") is not None else 10**9,
    )[:limit]
    return {
        "top_by_avg_monthly_searches": top_items(historical_items, "avg_monthly_searches", limit),
        "top_by_high_top_of_page_bid": top_items(historical_items, "high_top_of_page_bid_micros", limit),
        "low_competition_high_volume": low_competition_candidates(historical_items, limit),
        "rising_recent_3mo_vs_prior_3mo": rising,
        "declining_recent_3mo_vs_prior_3mo": declining,
    }


def collect_keywords(args: argparse.Namespace) -> list[str]:
    keywords = [args.topic]
    keywords.extend(args.keyword or [])
    return list(dict.fromkeys([item.strip() for item in keywords if item and item.strip()]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Keyword Planner topic scan and print JSON to stdout.",
    )
    parser.add_argument("topic", help="Primary seed keyword or theme.")
    parser.add_argument("--keyword", action="append", help="Additional seed keyword. Repeatable.")
    parser.add_argument("--url", help="Optional landing page URL seed.")
    parser.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")
    parser.add_argument("--customer-id", help="Google Ads customer ID. Defaults to GOOGLE_ADS_CUSTOMER_ID.")
    parser.add_argument("--geo", action="append", help="Geo target ID/resource or common country code. Repeatable. Default: JP.")
    parser.add_argument("--language", default="ja", help="Language ID/resource or common code. Default: ja.")
    parser.add_argument(
        "--network",
        default="GOOGLE_SEARCH",
        help="GOOGLE_SEARCH or GOOGLE_SEARCH_AND_PARTNERS. Default: GOOGLE_SEARCH.",
    )
    parser.add_argument("--max-ideas", type=int, default=50, help="Maximum keyword ideas to fetch. Default: 50.")
    parser.add_argument(
        "--max-historical-keywords",
        type=int,
        default=25,
        help="Maximum seed+idea keywords to request historical metrics for. Default: 25.",
    )
    parser.add_argument("--summary-limit", type=int, default=10)
    parser.add_argument("--include-average-cpc", action="store_true", help="Request average CPC when available.")
    parser.add_argument("--include-adult-keywords", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        env_path = load_env(args.env)
        client = load_google_ads_client(args.env)
        customer_id = clean_customer_id(args.customer_id) or clean_customer_id(
            os.environ.get("GOOGLE_ADS_CUSTOMER_ID")
        )
        if not customer_id:
            print_json({"ok": False, "error": "missing_customer_id", "missing": ["GOOGLE_ADS_CUSTOMER_ID"]})
            return 1
        seed_keywords = collect_keywords(args)
        geo_ids = resolve_geo_ids(args.geo)
        language_id = resolve_language_id(args.language)

        ideas = generate_keyword_ideas(
            client=client,
            customer_id=customer_id,
            keywords=seed_keywords,
            page_url=args.url,
            geo_ids=geo_ids,
            language_id=language_id,
            network=args.network,
            max_results=args.max_ideas,
            include_adult_keywords=args.include_adult_keywords,
        )
        idea_items = ideas["items"]
        ideas_by_volume = top_items(idea_items, "avg_monthly_searches", args.max_historical_keywords)
        historical_keywords = seed_keywords + [item["text"] for item in ideas_by_volume if item.get("text")]
        historical_keywords = list(dict.fromkeys(historical_keywords))[: args.max_historical_keywords]

        historical = generate_historical_metrics(
            client=client,
            customer_id=customer_id,
            keywords=historical_keywords,
            geo_ids=geo_ids,
            language_id=language_id,
            network=args.network,
            include_average_cpc=args.include_average_cpc,
        )
        historical_items = historical["items"]

        print_json(
            {
                "ok": True,
                "research_type": "google_keyword_planner_topic_scan",
                "env_file_loaded": str(env_path) if env_path else None,
                "parameters": {
                    "topic": args.topic,
                    "seed_keywords": seed_keywords,
                    "url": args.url,
                    "customer_id": customer_id,
                    "geo_ids": geo_ids,
                    "language_id": language_id,
                    "network": args.network,
                    "max_ideas": args.max_ideas,
                    "max_historical_keywords": args.max_historical_keywords,
                    "include_average_cpc": args.include_average_cpc,
                    "include_adult_keywords": args.include_adult_keywords,
                },
                "summary": summarize(historical_items, args.summary_limit),
                "keyword_ideas": idea_items,
                "historical_metrics": historical_items,
            }
        )
        return 0
    except SystemExit:
        raise
    except Exception as exc:
        print_json(google_ads_error_to_dict(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
