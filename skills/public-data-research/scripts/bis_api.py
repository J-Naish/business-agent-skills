#!/usr/bin/env python3
"""Read-only BIS statistics helper using SDMX dataflows and bulk CSV downloads."""
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Iterable


SDMX_BASE = "https://stats.bis.org/api/v1"
BULK_PAGE = "https://data.bis.org/bulkdownload"
BULK_BASE = "https://data.bis.org"
USER_AGENT = "codex-public-data-research-bis/1.0"


class BisApiError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"BIS request failed with status {status}")
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


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str | None:
    fallback: str | None = None
    for child in element:
        if local_name(child.tag) != child_name:
            continue
        text = " ".join((child.text or "").split())
        if not text:
            continue
        if child.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") == "en":
            return text
        fallback = fallback or text
    return fallback


def contains_query(item: dict[str, Any], query: str | None, fields: Iterable[str]) -> bool:
    if not query:
        return True
    needle = query.casefold()
    haystack = " ".join(str(item.get(field) or "") for field in fields)
    return needle in haystack.casefold()


class BisClient:
    def request_text(self, url_or_path: str, params: dict[str, Any] | None = None, accept: str = "*/*") -> str:
        clean_params = {key: value for key, value in (params or {}).items() if value is not None}
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            url = url_or_path
        else:
            url = SDMX_BASE.rstrip("/") + clean_path(url_or_path)
        if clean_params:
            url += "?" + urllib.parse.urlencode(clean_params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8-sig", "replace")
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8-sig", "replace")
            raise BisApiError(exc.code, {"raw": text[:4000]}) from exc
        except urllib.error.URLError as exc:
            raise BisApiError(None, {"error": str(exc.reason)}) from exc

    def request_bytes(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8-sig", "replace")
            raise BisApiError(exc.code, {"raw": text[:4000]}) from exc
        except urllib.error.URLError as exc:
            raise BisApiError(None, {"error": str(exc.reason)}) from exc


def parse_dataflows(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, Any]] = []
    for element in root.iter():
        if local_name(element.tag) != "Dataflow":
            continue
        rows.append(
            {
                "id": element.attrib.get("id"),
                "agencyId": element.attrib.get("agencyID"),
                "version": element.attrib.get("version"),
                "name": child_text(element, "Name"),
                "description": child_text(element, "Description"),
                "isFinal": element.attrib.get("isFinal"),
            }
        )
    return rows


def parse_bulk_links(page_html: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = re.compile(
        r'<a href="(?P<href>/static/bulk/[^"]+?\.zip)"[^>]*>.*?'
        r"<h4[^>]*>(?P<title>.*?)</h4>.*?"
        r'<time dateTime="(?P<date>[^"]+)">(?P<date_text>.*?)</time>',
        re.DOTALL,
    )
    for match in pattern.finditer(page_html):
        href = html.unescape(match.group("href"))
        title = re.sub(r"<[^>]+>", "", html.unescape(match.group("title")))
        date_text = re.sub(r"<[^>]+>", "", html.unescape(match.group("date_text")))
        rows.append(
            {
                "title": " ".join(title.split()),
                "date": " ".join(date_text.split()),
                "href": href,
                "url": urllib.parse.urljoin(BULK_BASE, href),
                "format": "csv" if "_csv_" in href else "sdmx",
                "flat": href.endswith("_csv_flat.zip"),
            }
        )
    return rows


def render_rows(title: str, endpoint: str, rows: list[dict[str, Any]], limit: int) -> str:
    lines = [f"# {title}", ""]
    lines.append(f"- Endpoint: `{endpoint}`")
    lines.append(f"- Rows shown: {min(len(rows), limit)} of {len(rows)} matched")
    lines.append("")
    lines.append("## Rows")
    if not rows:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in rows[:limit]:
        parts = [f"{key}={value}" for key, value in row.items() if value not in (None, "", [])]
        lines.append(f"- {', '.join(parts)}")
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


def resolve_bulk_source(client: BisClient, source: str, prefer_flat: bool) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        return source
    if source.startswith("/static/bulk/"):
        return urllib.parse.urljoin(BULK_BASE, source)
    rows = parse_bulk_links(client.request_text(BULK_PAGE))
    matches = [row for row in rows if contains_query(row, source, ["title", "href"]) and row.get("format") == "csv"]
    if prefer_flat:
        flat = [row for row in matches if row.get("flat")]
        if flat:
            matches = flat
    if not matches:
        raise SystemExit(f"No BIS CSV bulk download matched: {source}")
    return str(matches[0]["url"])


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
    client = BisClient()
    endpoint = "/dataflow/all/all/latest"
    try:
        rows = parse_dataflows(client.request_text(endpoint))
        print_json(
            {
                "checks": [
                    {
                        "auth": "none",
                        "endpoint": endpoint,
                        "ok": bool(rows),
                        "status": 200,
                        "dataflowCount": len(rows),
                        "sample": rows[0] if rows else None,
                    }
                ]
            }
        )
    except BisApiError as exc:
        print_json({"checks": [{"auth": "none", "endpoint": endpoint, "ok": False, "status": exc.status, "error": exc.data}]})


def command_dataflows(args: argparse.Namespace) -> None:
    client = BisClient()
    endpoint = "/dataflow/all/all/latest"
    rows = [row for row in parse_dataflows(client.request_text(endpoint)) if contains_query(row, args.query, ["id", "agencyId", "name", "description"])]
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": endpoint, "query": args.query, "rows": rows})
    else:
        print(render_rows("BIS SDMX Dataflows", endpoint, rows, args.limit))


def command_bulk_list(args: argparse.Namespace) -> None:
    client = BisClient()
    rows = [row for row in parse_bulk_links(client.request_text(BULK_PAGE)) if contains_query(row, args.query, ["title", "href", "date"])]
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": BULK_PAGE, "query": args.query, "rows": rows})
    else:
        print(render_rows("BIS Bulk Downloads", BULK_PAGE, rows, args.limit))


def command_bulk_fetch(args: argparse.Namespace) -> None:
    client = BisClient()
    url = resolve_bulk_source(client, args.source, args.prefer_flat)
    data = client.request_bytes(url)
    output_zip_member(data, args.member, args.limit, parse_kv(args.filter))


def command_request(args: argparse.Namespace) -> None:
    client = BisClient()
    print(client.request_text(args.path, parse_kv(args.param)), end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only BIS statistics helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check BIS SDMX access. No credential is required.")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("dataflows", help="List or filter BIS SDMX dataflows.")
    p.add_argument("query", nargs="?", help="Optional local filter.")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.add_argument("--csv", action="store_true")
    p.set_defaults(func=command_dataflows)

    p = sub.add_parser("bulk-list", help="List or filter BIS bulk download ZIPs.")
    p.add_argument("query", nargs="?", help="Optional local filter.")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.add_argument("--csv", action="store_true")
    p.set_defaults(func=command_bulk_list)

    p = sub.add_parser("bulk-fetch", help="Fetch a BIS bulk CSV ZIP and print rows to stdout.")
    p.add_argument("source", help="Bulk URL, /static/bulk path, or search term such as 'policy rates'.")
    p.add_argument("--prefer-flat", action="store_true", default=True, help="Prefer '(CSV, flat)' downloads when searching.")
    p.add_argument("--member", help="Optional ZIP member name.")
    p.add_argument("--filter", action="append", help="CSV filter as COLUMN=VALUE. Exact match.")
    p.add_argument("--limit", type=int, default=100, help="Maximum data rows or text lines to print.")
    p.set_defaults(func=command_bulk_fetch)

    p = sub.add_parser("request", help="Call a read-only BIS SDMX path directly.")
    p.add_argument("path", help="Path under https://stats.bis.org/api/v1, e.g. /dataflow/all/all/latest.")
    p.add_argument("--param", action="append", help="Parameter as KEY=VALUE.")
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (BisApiError, ET.ParseError, zipfile.BadZipFile) as exc:
        if isinstance(exc, BisApiError):
            print_json({"ok": False, "status": exc.status, "error": exc.data})
        else:
            print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
