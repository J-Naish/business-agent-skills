#!/usr/bin/env python3
"""Read-only FAOSTAT bulk download helper for public-data research."""
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Iterable


USER_AGENT = "codex-public-data-research-faostat/1.0"

CATALOG = [
    {
        "key": "production-crops-livestock",
        "title": "Production: crops and livestock products",
        "coverage": "World countries/areas; crop and livestock production, area, yield, stocks, slaughtered animals.",
        "url": "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip",
        "verified": "2026-06-22",
    }
]


class FaostatError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"FAOSTAT request failed with status {status}")
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


def contains_query(item: dict[str, Any], query: str | None, fields: Iterable[str]) -> bool:
    if not query:
        return True
    needle = query.casefold()
    haystack = " ".join(str(item.get(field) or "") for field in fields)
    return needle in haystack.casefold()


def resolve_source(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        return source
    matches = [item for item in CATALOG if source == item["key"]]
    if not matches:
        matches = [item for item in CATALOG if contains_query(item, source, ["key", "title", "coverage"])]
    if not matches:
        raise SystemExit(f"No FAOSTAT catalog item matched: {source}. Use a full bulk ZIP URL if needed.")
    return str(matches[0]["url"])


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8-sig", "replace")
        raise FaostatError(exc.code, {"raw": text[:4000], "url": url}) from exc
    except urllib.error.URLError as exc:
        raise FaostatError(None, {"error": str(exc.reason), "url": url}) from exc


def request_head(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return {
                "status": resp.status,
                "contentType": resp.headers.get("content-type"),
                "contentLength": resp.headers.get("content-length"),
                "lastModified": resp.headers.get("last-modified"),
            }
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8-sig", "replace")
        raise FaostatError(exc.code, {"raw": text[:4000], "url": url}) from exc
    except urllib.error.URLError as exc:
        raise FaostatError(None, {"error": str(exc.reason), "url": url}) from exc


def write_catalog(rows: list[dict[str, Any]]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=["key", "title", "coverage", "url", "verified"])
    writer.writeheader()
    writer.writerows(rows)


def render_catalog(rows: list[dict[str, Any]], limit: int) -> str:
    lines = ["# FAOSTAT Bulk Catalog", ""]
    lines.append(f"- Rows shown: {min(len(rows), limit)} of {len(rows)} matched")
    lines.append("")
    lines.append("## Rows")
    if not rows:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        lines.append(f"- `{row['key']}` | {row['title']} | {row['coverage']} | {row['url']}")
    return "\n".join(lines)


def output_zip_member(data: bytes, member: str | None, limit: int, filters: dict[str, str]) -> None:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        chosen = member
        if not chosen:
            csv_names = [name for name in names if name.lower().endswith(".csv")]
            chosen = csv_names[0] if csv_names else names[0]
        if chosen not in names:
            raise SystemExit(f"Member not found in ZIP: {chosen}. Available: {', '.join(names[:20])}")
        with zf.open(chosen) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8-sig", errors="replace", newline="")
            if chosen.lower().endswith(".csv"):
                reader = csv.DictReader(text)
                writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames or [])
                writer.writeheader()
                written = 0
                for row in reader:
                    if filters and any(str(row.get(key, "")) != value for key, value in filters.items()):
                        continue
                    writer.writerow(row)
                    written += 1
                    if written >= limit:
                        break
            else:
                for idx, line in enumerate(text):
                    if idx >= limit:
                        break
                    print(line, end="")


def command_check_auth(args: argparse.Namespace) -> None:
    try:
        meta = request_head(CATALOG[0]["url"])
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": CATALOG[0]["url"],
                        "ok": meta.get("status") == 200,
                        **meta,
                    }
                ]
            }
        )
    except FaostatError as exc:
        if isinstance(exc, FaostatError):
            error = {"status": exc.status, "error": exc.data}
        else:
            error = {"status": None, "error": str(exc)}
        print_json({"checks": [{"auth": "none", "endpoint": CATALOG[0]["url"], "ok": False, **error}]})


def command_catalog(args: argparse.Namespace) -> None:
    rows = [row for row in CATALOG if contains_query(row, args.query, ["key", "title", "coverage"])]
    if args.csv:
        write_catalog(rows)
    elif args.json:
        print_json({"rows": rows})
    else:
        print(render_catalog(rows, args.limit))


def command_fetch(args: argparse.Namespace) -> None:
    url = resolve_source(args.source)
    output_zip_member(request_bytes(url), args.member, args.limit, parse_kv(args.filter))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only FAOSTAT bulk download helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check FAOSTAT public bulk access. No credential is required.")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("catalog", help="List known FAOSTAT bulk downloads.")
    p.add_argument("query", nargs="?", help="Optional local filter.")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.add_argument("--csv", action="store_true")
    p.set_defaults(func=command_catalog)

    p = sub.add_parser("fetch", help="Fetch a FAOSTAT bulk ZIP and print CSV rows to stdout.")
    p.add_argument("source", help="Catalog key, search term, or full FAOSTAT bulk ZIP URL.")
    p.add_argument("--member", help="Optional ZIP member name.")
    p.add_argument("--filter", action="append", help="CSV filter as COLUMN=VALUE. Exact match.")
    p.add_argument("--limit", type=int, default=100, help="Maximum data rows or text lines to print.")
    p.set_defaults(func=command_fetch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (FaostatError, zipfile.BadZipFile) as exc:
        if isinstance(exc, FaostatError):
            print_json({"ok": False, "status": exc.status, "error": exc.data})
        else:
            print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
