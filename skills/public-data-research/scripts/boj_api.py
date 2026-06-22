#!/usr/bin/env python3
"""Read-only Bank of Japan Time-Series Data Search API helper."""
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
from typing import Any


API_BASE = "https://www.stat-search.boj.or.jp/api/v1"
USER_AGENT = "codex-public-data-research-boj/1.0"


class BojApiError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"BOJ API request failed with status {status}")
        self.status = status
        self.data = data


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def parse_kv(items: list[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def clean_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip("/")
    allowed = {"getDataCode", "getDataLayer", "getMetadata"}
    if endpoint not in allowed:
        raise SystemExit(f"Unsupported BOJ endpoint: {endpoint}")
    return endpoint


class BojClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")

    def request_text(self, endpoint: str, params: dict[str, Any]) -> str:
        clean_params = {key: value for key, value in params.items() if value is not None}
        url = self.base_url + "/" + clean_endpoint(endpoint) + "?" + urllib.parse.urlencode(clean_params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read().decode("utf-8-sig", "replace")
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8-sig", "replace")
            try:
                data = json.loads(text) if text else {}
            except json.JSONDecodeError:
                data = {"raw": text[:2000]}
            raise BojApiError(exc.code, data) from exc
        except urllib.error.URLError as exc:
            raise BojApiError(None, {"error": str(exc.reason)}) from exc

    def request_json(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        params = dict(params)
        params["format"] = "json"
        text = self.request_text(endpoint, params)
        try:
            data = json.loads(text) if text else {}
        except json.JSONDecodeError as exc:
            raise BojApiError(None, {"error": "Invalid JSON response", "raw": text[:2000]}) from exc
        return data if isinstance(data, dict) else {"data": data}


def flatten_data_code(data: dict[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for series in data.get("RESULTSET") or []:
        if not isinstance(series, dict):
            continue
        values = series.get("VALUES") if isinstance(series.get("VALUES"), dict) else {}
        dates = values.get("SURVEY_DATES") or []
        obs_values = values.get("VALUES") or []
        for idx, date in enumerate(dates):
            value = obs_values[idx] if idx < len(obs_values) else None
            rows.append(
                {
                    "seriesCode": series.get("SERIES_CODE"),
                    "nameJ": series.get("NAME_OF_TIME_SERIES_J"),
                    "nameE": series.get("NAME_OF_TIME_SERIES_E"),
                    "unitJ": series.get("UNIT_J"),
                    "unitE": series.get("UNIT_E"),
                    "frequency": series.get("FREQUENCY"),
                    "categoryJ": series.get("CATEGORY_J"),
                    "categoryE": series.get("CATEGORY_E"),
                    "lastUpdate": series.get("LAST_UPDATE"),
                    "surveyDate": date,
                    "value": value,
                }
            )
            if limit and len(rows) >= limit:
                return rows
    return rows


def render_data(endpoint: str, raw: dict[str, Any], rows: list[dict[str, Any]], request: dict[str, Any], limit: int) -> str:
    lines = ["# BOJ Time-Series Data", ""]
    lines.append(f"- Endpoint: `{endpoint}`")
    lines.append(f"- Status: {raw.get('STATUS')} {raw.get('MESSAGE') or ''}".rstrip())
    lines.append(f"- Date: {raw.get('DATE')}")
    lines.append(f"- Request: `{request}`")
    lines.append(f"- Rows shown: {min(len(rows), limit)}")
    if raw.get("NEXTPOSITION"):
        lines.append(f"- Next position: {raw.get('NEXTPOSITION')}")
    lines.append("")
    lines.append("## Rows")
    if not rows:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        unit = f" {row.get('unitJ') or row.get('unitE')}" if row.get("unitJ") or row.get("unitE") else ""
        lines.append(
            f"- {row.get('seriesCode')} {row.get('surveyDate')}: {row.get('value')}{unit} | "
            f"{row.get('nameJ') or row.get('nameE')}"
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
    client = BojClient()
    params = {"db": "FM01", "code": "STRDCLUCON", "startDate": "202606", "endDate": "202606", "lang": "jp"}
    try:
        data = client.request_json("getDataCode", params)
        rows = flatten_data_code(data, limit=3)
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/api/v1/getDataCode",
                        "ok": data.get("STATUS") == 200,
                        "status": data.get("STATUS"),
                        "message": data.get("MESSAGE"),
                        "sampleRows": rows,
                    }
                ]
            }
        )
    except BojApiError as exc:
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/api/v1/getDataCode",
                        "ok": False,
                        "status": exc.status,
                        "error": exc.data,
                    }
                ]
            }
        )


def command_data_code(args: argparse.Namespace) -> None:
    client = BojClient()
    params: dict[str, Any] = {
        "db": args.db,
        "code": ",".join(args.code),
        "startDate": args.start_date,
        "endDate": args.end_date,
        "lang": args.lang,
        "startPosition": args.start_position,
    }
    params.update(parse_kv(args.param))
    data = client.request_json("getDataCode", params)
    rows = flatten_data_code(data, limit=args.limit if not args.json else None)
    request = {key: value for key, value in params.items() if value is not None}
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": "/api/v1/getDataCode", "request": request, "raw": data, "rows": flatten_data_code(data)})
    else:
        print(render_data("/api/v1/getDataCode", data, rows, request, args.limit))


def command_metadata(args: argparse.Namespace) -> None:
    client = BojClient()
    params: dict[str, Any] = {"db": args.db, "lang": args.lang, "format": args.format}
    params.update(parse_kv(args.param))
    if args.format == "json":
        print_json(client.request_json("getMetadata", params))
    else:
        print(client.request_text("getMetadata", params), end="")


def command_layer(args: argparse.Namespace) -> None:
    client = BojClient()
    params: dict[str, Any] = {
        "db": args.db,
        "frequency": args.frequency,
        "layer": args.layer,
        "startDate": args.start_date,
        "endDate": args.end_date,
        "lang": args.lang,
        "format": args.format,
        "startPosition": args.start_position,
    }
    params.update(parse_kv(args.param))
    if args.format == "json":
        print_json(client.request_json("getDataLayer", params))
    else:
        print(client.request_text("getDataLayer", params), end="")


def command_request(args: argparse.Namespace) -> None:
    client = BojClient()
    params = parse_kv(args.param)
    params.setdefault("format", args.format)
    text = client.request_text(args.endpoint, params)
    print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Bank of Japan Time-Series Data Search API helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check BOJ API access. No credential is required.")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("data-code", help="Fetch time-series values by BOJ series code.")
    p.add_argument("--db", required=True, help="Database name, e.g. FM01.")
    p.add_argument("--code", action="append", required=True, help="Series code. Repeat or pass comma-separated values.")
    p.add_argument("--start-date", help="Start date such as 202501, 2025Q1, or 20250101 depending on DB.")
    p.add_argument("--end-date", help="End date.")
    p.add_argument("--lang", choices=["jp", "en"], default="jp")
    p.add_argument("--start-position", type=int)
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.add_argument("--limit", type=int, default=50, help="Maximum rows to print.")
    p.add_argument("--json", action="store_true")
    p.add_argument("--csv", action="store_true")
    p.set_defaults(func=command_data_code)

    p = sub.add_parser("metadata", help="Fetch BOJ metadata for a database.")
    p.add_argument("--db", required=True)
    p.add_argument("--lang", choices=["jp", "en"], default="jp")
    p.add_argument("--format", choices=["json", "csv"], default="json")
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.set_defaults(func=command_metadata)

    p = sub.add_parser("layer", help="Fetch BOJ layer data.")
    p.add_argument("--db", required=True)
    p.add_argument("--frequency", help="Frequency such as M, Q, A, or D.")
    p.add_argument("--layer", required=True, help="Layer expression, e.g. '*' or '1,1,1'.")
    p.add_argument("--start-date")
    p.add_argument("--end-date")
    p.add_argument("--lang", choices=["jp", "en"], default="jp")
    p.add_argument("--format", choices=["json", "csv"], default="csv")
    p.add_argument("--start-position", type=int)
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.set_defaults(func=command_layer)

    p = sub.add_parser("request", help="Call a read-only BOJ API endpoint directly.")
    p.add_argument("endpoint", choices=["getDataCode", "getDataLayer", "getMetadata"])
    p.add_argument("--format", choices=["json", "csv"], default="json")
    p.add_argument("--param", action="append", help="Parameter as KEY=VALUE.")
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except BojApiError as exc:
        print_json({"ok": False, "status": exc.status, "error": exc.data})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
