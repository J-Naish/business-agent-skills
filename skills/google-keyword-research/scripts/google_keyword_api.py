#!/usr/bin/env python3
"""Read-only Google Ads Keyword Planner helper for research workflows.

Loads Google Ads API credentials from environment variables or a nearby .env file.
Credential values are never printed.
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-ads",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


USER_AGENT = "codex-google-keyword-research/1.0.0"
REQUIRED_ENV = [
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_CUSTOMER_ID",
]
OPTIONAL_ENV = ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]

COMMON_GEO_TARGETS = {
    "AU": "2036",
    "BR": "2076",
    "CA": "2124",
    "DE": "2276",
    "FR": "2250",
    "GB": "2826",
    "ID": "2360",
    "IN": "2356",
    "IT": "2380",
    "JP": "2392",
    "KR": "2410",
    "MX": "2484",
    "SG": "2702",
    "TH": "2764",
    "TW": "2158",
    "US": "2840",
    "VN": "2704",
}

COMMON_LANGUAGES = {
    "ar": "1019",
    "de": "1001",
    "en": "1000",
    "es": "1003",
    "fr": "1002",
    "hi": "1023",
    "id": "1025",
    "it": "1004",
    "ja": "1011",
    "ko": "1012",
    "pt": "1014",
    "th": "1044",
    "vi": "1040",
    "zh": "1017",
}

MONTH_NUMBERS = {
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
}


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def print_jsonl(items: Iterable[Any]) -> None:
    for item in items:
        print(json.dumps(item, ensure_ascii=False, sort_keys=False))


def fail_json(message: str, **extra: Any) -> None:
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print_json(payload)
    raise SystemExit(1)


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
    path: Path | None = Path(env_path).expanduser() if env_path else None
    if not path:
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


def clean_customer_id(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = "".join(ch for ch in value if ch.isdigit())
    return cleaned or None


def require_env() -> dict[str, str]:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        fail_json(
            "missing_google_ads_credentials",
            missing=missing,
            required=REQUIRED_ENV,
            optional=OPTIONAL_ENV,
        )
    values = {name: os.environ[name] for name in REQUIRED_ENV}
    for name in OPTIONAL_ENV:
        if os.environ.get(name):
            values[name] = os.environ[name]
    return values


def import_google_ads_client():
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError:
        fail_json(
            "missing_python_dependency",
            package="google-ads",
            install="uv run skills/google-keyword-research/scripts/google_keyword_api.py --help",
            plain_python_install="python3 -m pip install google-ads python-dotenv",
        )
    return GoogleAdsClient


def load_google_ads_client(env_path: str | None = None):
    load_env(env_path)
    values = require_env()
    config: dict[str, Any] = {
        "developer_token": values["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": values["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": values["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": values["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    login_customer_id = clean_customer_id(values.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"))
    if login_customer_id:
        config["login_customer_id"] = login_customer_id
    client_cls = import_google_ads_client()
    return client_cls.load_from_dict(config)


def default_customer_id() -> str:
    customer_id = clean_customer_id(os.environ.get("GOOGLE_ADS_CUSTOMER_ID"))
    if not customer_id:
        fail_json("missing_customer_id", missing=["GOOGLE_ADS_CUSTOMER_ID"])
    return customer_id


def customer_id_from_args(args: argparse.Namespace) -> str:
    return clean_customer_id(getattr(args, "customer_id", None)) or default_customer_id()


def enum_name(value: Any) -> str | None:
    if value is None:
        return None
    name = getattr(value, "name", None)
    if name:
        return str(name)
    return str(value)


def month_to_dict(volume: Any) -> dict[str, Any]:
    month_name = enum_name(getattr(volume, "month", None))
    month_number = MONTH_NUMBERS.get(month_name or "")
    year = int(getattr(volume, "year", 0) or 0)
    iso_month = f"{year:04d}-{month_number:02d}" if year and month_number else None
    return {
        "year": year or None,
        "month": month_name,
        "month_number": month_number,
        "iso_month": iso_month,
        "monthly_searches": int(getattr(volume, "monthly_searches", 0) or 0),
    }


def micros_to_units(value: Any) -> float | None:
    if value is None:
        return None
    value_int = int(value or 0)
    if value_int == 0:
        return None
    return round(value_int / 1_000_000, 6)


def metrics_to_dict(metrics: Any) -> dict[str, Any] | None:
    if not metrics:
        return None
    monthly = [month_to_dict(volume) for volume in getattr(metrics, "monthly_search_volumes", [])]
    monthly.sort(key=lambda item: (item.get("year") or 0, item.get("month_number") or 0), reverse=True)
    low_bid = int(getattr(metrics, "low_top_of_page_bid_micros", 0) or 0)
    high_bid = int(getattr(metrics, "high_top_of_page_bid_micros", 0) or 0)
    average_cpc = int(getattr(metrics, "average_cpc_micros", 0) or 0)
    return {
        "avg_monthly_searches": int(getattr(metrics, "avg_monthly_searches", 0) or 0),
        "competition": enum_name(getattr(metrics, "competition", None)),
        "competition_index": int(getattr(metrics, "competition_index", 0) or 0),
        "low_top_of_page_bid_micros": low_bid or None,
        "low_top_of_page_bid": micros_to_units(low_bid),
        "high_top_of_page_bid_micros": high_bid or None,
        "high_top_of_page_bid": micros_to_units(high_bid),
        "average_cpc_micros": average_cpc or None,
        "average_cpc": micros_to_units(average_cpc),
        "monthly_search_volumes": monthly,
    }


def clean_resource_id(value: str) -> str:
    return value.rsplit("/", 1)[-1].strip()


def resolve_geo_ids(values: list[str] | None) -> list[str]:
    inputs = values or ["JP"]
    resolved: list[str] = []
    for raw in inputs:
        value = raw.strip()
        if not value:
            continue
        upper = value.upper()
        if upper in COMMON_GEO_TARGETS:
            resolved.append(COMMON_GEO_TARGETS[upper])
        else:
            resolved.append(clean_resource_id(value))
    return list(dict.fromkeys(resolved))


def resolve_language_id(value: str | None) -> str:
    raw = (value or "ja").strip()
    lower = raw.lower()
    if lower in COMMON_LANGUAGES:
        return COMMON_LANGUAGES[lower]
    return clean_resource_id(raw)


def resolve_network(client: Any, value: str):
    name = value.upper().strip()
    aliases = {
        "SEARCH": "GOOGLE_SEARCH",
        "GOOGLE": "GOOGLE_SEARCH",
        "SEARCH_AND_PARTNERS": "GOOGLE_SEARCH_AND_PARTNERS",
        "PARTNERS": "GOOGLE_SEARCH_AND_PARTNERS",
    }
    name = aliases.get(name, name)
    try:
        return getattr(client.enums.KeywordPlanNetworkEnum, name), name
    except AttributeError:
        fail_json(
            "invalid_keyword_plan_network",
            value=value,
            allowed=["GOOGLE_SEARCH", "GOOGLE_SEARCH_AND_PARTNERS"],
        )


def keyword_request_context(client: Any, args: argparse.Namespace) -> dict[str, Any]:
    google_ads_service = client.get_service("GoogleAdsService")
    geo_ids = resolve_geo_ids(args.geo)
    language_id = resolve_language_id(args.language)
    network_value, network_name = resolve_network(client, args.network)
    return {
        "google_ads_service": google_ads_service,
        "geo_ids": geo_ids,
        "geo_target_constants": [
            google_ads_service.geo_target_constant_path(geo_id) for geo_id in geo_ids
        ],
        "language_id": language_id,
        "language": google_ads_service.language_constant_path(language_id),
        "network_value": network_value,
        "network_name": network_name,
    }


def collect_keywords(args: argparse.Namespace) -> list[str]:
    keywords: list[str] = []
    for value in getattr(args, "keywords", []) or []:
        keywords.append(value)
    for value in getattr(args, "keyword", []) or []:
        keywords.append(value)
    cleaned = [item.strip() for item in keywords if item and item.strip()]
    return list(dict.fromkeys(cleaned))


def idea_to_dict(idea: Any) -> dict[str, Any]:
    return {
        "text": getattr(idea, "text", None),
        "metrics": metrics_to_dict(getattr(idea, "keyword_idea_metrics", None)),
    }


def historical_result_to_dict(result: Any) -> dict[str, Any]:
    return {
        "text": getattr(result, "text", None),
        "close_variants": list(getattr(result, "close_variants", []) or []),
        "metrics": metrics_to_dict(getattr(result, "keyword_metrics", None)),
    }


def google_ads_error_to_dict(exc: Exception) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }
    request_id = getattr(exc, "request_id", None)
    if request_id:
        payload["request_id"] = request_id
    failure = getattr(exc, "failure", None)
    errors = []
    for error in getattr(failure, "errors", []) or []:
        field_path = []
        location = getattr(error, "location", None)
        for element in getattr(location, "field_path_elements", []) or []:
            field_name = getattr(element, "field_name", None)
            if field_name:
                field_path.append(field_name)
        errors.append(
            {
                "message": getattr(error, "message", None),
                "code": enum_name(getattr(error, "error_code", None)),
                "field_path": ".".join(field_path) if field_path else None,
            }
        )
    if errors:
        payload["errors"] = errors
    return payload


def generate_keyword_ideas(
    client: Any,
    customer_id: str,
    keywords: list[str],
    page_url: str | None,
    geo_ids: list[str],
    language_id: str,
    network: str = "GOOGLE_SEARCH",
    max_results: int = 50,
    include_adult_keywords: bool = False,
) -> dict[str, Any]:
    if not keywords and not page_url:
        fail_json("missing_seed", detail="Provide at least one keyword or --url.")

    service = client.get_service("KeywordPlanIdeaService")
    google_ads_service = client.get_service("GoogleAdsService")
    network_value, network_name = resolve_network(client, network)
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = google_ads_service.language_constant_path(language_id)
    request.geo_target_constants = [
        google_ads_service.geo_target_constant_path(geo_id) for geo_id in geo_ids
    ]
    request.include_adult_keywords = include_adult_keywords
    request.keyword_plan_network = network_value
    if keywords and page_url:
        request.keyword_and_url_seed.url = page_url
        request.keyword_and_url_seed.keywords.extend(keywords)
        seed_type = "keyword_and_url_seed"
    elif keywords:
        request.keyword_seed.keywords.extend(keywords)
        seed_type = "keyword_seed"
    else:
        request.url_seed.url = page_url
        seed_type = "url_seed"

    items: list[dict[str, Any]] = []
    for idea in service.generate_keyword_ideas(request=request):
        items.append(idea_to_dict(idea))
        if len(items) >= max_results:
            break

    return {
        "endpoint": "KeywordPlanIdeaService.GenerateKeywordIdeas",
        "customer_id": customer_id,
        "seed": {"type": seed_type, "keywords": keywords, "url": page_url},
        "geo_ids": geo_ids,
        "geo_target_constants": list(request.geo_target_constants),
        "language_id": language_id,
        "language": request.language,
        "network": network_name,
        "include_adult_keywords": include_adult_keywords,
        "max_results": max_results,
        "items": items,
    }


def generate_historical_metrics(
    client: Any,
    customer_id: str,
    keywords: list[str],
    geo_ids: list[str],
    language_id: str,
    network: str = "GOOGLE_SEARCH",
    include_average_cpc: bool = False,
) -> dict[str, Any]:
    if not keywords:
        fail_json("missing_keywords", detail="Provide at least one keyword.")

    service = client.get_service("KeywordPlanIdeaService")
    google_ads_service = client.get_service("GoogleAdsService")
    network_value, network_name = resolve_network(client, network)
    request = client.get_type("GenerateKeywordHistoricalMetricsRequest")
    request.customer_id = customer_id
    request.keywords = keywords
    request.geo_target_constants.extend(
        [google_ads_service.geo_target_constant_path(geo_id) for geo_id in geo_ids]
    )
    request.keyword_plan_network = network_value
    request.language = google_ads_service.language_constant_path(language_id)
    if include_average_cpc:
        request.historical_metrics_options.include_average_cpc = True

    response = service.generate_keyword_historical_metrics(request=request)
    return {
        "endpoint": "KeywordPlanIdeaService.GenerateKeywordHistoricalMetrics",
        "customer_id": customer_id,
        "keywords": keywords,
        "geo_ids": geo_ids,
        "geo_target_constants": list(request.geo_target_constants),
        "language_id": language_id,
        "language": request.language,
        "network": network_name,
        "include_average_cpc": include_average_cpc,
        "items": [historical_result_to_dict(result) for result in response.results],
    }


def command_check_auth(args: argparse.Namespace) -> None:
    env_path = load_env(args.env)
    client = load_google_ads_client(args.env)
    customer_id = customer_id_from_args(args)
    checks: list[dict[str, Any]] = []

    customer_service = client.get_service("CustomerService")
    response = customer_service.list_accessible_customers()
    resource_names = list(response.resource_names)
    checks.append(
        {
            "endpoint": "CustomerService.ListAccessibleCustomers",
            "ok": True,
            "accessible_customer_count": len(resource_names),
            "accessible_customers_sample": resource_names[:20],
        }
    )

    google_ads_service = client.get_service("GoogleAdsService")
    query = (
        "SELECT customer.id, customer.descriptive_name, customer.currency_code, "
        "customer.time_zone FROM customer LIMIT 1"
    )
    rows = list(google_ads_service.search(customer_id=customer_id, query=query))
    checks.append(
        {
            "endpoint": "GoogleAdsService.Search",
            "ok": True,
            "customer_id": customer_id,
            "rows": [
                {
                    "id": str(row.customer.id),
                    "descriptive_name": row.customer.descriptive_name,
                    "currency_code": row.customer.currency_code,
                    "time_zone": row.customer.time_zone,
                }
                for row in rows
            ],
        }
    )

    print_json(
        {
            "ok": True,
            "auth": "oauth_refresh_token",
            "env_file_loaded": str(env_path) if env_path else None,
            "login_customer_id": clean_customer_id(os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")),
            "customer_id": customer_id,
            "checks": checks,
        }
    )


def command_ideas(args: argparse.Namespace) -> None:
    load_env(args.env)
    client = load_google_ads_client(args.env)
    customer_id = customer_id_from_args(args)
    keywords = collect_keywords(args)
    geo_ids = resolve_geo_ids(args.geo)
    language_id = resolve_language_id(args.language)
    result = generate_keyword_ideas(
        client=client,
        customer_id=customer_id,
        keywords=keywords,
        page_url=args.url,
        geo_ids=geo_ids,
        language_id=language_id,
        network=args.network,
        max_results=args.max_results,
        include_adult_keywords=args.include_adult_keywords,
    )
    if args.jsonl:
        print_jsonl(result["items"])
    else:
        print_json(result)


def command_historical(args: argparse.Namespace) -> None:
    load_env(args.env)
    client = load_google_ads_client(args.env)
    customer_id = customer_id_from_args(args)
    keywords = collect_keywords(args)
    geo_ids = resolve_geo_ids(args.geo)
    language_id = resolve_language_id(args.language)
    result = generate_historical_metrics(
        client=client,
        customer_id=customer_id,
        keywords=keywords,
        geo_ids=geo_ids,
        language_id=language_id,
        network=args.network,
        include_average_cpc=args.include_average_cpc,
    )
    if args.jsonl:
        print_jsonl(result["items"])
    else:
        print_json(result)


def escape_gaql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def command_geo_targets(args: argparse.Namespace) -> None:
    load_env(args.env)
    client = load_google_ads_client(args.env)
    customer_id = customer_id_from_args(args)
    service = client.get_service("GoogleAdsService")
    query_text = escape_gaql_string(args.query.strip())
    where = (
        "geo_target_constant.status = ENABLED "
        f"AND (geo_target_constant.name LIKE '%{query_text}%' "
        f"OR geo_target_constant.country_code = '{query_text.upper()}')"
    )
    query = (
        "SELECT geo_target_constant.resource_name, geo_target_constant.id, "
        "geo_target_constant.name, geo_target_constant.country_code, "
        "geo_target_constant.target_type, geo_target_constant.status "
        f"FROM geo_target_constant WHERE {where} "
        f"ORDER BY geo_target_constant.target_type, geo_target_constant.name LIMIT {args.max_results}"
    )
    rows = service.search(customer_id=customer_id, query=query)
    items = [
        {
            "resource_name": row.geo_target_constant.resource_name,
            "id": str(row.geo_target_constant.id),
            "name": row.geo_target_constant.name,
            "country_code": row.geo_target_constant.country_code,
            "target_type": row.geo_target_constant.target_type,
            "status": enum_name(row.geo_target_constant.status),
        }
        for row in rows
    ]
    print_json(
        {
            "endpoint": "GoogleAdsService.Search",
            "resource": "geo_target_constant",
            "query_text": args.query,
            "customer_id": customer_id,
            "items": items,
        }
    )


def command_languages(args: argparse.Namespace) -> None:
    load_env(args.env)
    client = load_google_ads_client(args.env)
    customer_id = customer_id_from_args(args)
    service = client.get_service("GoogleAdsService")
    if args.query:
        query_text = escape_gaql_string(args.query.strip())
        where = (
            "language_constant.targetable = true "
            f"AND (language_constant.name LIKE '%{query_text}%' "
            f"OR language_constant.code = '{query_text.lower()}')"
        )
    else:
        where = "language_constant.targetable = true"
    query = (
        "SELECT language_constant.resource_name, language_constant.id, "
        "language_constant.code, language_constant.name, language_constant.targetable "
        f"FROM language_constant WHERE {where} "
        f"ORDER BY language_constant.name LIMIT {args.max_results}"
    )
    rows = service.search(customer_id=customer_id, query=query)
    items = [
        {
            "resource_name": row.language_constant.resource_name,
            "id": str(row.language_constant.id),
            "code": row.language_constant.code,
            "name": row.language_constant.name,
            "targetable": bool(row.language_constant.targetable),
        }
        for row in rows
    ]
    print_json(
        {
            "endpoint": "GoogleAdsService.Search",
            "resource": "language_constant",
            "query_text": args.query,
            "customer_id": customer_id,
            "items": items,
        }
    )


def command_gaql(args: argparse.Namespace) -> None:
    load_env(args.env)
    client = load_google_ads_client(args.env)
    customer_id = customer_id_from_args(args)
    query = args.query
    if args.query_file:
        query = Path(args.query_file).expanduser().read_text(encoding="utf-8")
    if not query:
        fail_json("missing_gaql_query", detail="Provide QUERY or --query-file.")
    service = client.get_service("GoogleAdsService")
    try:
        from google.protobuf.json_format import MessageToDict
    except ImportError:
        fail_json("missing_python_dependency", package="protobuf")
    rows = []
    for idx, row in enumerate(service.search(customer_id=customer_id, query=query)):
        if idx >= args.max_rows:
            break
        rows.append(MessageToDict(row._pb, preserving_proto_field_name=True))
    if args.jsonl:
        print_jsonl(rows)
    else:
        print_json(
            {
                "endpoint": "GoogleAdsService.Search",
                "customer_id": customer_id,
                "max_rows": args.max_rows,
                "query": query,
                "items": rows,
            }
        )


def add_common_keyword_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")
    parser.add_argument("--customer-id", help="Google Ads customer ID. Defaults to GOOGLE_ADS_CUSTOMER_ID.")
    parser.add_argument("--geo", action="append", help="Geo target ID/resource or common country code. Repeatable. Default: JP.")
    parser.add_argument("--language", default="ja", help="Language ID/resource or common code. Default: ja.")
    parser.add_argument(
        "--network",
        default="GOOGLE_SEARCH",
        help="GOOGLE_SEARCH or GOOGLE_SEARCH_AND_PARTNERS. Default: GOOGLE_SEARCH.",
    )
    parser.add_argument("--keyword", action="append", help="Seed keyword. Repeatable.")
    parser.add_argument("--jsonl", action="store_true", help="Print result items as JSON Lines.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Google Ads Keyword Planner research helper.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check-auth", help="Validate Google Ads credentials and customer access.")
    check.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")
    check.add_argument("--customer-id", help="Google Ads customer ID. Defaults to GOOGLE_ADS_CUSTOMER_ID.")
    check.set_defaults(func=command_check_auth)

    ideas = subparsers.add_parser("ideas", help="Generate keyword ideas from keywords and/or a page URL.")
    add_common_keyword_args(ideas)
    ideas.add_argument("keywords", nargs="*", help="Seed keywords.")
    ideas.add_argument("--url", help="Page URL seed.")
    ideas.add_argument("--max-results", type=int, default=50, help="Maximum ideas to print. Default: 50.")
    ideas.add_argument("--include-adult-keywords", action="store_true")
    ideas.set_defaults(func=command_ideas)

    historical = subparsers.add_parser("historical", help="Generate historical metrics for exact keywords.")
    add_common_keyword_args(historical)
    historical.add_argument("keywords", nargs="*", help="Keywords to inspect.")
    historical.add_argument("--include-average-cpc", action="store_true", help="Request average CPC when available.")
    historical.set_defaults(func=command_historical)

    geo = subparsers.add_parser("geo-targets", help="Search geo target constants by name or country code.")
    geo.add_argument("query", help="Geo name or country code, e.g. Japan, Tokyo, JP.")
    geo.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")
    geo.add_argument("--customer-id", help="Google Ads customer ID. Defaults to GOOGLE_ADS_CUSTOMER_ID.")
    geo.add_argument("--max-results", type=int, default=25)
    geo.set_defaults(func=command_geo_targets)

    languages = subparsers.add_parser("languages", help="Search language constants by name or code.")
    languages.add_argument("query", nargs="?", help="Language name or code, e.g. Japanese, ja.")
    languages.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")
    languages.add_argument("--customer-id", help="Google Ads customer ID. Defaults to GOOGLE_ADS_CUSTOMER_ID.")
    languages.add_argument("--max-results", type=int, default=50)
    languages.set_defaults(func=command_languages)

    gaql = subparsers.add_parser("gaql", help="Run a read-only GAQL query and print rows.")
    gaql.add_argument("query", nargs="?", help="GAQL query string.")
    gaql.add_argument("--query-file", help="Read GAQL from a file.")
    gaql.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")
    gaql.add_argument("--customer-id", help="Google Ads customer ID. Defaults to GOOGLE_ADS_CUSTOMER_ID.")
    gaql.add_argument("--max-rows", type=int, default=100)
    gaql.add_argument("--jsonl", action="store_true", help="Print rows as JSON Lines.")
    gaql.set_defaults(func=command_gaql)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except SystemExit:
        raise
    except Exception as exc:
        print_json(google_ads_error_to_dict(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
