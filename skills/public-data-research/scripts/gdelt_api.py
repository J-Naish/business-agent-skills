#!/usr/bin/env python3
"""Read-only GDELT API helper for public-data research."""
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


API_BASE = "https://api.gdeltproject.org/api/v2"
USER_AGENT = "codex-public-data-research-gdelt/1.0"


class GdeltApiError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"GDELT API request failed with status {status}")
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


def clean_path(path: str) -> str:
    return path if path.startswith("/") else "/" + path


class GdeltClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")

    def request_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        clean_params = {key: value for key, value in params.items() if value is not None}
        clean_params.setdefault("format", "json")
        url = self.base_url + clean_path(path) + "?" + urllib.parse.urlencode(clean_params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                text = resp.read().decode("utf-8-sig", "replace")
                try:
                    data = json.loads(text) if text else {}
                except json.JSONDecodeError as exc:
                    raise GdeltApiError(None, {"error": "Invalid JSON response", "raw": text[:2000], "url": url}) from exc
                return data if isinstance(data, dict) else {"data": data}
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8-sig", "replace")
            try:
                data = json.loads(text) if text else {}
            except json.JSONDecodeError:
                data = {"raw": text[:2000]}
            raise GdeltApiError(exc.code, data) from exc
        except urllib.error.URLError as exc:
            raise GdeltApiError(None, {"error": str(exc.reason)}) from exc


def article_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    articles = data.get("articles")
    if not isinstance(articles, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in articles:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "domain": item.get("domain"),
                "sourceCountry": item.get("sourcecountry"),
                "language": item.get("language"),
                "seendate": item.get("seendate"),
                "socialImage": item.get("socialimage"),
            }
        )
    return rows


def render_doc(data: dict[str, Any], request: dict[str, Any], rows: list[dict[str, Any]], limit: int) -> str:
    lines = ["# GDELT DOC", ""]
    lines.append("- Endpoint: `/api/v2/doc/doc`")
    lines.append(f"- Request: `{request}`")
    if data.get("status"):
        lines.append(f"- Status: {data.get('status')}")
    lines.append(f"- Rows shown: {min(len(rows), limit)} of {len(rows)} fetched")
    lines.append("")
    lines.append("## Articles")
    if not rows:
        lines.append("- No articles returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        lines.append(
            f"- {row.get('seendate') or ''} | {row.get('domain') or ''} | "
            f"{row.get('title') or ''} | {row.get('url') or ''}"
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
    client = GdeltClient()
    params = {"query": "climate", "mode": "artlist", "format": "json", "maxrecords": 1, "timespan": "1d"}
    try:
        data = client.request_json("/doc/doc", params)
        rows = article_rows(data)
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/api/v2/doc/doc",
                        "ok": bool(rows) or "articles" in data,
                        "status": 200,
                        "sampleRows": rows[:1],
                    }
                ]
            }
        )
    except GdeltApiError as exc:
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": "/api/v2/doc/doc",
                        "ok": False,
                        "status": exc.status,
                        "error": exc.data,
                    }
                ]
            }
        )


def command_doc(args: argparse.Namespace) -> None:
    client = GdeltClient()
    params: dict[str, Any] = {
        "query": args.query,
        "mode": args.mode,
        "format": "json",
        "maxrecords": args.maxrecords,
        "timespan": args.timespan,
        "startdatetime": args.startdatetime,
        "enddatetime": args.enddatetime,
        "sort": args.sort,
    }
    params.update(parse_kv(args.param))
    data = client.request_json("/doc/doc", params)
    rows = article_rows(data)
    request = {key: value for key, value in params.items() if value is not None}
    if args.csv:
        write_csv(rows)
    elif args.json or args.mode != "artlist":
        print_json({"endpoint": "/api/v2/doc/doc", "request": request, "raw": data, "rows": rows})
    else:
        print(render_doc(data, request, rows, args.limit))


def command_request(args: argparse.Namespace) -> None:
    client = GdeltClient()
    params = parse_kv(args.param)
    print_json(client.request_json(args.path, params))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only GDELT API research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check GDELT API access. No credential is required.")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("doc", help="Search GDELT DOC 2.0 and print article/timeline data.")
    p.add_argument("query", help="GDELT full-text query.")
    p.add_argument("--mode", default="artlist", help="DOC mode, e.g. artlist, timelinevol, timelinevolraw.")
    p.add_argument("--maxrecords", type=int, default=10)
    p.add_argument("--timespan", default="7d", help="Relative window such as 1d, 7d, 1m.")
    p.add_argument("--startdatetime", help="UTC start datetime, e.g. 20260101000000.")
    p.add_argument("--enddatetime", help="UTC end datetime, e.g. 20260131235959.")
    p.add_argument("--sort", help="Sort option supported by GDELT, e.g. datedesc.")
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.add_argument("--csv", action="store_true")
    p.set_defaults(func=command_doc)

    p = sub.add_parser("request", help="Call a read-only GDELT API path directly.")
    p.add_argument("path", help="Path under /api/v2, e.g. /doc/doc or /geo/geo.")
    p.add_argument("--param", action="append", help="Parameter as KEY=VALUE.")
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except GdeltApiError as exc:
        print_json({"ok": False, "status": exc.status, "error": exc.data})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
