#!/usr/bin/env python3
"""Read-only OECD SDMX API helper for public-data research."""
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
import xml.etree.ElementTree as ET
from typing import Any, Iterable


API_BASE = "https://sdmx.oecd.org/public/rest"
USER_AGENT = "codex-public-data-research-oecd-sdmx/1.0"
CSV_ACCEPT = "application/vnd.sdmx.data+csv; charset=utf-8"
XML_ACCEPT = "application/vnd.sdmx.structure+xml; version=2.1"


class OecdApiError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"OECD SDMX API request failed with status {status}")
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


class OecdClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")

    def request_text(self, path: str, params: dict[str, Any] | None = None, accept: str = XML_ACCEPT) -> str:
        clean_params = {key: value for key, value in (params or {}).items() if value is not None}
        url = self.base_url + clean_path(path)
        if clean_params:
            url += "?" + urllib.parse.urlencode(clean_params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8-sig", "replace")
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8-sig", "replace")
            raise OecdApiError(exc.code, {"raw": text[:4000]}) from exc
        except urllib.error.URLError as exc:
            raise OecdApiError(None, {"error": str(exc.reason)}) from exc


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
                "isExternalReference": element.attrib.get("isExternalReference"),
                "isFinal": element.attrib.get("isFinal"),
                "structureUrl": element.attrib.get("structureURL"),
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
        lines.append(
            f"- `{row.get('agencyId')},{row.get('id')},{row.get('version')}` | "
            f"{row.get('name') or ''} | {row.get('description') or ''}"
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
    client = OecdClient()
    endpoint = "/dataflow/all/all/latest"
    try:
        text = client.request_text(endpoint, {"references": "none", "detail": "allstubs"})
        rows = parse_dataflows(text)
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
    except OecdApiError as exc:
        print_json({"checks": [{"auth": "none", "endpoint": endpoint, "ok": False, "status": exc.status, "error": exc.data}]})


def command_dataflows(args: argparse.Namespace) -> None:
    client = OecdClient()
    endpoint = "/dataflow/all/all/latest"
    text = client.request_text(endpoint, {"references": "none", "detail": "allstubs"})
    rows = [row for row in parse_dataflows(text) if contains_query(row, args.query, ["id", "agencyId", "name", "description"])]
    if args.csv:
        write_csv(rows)
    elif args.json:
        print_json({"endpoint": endpoint, "query": args.query, "rows": rows})
    else:
        print(render_rows("OECD SDMX Dataflows", endpoint, rows, args.limit))


def command_structure(args: argparse.Namespace) -> None:
    client = OecdClient()
    endpoint = f"/dataflow/{args.agency}/{args.dataflow}/{args.version}"
    params = {"references": args.references, "detail": args.detail}
    params.update(parse_kv(args.param))
    text = client.request_text(endpoint, params)
    if args.json:
        print_json({"endpoint": endpoint, "params": params, "dataflows": parse_dataflows(text)})
    else:
        print(text, end="")


def command_data(args: argparse.Namespace) -> None:
    client = OecdClient()
    endpoint = f"/data/{args.agency},{args.dataflow},{args.version}/{args.filter}"
    params: dict[str, Any] = {
        "startPeriod": args.start_period,
        "endPeriod": args.end_period,
        "lastNObservations": args.last_n_observations,
        "dimensionAtObservation": args.dimension_at_observation,
    }
    params.update(parse_kv(args.param))
    accept = CSV_ACCEPT if args.format == "csv" else "application/vnd.sdmx.genericdata+xml; charset=utf-8; version=2.1"
    print(client.request_text(endpoint, params, accept=accept), end="")


def command_request(args: argparse.Namespace) -> None:
    client = OecdClient()
    params = parse_kv(args.param)
    accept = CSV_ACCEPT if args.accept == "csv" else XML_ACCEPT
    print(client.request_text(args.path, params, accept=accept), end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only OECD SDMX API research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check OECD SDMX access. No credential is required.")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("dataflows", help="List or filter OECD SDMX dataflows.")
    p.add_argument("query", nargs="?", help="Optional local filter.")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.add_argument("--csv", action="store_true")
    p.set_defaults(func=command_dataflows)

    p = sub.add_parser("structure", help="Fetch dataflow structure XML.")
    p.add_argument("agency", help="Agency id, e.g. OECD.ENV.EPI.")
    p.add_argument("dataflow", help="Dataflow id, e.g. DSD_ECH@EXT_DROUGHT.")
    p.add_argument("--version", default="latest")
    p.add_argument("--references", default="all")
    p.add_argument("--detail", default="referencepartial")
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.add_argument("--json", action="store_true", help="Only extract dataflow stubs from the structure response.")
    p.set_defaults(func=command_structure)

    p = sub.add_parser("data", help="Fetch OECD SDMX data and print raw CSV/XML to stdout.")
    p.add_argument("agency", help="Agency id.")
    p.add_argument("dataflow", help="Dataflow id.")
    p.add_argument("filter", help="SDMX v1 filter expression, e.g. all or AUS.A.ED_CROP_ANOM.....")
    p.add_argument("--version", default="latest")
    p.add_argument("--start-period")
    p.add_argument("--end-period")
    p.add_argument("--last-n-observations", type=int)
    p.add_argument("--dimension-at-observation", default="AllDimensions")
    p.add_argument("--format", choices=["csv", "xml"], default="csv")
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.set_defaults(func=command_data)

    p = sub.add_parser("request", help="Call a read-only OECD SDMX path directly.")
    p.add_argument("path", help="Path under /public/rest, e.g. /dataflow/all/all/latest.")
    p.add_argument("--param", action="append", help="Parameter as KEY=VALUE.")
    p.add_argument("--accept", choices=["xml", "csv"], default="xml")
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (OecdApiError, ET.ParseError) as exc:
        if isinstance(exc, OecdApiError):
            print_json({"ok": False, "status": exc.status, "error": exc.data})
        else:
            print_json({"ok": False, "error": f"XML parse error: {exc}"})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
