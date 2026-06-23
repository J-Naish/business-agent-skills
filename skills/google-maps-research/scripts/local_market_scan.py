#!/usr/bin/env python3
"""Local market and competitor scan using Google Maps Places data."""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
from collections import Counter
from statistics import mean
from typing import Any

from google_maps_api import (
    PLACES_SEARCH_FIELD_SETS,
    field_mask,
    http_json,
    lat_lng_dict,
    place_items,
    print_json,
    require_api_key,
)


def display_text(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("text")
    if isinstance(value, str):
        return value
    return None


def place_name(place: dict[str, Any]) -> str | None:
    return display_text(place.get("displayName")) or place.get("name") or place.get("id")


def numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def analyze_places(places: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts: Counter[str] = Counter()
    primary_type_counts: Counter[str] = Counter()
    business_status_counts: Counter[str] = Counter()
    price_counts: Counter[str] = Counter()
    rating_values: list[float] = []
    user_rating_counts: list[int] = []
    with_website = 0
    with_phone = 0
    with_hours = 0

    for place in places:
        for place_type in place.get("types") or []:
            type_counts.update([str(place_type)])
        if place.get("primaryType"):
            primary_type_counts.update([str(place["primaryType"])])
        if place.get("businessStatus"):
            business_status_counts.update([str(place["businessStatus"])])
        if place.get("priceLevel"):
            price_counts.update([str(place["priceLevel"])])
        rating = numeric(place.get("rating"))
        if rating is not None:
            rating_values.append(rating)
        user_rating_count = place.get("userRatingCount")
        if isinstance(user_rating_count, int):
            user_rating_counts.append(user_rating_count)
        if place.get("websiteUri"):
            with_website += 1
        if place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"):
            with_phone += 1
        if place.get("currentOpeningHours") or place.get("regularOpeningHours"):
            with_hours += 1

    def compact(place: dict[str, Any]) -> dict[str, Any]:
        location = place.get("location") or {}
        return {
            "id": place.get("id"),
            "name": place_name(place),
            "formattedAddress": place.get("formattedAddress") or place.get("shortFormattedAddress"),
            "rating": place.get("rating"),
            "userRatingCount": place.get("userRatingCount"),
            "priceLevel": place.get("priceLevel"),
            "primaryType": place.get("primaryType"),
            "businessStatus": place.get("businessStatus"),
            "websiteUri": place.get("websiteUri"),
            "googleMapsUri": place.get("googleMapsUri"),
            "lat": location.get("latitude"),
            "lng": location.get("longitude"),
        }

    ranked_by_review_count = sorted(
        places,
        key=lambda item: (
            item.get("userRatingCount") if isinstance(item.get("userRatingCount"), int) else -1,
            item.get("rating") if isinstance(item.get("rating"), (int, float)) else -1,
        ),
        reverse=True,
    )
    ranked_by_rating = sorted(
        places,
        key=lambda item: (
            item.get("rating") if isinstance(item.get("rating"), (int, float)) else -1,
            item.get("userRatingCount") if isinstance(item.get("userRatingCount"), int) else -1,
        ),
        reverse=True,
    )

    return {
        "sample_size": len(places),
        "average_rating": round(mean(rating_values), 3) if rating_values else None,
        "average_user_rating_count": round(mean(user_rating_counts), 2) if user_rating_counts else None,
        "total_user_rating_count": sum(user_rating_counts),
        "places_with_website": with_website,
        "places_with_phone": with_phone,
        "places_with_hours": with_hours,
        "primary_types": primary_type_counts.most_common(20),
        "types": type_counts.most_common(30),
        "business_statuses": business_status_counts.most_common(10),
        "price_levels": price_counts.most_common(10),
        "top_by_review_count": [compact(place) for place in ranked_by_review_count[:10]],
        "top_by_rating": [compact(place) for place in ranked_by_rating[:10]],
    }


def build_text_body(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {
        "textQuery": args.query,
        "languageCode": args.language_code,
        "regionCode": args.region_code,
        "includedType": args.included_type,
        "pageSize": args.page_size,
    }
    if args.center:
        body["locationBias"] = {
            "circle": {"center": lat_lng_dict(args.center), "radius": args.radius}
        }
    return {key: value for key, value in body.items() if value is not None}


def build_nearby_body(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {
        "locationRestriction": {
            "circle": {"center": lat_lng_dict(args.center), "radius": args.radius}
        },
        "maxResultCount": args.page_size,
        "rankPreference": args.rank_preference,
    }
    if args.included_type:
        body["includedTypes"] = [args.included_type]
    return {key: value for key, value in body.items() if value is not None}


def run(args: argparse.Namespace) -> dict[str, Any]:
    key = require_api_key(args.env)
    fields = field_mask(args.fields, args.field_set, PLACES_SEARCH_FIELD_SETS)
    if args.mode == "text":
        url = "https://places.googleapis.com/v1/places:searchText"
        body = build_text_body(args)
        endpoint = "Places API Text Search (New)"
    else:
        if not args.center:
            raise SystemExit("--center is required for nearby mode.")
        url = "https://places.googleapis.com/v1/places:searchNearby"
        body = build_nearby_body(args)
        endpoint = "Places API Nearby Search (New)"

    pages = []
    places: list[dict[str, Any]] = []
    for page_idx in range(max(1, args.max_pages)):
        response = http_json(
            "POST",
            url,
            body=body,
            headers={"X-Goog-FieldMask": fields},
            key=key,
            key_mode="header",
        )
        data = response["data"]
        pages.append(data)
        places.extend(place_items(data))
        token = data.get("nextPageToken") if isinstance(data, dict) else None
        if args.mode != "text" or not token or page_idx + 1 >= args.max_pages:
            break
        body["pageToken"] = token

    return {
        "ok": True,
        "research_type": "google_maps_local_market_scan",
        "endpoint": endpoint,
        "parameters": {
            "mode": args.mode,
            "query": args.query,
            "included_type": args.included_type,
            "center": args.center,
            "radius": args.radius,
            "language_code": args.language_code,
            "region_code": args.region_code,
            "page_size": args.page_size,
            "max_pages": args.max_pages,
            "field_mask": fields,
        },
        "analysis": analyze_places(places),
        "places": places,
        "pages_returned": len(pages),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan local places and print market/competitor summary JSON.")
    parser.add_argument("query", help="Search text, such as 'cafe in Shibuya' or '美容クリニック'.")
    parser.add_argument("--mode", choices=["text", "nearby"], default="text")
    parser.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")
    parser.add_argument("--center", help="LAT,LNG. Bias for text mode; required for nearby mode.")
    parser.add_argument("--radius", type=float, default=1000)
    parser.add_argument("--included-type")
    parser.add_argument("--rank-preference", choices=["POPULARITY", "DISTANCE"])
    parser.add_argument("--language-code", default="ja")
    parser.add_argument("--region-code", default="JP")
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--field-set", choices=sorted(PLACES_SEARCH_FIELD_SETS), default="research")
    parser.add_argument("--fields")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print_json(run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
