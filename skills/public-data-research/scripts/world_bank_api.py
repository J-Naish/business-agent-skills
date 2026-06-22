#!/usr/bin/env python3
"""Read-only World Bank Indicators API helper for public-data research."""
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable


API_BASE = "https://api.worldbank.org/v2"
USER_AGENT = "codex-public-data-research-world-bank/1.0"
DEFAULT_SOURCE = "2"  # World Development Indicators


class WorldBankApiError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"World Bank API request failed with status {status}")
        self.status = status
        self.data = data


def parse_kv(items: list[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clean_path(path: str) -> str:
    return path if path.startswith("/") else "/" + path


def response_meta(data: Any) -> dict[str, Any]:
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    return {}


def response_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        return [item for item in data[1] if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def value_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or value.get("name") or value.get("id") or "")
    return "" if value is None else str(value)


def is_empty_cell(value: Any) -> bool:
    return value is None or value == "" or value == []


def format_cell(value: Any, limit: int = 180) -> str:
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value)
    else:
        text = str(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def contains_query(item: dict[str, Any], query: str | None, fields: Iterable[str]) -> bool:
    if not query:
        return True
    needle = query.casefold()
    haystack: list[str] = []
    for field in fields:
        value = item.get(field)
        if isinstance(value, list):
            haystack.extend(value_text(part) for part in value)
        else:
            haystack.append(value_text(value))
    return needle in " ".join(haystack).casefold()


class WorldBankClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        clean_params = {key: value for key, value in (params or {}).items() if value is not None}
        clean_params.setdefault("format", "json")
        url = self.base_url + clean_path(path) + "?" + urllib.parse.urlencode(clean_params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                text = resp.read().decode("utf-8", "replace")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace")
            try:
                data = json.loads(text) if text else {}
            except json.JSONDecodeError:
                data = {"raw": text[:2000]}
            raise WorldBankApiError(exc.code, data) from exc
        except urllib.error.URLError as exc:
            raise WorldBankApiError(None, {"error": str(exc.reason)}) from exc

    def paged(self, path: str, params: dict[str, Any], max_pages: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        all_items: list[dict[str, Any]] = []
        first_meta: dict[str, Any] = {}
        page = as_int(params.get("page"), 1)
        for _ in range(max_pages):
            page_params = dict(params)
            page_params["page"] = page
            data = self.request(path, page_params)
            meta = response_meta(data)
            if not first_meta:
                first_meta = meta
            all_items.extend(response_items(data))
            total_pages = as_int(meta.get("pages"), page)
            if page >= total_pages:
                break
            page += 1
        return first_meta, all_items


def country_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "iso2Code": item.get("iso2Code"),
        "name": item.get("name"),
        "region": value_text(item.get("region")),
        "incomeLevel": value_text(item.get("incomeLevel")),
        "lendingType": value_text(item.get("lendingType")),
        "capitalCity": item.get("capitalCity"),
        "longitude": item.get("longitude"),
        "latitude": item.get("latitude"),
    }


def source_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "code": item.get("code"),
        "name": item.get("name"),
        "lastUpdated": item.get("lastupdated"),
        "dataAvailability": item.get("dataavailability"),
        "metadataAvailability": item.get("metadataavailability"),
        "concepts": item.get("concepts"),
    }


def indicator_row(item: dict[str, Any]) -> dict[str, Any]:
    topics = item.get("topics") or []
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "unit": item.get("unit"),
        "source": value_text(item.get("source")),
        "sourceId": (item.get("source") or {}).get("id") if isinstance(item.get("source"), dict) else None,
        "topics": [value_text(topic).strip() for topic in topics if value_text(topic).strip()],
        "sourceNote": item.get("sourceNote"),
        "sourceOrganization": item.get("sourceOrganization"),
    }


def data_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "indicatorId": (item.get("indicator") or {}).get("id"),
        "indicator": value_text(item.get("indicator")),
        "countryId": (item.get("country") or {}).get("id"),
        "country": value_text(item.get("country")),
        "countryIso3Code": item.get("countryiso3code"),
        "date": item.get("date"),
        "value": item.get("value"),
        "unit": item.get("unit"),
        "obsStatus": item.get("obs_status"),
        "decimal": item.get("decimal"),
    }


def render_rows(title: str, endpoint: str, meta: dict[str, Any], rows: list[dict[str, Any]], limit: int) -> str:
    lines = [f"# {title}", ""]
    lines.append(f"- Endpoint: `{endpoint}`")
    if meta:
        lines.append(
            f"- Page info: page {meta.get('page')}, pages {meta.get('pages')}, "
            f"per_page {meta.get('per_page')}, total {meta.get('total')}"
        )
        if meta.get("lastupdated"):
            lines.append(f"- Last updated: {meta.get('lastupdated')}")
    lines.append(f"- Rows shown: {min(len(rows), limit)} of {len(rows)} fetched")
    lines.append("")
    lines.append("## Rows")
    if not rows:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        parts = [f"{key}={format_cell(value)}" for key, value in row.items() if not is_empty_cell(value)]
        lines.append(f"- {', '.join(parts)}")
    return "\n".join(lines)


def render_data(endpoint: str, meta: dict[str, Any], rows: list[dict[str, Any]], request: dict[str, Any], limit: int) -> str:
    lines = ["# World Bank Data", ""]
    lines.append(f"- Endpoint: `{endpoint}`")
    lines.append(f"- Request: `{request}`")
    if meta:
        lines.append(
            f"- Page info: page {meta.get('page')}, pages {meta.get('pages')}, "
            f"per_page {meta.get('per_page')}, total {meta.get('total')}"
        )
        if meta.get("sourceid"):
            lines.append(f"- Source ID: {meta.get('sourceid')}")
        if meta.get("lastupdated"):
            lines.append(f"- Last updated: {meta.get('lastupdated')}")
    lines.append(f"- Rows shown: {min(len(rows), limit)} of {len(rows)} fetched")
    lines.append("")
    lines.append("## Rows")
    if not rows:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        unit = f" {row['unit']}" if row.get("unit") else ""
        lines.append(
            f"- {row.get('countryIso3Code') or row.get('country')} {row.get('date')}: "
            f"{row.get('value')}{unit} | {row.get('indicator')} ({row.get('indicatorId')})"
        )
    return "\n".join(lines)


def write_csv(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


def command_check_auth(args: argparse.Namespace) -> None:
    client = WorldBankClient()
    try:
        data = client.request("/country/JPN/indicator/SP.POP.TOTL", {"mrv": 2})
        meta = response_meta(data)
        items = response_items(data)
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/v2/country/JPN/indicator/SP.POP.TOTL",
                        "ok": bool(items),
                        "status": 200,
                        "meta": meta,
                        "sample": data_row(items[0]) if items else None,
                    }
                ]
            }
        )
    except WorldBankApiError as exc:
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/v2/country/JPN/indicator/SP.POP.TOTL",
                        "ok": False,
                        "status": exc.status,
                        "error": exc.data,
                    }
                ]
            }
        )


def command_countries(args: argparse.Namespace) -> None:
    client = WorldBankClient()
    params = {"per_page": args.per_page}
    params.update(parse_kv(args.param))
    meta, items = client.paged("/country", params, args.max_pages)
    rows = [
        country_row(item)
        for item in items
        if contains_query(item, args.query, ["id", "iso2Code", "name", "region", "incomeLevel"])
    ]
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": "/v2/country", "meta": meta, "rows": rows})
    else:
        print(render_rows("World Bank Countries", "/v2/country", meta, rows, args.limit))


def command_sources(args: argparse.Namespace) -> None:
    client = WorldBankClient()
    params = {"per_page": args.per_page}
    params.update(parse_kv(args.param))
    meta, items = client.paged("/source", params, args.max_pages)
    rows = [source_row(item) for item in items if contains_query(item, args.query, ["id", "code", "name"])]
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": "/v2/source", "meta": meta, "rows": rows})
    else:
        print(render_rows("World Bank Sources", "/v2/source", meta, rows, args.limit))


def command_indicators(args: argparse.Namespace) -> None:
    client = WorldBankClient()
    if args.all_sources:
        endpoint = "/indicator"
    else:
        endpoint = f"/source/{args.source}/indicator"
    params = {"per_page": args.per_page}
    params.update(parse_kv(args.param))
    meta, items = client.paged(endpoint, params, args.max_pages)
    rows = [
        indicator_row(item)
        for item in items
        if contains_query(item, args.query, ["id", "name", "sourceNote", "sourceOrganization", "topics"])
    ]
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": f"/v2{endpoint}", "meta": meta, "query": args.query, "rows": rows})
    else:
        print(render_rows("World Bank Indicators", f"/v2{endpoint}", meta, rows, args.limit))


def command_data(args: argparse.Namespace) -> None:
    client = WorldBankClient()
    countries = ";".join(args.countries)
    endpoint = f"/country/{countries}/indicator/{args.indicator}"
    params: dict[str, Any] = {
        "date": args.date,
        "mrv": args.mrv,
        "mrnev": args.mrnev,
        "per_page": args.per_page,
        "source": args.source,
    }
    params.update(parse_kv(args.param))
    meta, items = client.paged(endpoint, params, args.max_pages)
    rows = [data_row(item) for item in items]
    request = {key: value for key, value in params.items() if value is not None}
    request["countries"] = countries
    request["indicator"] = args.indicator
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": f"/v2{endpoint}", "meta": meta, "request": request, "rows": rows})
    else:
        print(render_data(f"/v2{endpoint}", meta, rows, request, args.limit))


def command_request(args: argparse.Namespace) -> None:
    client = WorldBankClient()
    params = parse_kv(args.param)
    if args.paginate:
        meta, items = client.paged(args.path, params, args.max_pages)
        print_json({"endpoint": f"/v2{clean_path(args.path)}", "meta": meta, "items": items})
    else:
        print_json(client.request(args.path, params))


def add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print in Markdown.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--csv", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only World Bank Indicators API research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check World Bank API access. No credential is required.")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("countries", help="List or filter World Bank economies and regions.")
    p.add_argument("query", nargs="?", help="Optional local filter across code, name, region, and income level.")
    p.add_argument("--per-page", type=int, default=300)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    add_output_options(p)
    p.set_defaults(func=command_countries)

    p = sub.add_parser("sources", help="List or filter World Bank data sources.")
    p.add_argument("query", nargs="?", help="Optional local filter across source id, code, and name.")
    p.add_argument("--per-page", type=int, default=100)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    add_output_options(p)
    p.set_defaults(func=command_sources)

    p = sub.add_parser("indicators", help="Search indicators, defaulting to source 2 World Development Indicators.")
    p.add_argument("query", nargs="?", help="Optional local filter across id, name, topics, and notes.")
    p.add_argument("--source", default=DEFAULT_SOURCE, help="World Bank source id. Default 2 is WDI.")
    p.add_argument("--all-sources", action="store_true", help="Search the global indicator catalog instead of one source.")
    p.add_argument("--per-page", type=int, default=20000)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    add_output_options(p)
    p.set_defaults(func=command_indicators)

    p = sub.add_parser("data", help="Fetch country-level time series for an indicator.")
    p.add_argument("indicator", help="Indicator code, e.g. SP.POP.TOTL or NY.GDP.MKTP.CD.")
    p.add_argument("countries", nargs="+", help="Country/economy codes, e.g. JPN USA or JPN;USA.")
    p.add_argument("--date", help="Year or range such as 2020 or 2010:2024.")
    p.add_argument("--mrv", type=int, help="Most recent N values.")
    p.add_argument("--mrnev", type=int, help="Most recent N non-empty values.")
    p.add_argument("--source", default=DEFAULT_SOURCE)
    p.add_argument("--per-page", type=int, default=20000)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    add_output_options(p)
    p.set_defaults(func=command_data)

    p = sub.add_parser("request", help="Call a read-only World Bank API path directly.")
    p.add_argument("path", help="Path under /v2, e.g. /country/JPN/indicator/SP.POP.TOTL.")
    p.add_argument("--param", action="append", help="Parameter as KEY=VALUE.")
    p.add_argument("--paginate", action="store_true")
    p.add_argument("--max-pages", type=int, default=1)
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except WorldBankApiError as exc:
        print_json({"ok": False, "status": exc.status, "error": exc.data})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
