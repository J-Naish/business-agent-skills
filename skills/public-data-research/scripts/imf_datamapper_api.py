#!/usr/bin/env python3
"""Read-only IMF DataMapper API helper for public-data research."""
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable


API_BASE = "https://www.imf.org/external/datamapper/api/v2"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


class ImfApiError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"IMF DataMapper API request failed with status {status}")
        self.status = status
        self.data = data


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def clean_path(path: str) -> str:
    return path if path.startswith("/") else "/" + path


def split_csv(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {part.strip().upper() for part in value.split(",") if part.strip()}


def text_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("label") or value.get("name") or value.get("id") or "")
    return "" if value is None else str(value)


def format_cell(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def contains_query(item: dict[str, Any], query: str | None, fields: Iterable[str]) -> bool:
    if not query:
        return True
    needle = query.casefold()
    haystack = " ".join(text_value(item.get(field)) for field in fields)
    return needle in haystack.casefold()


class ImfClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        clean_params = {key: value for key, value in (params or {}).items() if value is not None}
        url = self.base_url + clean_path(path)
        if clean_params:
            url += "?" + urllib.parse.urlencode(clean_params)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.imf.org/external/datamapper/",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                text = resp.read().decode("utf-8", "replace")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace")
            if exc.code == 403:
                return self.request_with_curl(url)
            try:
                data = json.loads(text) if text else {}
            except json.JSONDecodeError:
                data = {"raw": text[:2000]}
            raise ImfApiError(exc.code, data) from exc
        except urllib.error.URLError as exc:
            raise ImfApiError(None, {"error": str(exc.reason)}) from exc

    def request_with_curl(self, url: str) -> Any:
        curl = shutil.which("curl")
        if not curl:
            raise ImfApiError(403, {"error": "IMF blocked urllib request and curl is not available."})
        result = subprocess.run(
            [curl, "-fsSL", url],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise ImfApiError(403, {"error": result.stderr.strip() or "curl request failed"})
        try:
            return json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError as exc:
            raise ImfApiError(None, {"error": "Invalid JSON response", "raw": result.stdout[:2000]}) from exc


def catalog_items(data: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    container = data.get(kind)
    if not isinstance(container, dict):
        return []
    rows: list[dict[str, Any]] = []
    for code, value in container.items():
        if not isinstance(value, dict):
            value = {"label": value}
        row = {"id": code}
        row.update(value)
        rows.append(row)
    return rows


def normalize_catalog_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "label": row.get("label"),
        "description": row.get("description"),
        "source": row.get("source"),
        "unit": row.get("unit"),
        "dataset": row.get("dataset"),
        "projectionYear": row.get("projection-year"),
        "lastModified": row.get("last-modified"),
    }


def flatten_data(data: dict[str, Any], entities: set[str] | None, periods: set[str] | None) -> list[dict[str, Any]]:
    indicators = data.get("indicators") if isinstance(data.get("indicators"), dict) else {}
    values = data.get("values") if isinstance(data.get("values"), dict) else {}
    rows: list[dict[str, Any]] = []
    for indicator_id, entity_values in values.items():
        if not isinstance(entity_values, dict):
            continue
        indicator_meta = indicators.get(indicator_id, {}) if isinstance(indicators, dict) else {}
        if not isinstance(indicator_meta, dict):
            indicator_meta = {}
        for entity_id, time_values in entity_values.items():
            entity_id_text = str(entity_id).upper()
            if entities and entity_id_text not in entities:
                continue
            if not isinstance(time_values, dict):
                continue
            for period, value in sorted(time_values.items(), key=lambda item: str(item[0])):
                if periods and str(period) not in periods:
                    continue
                rows.append(
                    {
                        "indicatorId": indicator_id,
                        "indicator": indicator_meta.get("label"),
                        "entityId": entity_id,
                        "period": period,
                        "value": value,
                        "unit": indicator_meta.get("unit"),
                        "source": indicator_meta.get("source"),
                        "dataset": indicator_meta.get("dataset"),
                        "lastModified": indicator_meta.get("last-modified"),
                    }
                )
    return rows


def render_rows(title: str, endpoint: str, rows: list[dict[str, Any]], limit: int) -> str:
    lines = [f"# {title}", ""]
    lines.append(f"- Endpoint: `{endpoint}`")
    lines.append(f"- Rows shown: {min(len(rows), limit)} of {len(rows)} fetched")
    lines.append("")
    lines.append("## Rows")
    if not rows:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        parts = [f"{key}={format_cell(value)}" for key, value in row.items() if value not in (None, "", [])]
        lines.append(f"- {', '.join(parts)}")
    return "\n".join(lines)


def render_data(endpoint: str, rows: list[dict[str, Any]], request: dict[str, Any], limit: int) -> str:
    lines = ["# IMF DataMapper Data", ""]
    lines.append(f"- Endpoint: `{endpoint}`")
    lines.append(f"- Request: `{request}`")
    lines.append(f"- Rows shown: {min(len(rows), limit)} of {len(rows)} fetched after local filtering")
    lines.append("")
    lines.append("## Rows")
    if not rows:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        unit = f" {row['unit']}" if row.get("unit") else ""
        lines.append(
            f"- {row.get('entityId')} {row.get('period')}: {row.get('value')}{unit} | "
            f"{row.get('indicator')} ({row.get('indicatorId')})"
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
    client = ImfClient()
    try:
        data = client.request("/indicators")
        rows = catalog_items(data, "indicators")
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/external/datamapper/api/v2/indicators",
                        "ok": bool(rows),
                        "status": 200,
                        "sample": normalize_catalog_row(rows[0]) if rows else None,
                    }
                ]
            }
        )
    except ImfApiError as exc:
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/external/datamapper/api/v2/indicators",
                        "ok": False,
                        "status": exc.status,
                        "error": exc.data,
                    }
                ]
            }
        )


def command_catalog(args: argparse.Namespace) -> None:
    client = ImfClient()
    data = client.request(f"/{args.kind}")
    rows = [
        normalize_catalog_row(item)
        for item in catalog_items(data, args.kind)
        if contains_query(item, args.query, ["id", "label", "description", "source", "unit", "dataset"])
    ]
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": f"/external/datamapper/api/v2/{args.kind}", "query": args.query, "rows": rows})
    else:
        print(render_rows(f"IMF DataMapper {args.kind.title()}", f"/external/datamapper/api/v2/{args.kind}", rows, args.limit))


def command_data(args: argparse.Namespace) -> None:
    client = ImfClient()
    params = {}
    if args.periods:
        params["periods"] = args.periods
    data = client.request(f"/{args.indicator}", params)
    entities = {entity.upper() for entity in args.entities} if args.entities else None
    periods = split_csv(args.periods)
    rows = flatten_data(data, entities, periods)
    request = {"indicator": args.indicator, "entities": args.entities, "periods": args.periods}
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": f"/external/datamapper/api/v2/{args.indicator}", "request": request, "rows": rows})
    else:
        print(render_data(f"/external/datamapper/api/v2/{args.indicator}", rows, request, args.limit))


def command_request(args: argparse.Namespace) -> None:
    client = ImfClient()
    params = {}
    for item in args.param or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    print_json(client.request(args.path, params))


def add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print in Markdown.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--csv", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only IMF DataMapper API research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check IMF DataMapper access. No credential is required.")
    p.set_defaults(func=command_check_auth)

    for kind in ["indicators", "countries", "regions", "groups"]:
        p = sub.add_parser(kind, help=f"List or filter IMF DataMapper {kind}.")
        p.add_argument("query", nargs="?", help="Optional local filter.")
        p.set_defaults(func=command_catalog, kind=kind)
        add_output_options(p)

    p = sub.add_parser("data", help="Fetch and locally filter IMF DataMapper time series.")
    p.add_argument("indicator", help="Indicator code, e.g. NGDP_RPCH or PCPIPCH.")
    p.add_argument("entities", nargs="*", help="Optional country/region/group codes, e.g. JPN USA WEOWORLD.")
    p.add_argument("--periods", help="Comma-separated years, e.g. 2023,2024,2025.")
    add_output_options(p)
    p.set_defaults(func=command_data)

    p = sub.add_parser("request", help="Call a read-only IMF DataMapper path directly.")
    p.add_argument("path", help="Path under /api/v2, e.g. /indicators or /NGDP_RPCH.")
    p.add_argument("--param", action="append", help="Parameter as KEY=VALUE.")
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ImfApiError as exc:
        print_json({"ok": False, "status": exc.status, "error": exc.data})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
