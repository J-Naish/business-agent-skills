#!/usr/bin/env python3
"""Read-only e-Stat API helper for public-data research workflows.

Loads ESTAT_APP_ID from environment variables or a nearby .env file.
Credential values and request URLs containing credentials are never printed.
"""
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


API_BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"
USER_AGENT = "codex-public-data-research-estat/1.0"
ENV_KEY = "ESTAT_APP_ID"
DEFAULT_CHECK_STATS_DATA_ID = "0002070001"


class EStatApiError(Exception):
    def __init__(self, status: int | None, data: Any):
        super().__init__(f"e-Stat API request failed with status {status}")
        self.status = status
        self.data = data


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
    path: Path | None = Path(env_path).expanduser() if env_path else find_dotenv()
    if not path or not path.exists():
        return None
    for raw in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_env_line(raw)
        if parsed:
            key, value = parsed
            os.environ.setdefault(key, value)
    return path


def missing_credentials_message() -> str:
    return (
        "ERROR: Required e-Stat API credential variable is not set.\n"
        f"Missing:\n  - {ENV_KEY}\n"
        "Define it in the OS environment or a nearby .env file. Do not print or commit secret values."
    )


def parse_kv(items: list[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def status_ok(status: Any) -> bool:
    return str(status) == "0"


def root_payload(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    for key, value in data.items():
        if key.startswith("GET_") and isinstance(value, dict):
            return key, value
    return "", data


def result_of(data: dict[str, Any]) -> dict[str, Any]:
    _, root = root_payload(data)
    result = root.get("RESULT", {})
    return result if isinstance(result, dict) else {}


def table_info(container: dict[str, Any]) -> dict[str, Any]:
    table = container.get("TABLE_INF", {})
    return table if isinstance(table, dict) else {}


def title_text(table: dict[str, Any]) -> str | None:
    title = table.get("TITLE")
    if isinstance(title, dict):
        return title.get("$")
    return title


def stat_name(table: dict[str, Any]) -> str | None:
    stat = table.get("STAT_NAME") or table.get("STATISTICS_NAME")
    if isinstance(stat, dict):
        return stat.get("$")
    return stat


def class_objects(container: dict[str, Any]) -> list[dict[str, Any]]:
    class_inf = container.get("CLASS_INF", {})
    if not isinstance(class_inf, dict):
        return []
    return [item for item in as_list(class_inf.get("CLASS_OBJ")) if isinstance(item, dict)]


def class_map(container: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    mapping: dict[str, dict[str, dict[str, Any]]] = {}
    for obj in class_objects(container):
        obj_id = obj.get("@id")
        if not obj_id:
            continue
        classes = [item for item in as_list(obj.get("CLASS")) if isinstance(item, dict)]
        mapping[obj_id] = {str(item.get("@code")): item for item in classes}
    return mapping


def class_label(mapping: dict[str, dict[str, dict[str, Any]]], dim: str, code: str | None) -> str | None:
    if code is None:
        return None
    item = mapping.get(dim, {}).get(str(code))
    if not item:
        return None
    return item.get("@name")


def class_unit(mapping: dict[str, dict[str, dict[str, Any]]], dim: str, code: str | None) -> str | None:
    if code is None:
        return None
    item = mapping.get(dim, {}).get(str(code))
    if not item:
        return None
    return item.get("@unit")


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


class EStatClient:
    def __init__(self, env_path: str | None = None, base_url: str = API_BASE):
        load_env(env_path)
        self.base_url = base_url.rstrip("/")

    def require_app_id(self) -> str:
        app_id = os.environ.get(ENV_KEY)
        if not app_id:
            raise SystemExit(missing_credentials_message())
        return app_id

    def request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        app_id = self.require_app_id()
        clean_params = {key: value for key, value in (params or {}).items() if value is not None}
        clean_params.setdefault("appId", app_id)
        path = endpoint.strip("/")
        url = self.base_url + "/" + path + "?" + urllib.parse.urlencode(clean_params)
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
            raise EStatApiError(exc.code, data) from exc
        except urllib.error.URLError as exc:
            raise EStatApiError(None, {"error": str(exc.reason)}) from exc


def table_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "statsDataId": item.get("@id"),
        "statName": stat_name(item),
        "title": title_text(item),
        "surveyDate": item.get("SURVEY_DATE"),
        "openDate": item.get("OPEN_DATE"),
        "updatedDate": item.get("UPDATED_DATE"),
        "collectArea": item.get("COLLECT_AREA"),
        "overallTotalNumber": item.get("OVERALL_TOTAL_NUMBER"),
    }


def metadata_container(data: dict[str, Any]) -> dict[str, Any]:
    _, root = root_payload(data)
    container = root.get("METADATA_INF", {})
    return container if isinstance(container, dict) else {}


def stats_data_container(data: dict[str, Any]) -> dict[str, Any]:
    _, root = root_payload(data)
    container = root.get("STATISTICAL_DATA", {})
    return container if isinstance(container, dict) else {}


def search_summary(data: dict[str, Any], query: str) -> dict[str, Any]:
    _, root = root_payload(data)
    result = result_of(data)
    datalist = root.get("DATALIST_INF", {})
    if not isinstance(datalist, dict):
        datalist = {}
    rows = [table_row(item) for item in as_list(datalist.get("TABLE_INF")) if isinstance(item, dict)]
    return {
        "ok": status_ok(result.get("STATUS")),
        "status": result.get("STATUS"),
        "error": result.get("ERROR_MSG"),
        "endpoint": "getStatsList",
        "query": query,
        "number": datalist.get("NUMBER"),
        "resultInf": datalist.get("RESULT_INF"),
        "tables": rows,
    }


def metadata_summary(data: dict[str, Any], find: str | None = None, class_id: str | None = None, limit: int = 12) -> dict[str, Any]:
    result = result_of(data)
    container = metadata_container(data)
    table = table_info(container)
    classes_summary = []
    matches = []
    needle = find.casefold() if find else None
    for obj in class_objects(container):
        obj_id = obj.get("@id")
        if class_id and obj_id != class_id:
            continue
        classes = [item for item in as_list(obj.get("CLASS")) if isinstance(item, dict)]
        first = [
            {
                "code": item.get("@code"),
                "name": item.get("@name"),
                "unit": item.get("@unit"),
                "level": item.get("@level"),
            }
            for item in classes[:limit]
        ]
        classes_summary.append(
            {
                "id": obj_id,
                "name": obj.get("@name"),
                "count": len(classes),
                "firstClasses": first,
            }
        )
        if needle:
            for item in classes:
                name = str(item.get("@name") or "")
                code = str(item.get("@code") or "")
                if needle in name.casefold() or needle in code.casefold():
                    matches.append(
                        {
                            "classId": obj_id,
                            "className": obj.get("@name"),
                            "code": item.get("@code"),
                            "name": item.get("@name"),
                            "unit": item.get("@unit"),
                            "level": item.get("@level"),
                        }
                    )
    return {
        "ok": status_ok(result.get("STATUS")),
        "status": result.get("STATUS"),
        "error": result.get("ERROR_MSG"),
        "endpoint": "getMetaInfo",
        "table": {
            "statsDataId": table.get("@id"),
            "statName": stat_name(table),
            "title": title_text(table),
        },
        "classes": classes_summary,
        "matches": matches[: max(limit, 50)] if needle else [],
    }


def values_list(container: dict[str, Any]) -> list[dict[str, Any]]:
    data_inf = container.get("DATA_INF", {})
    if not isinstance(data_inf, dict):
        return []
    return [item for item in as_list(data_inf.get("VALUE")) if isinstance(item, dict)]


def flatten_value(value: dict[str, Any], mapping: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    unit = value.get("@unit")
    for raw_key, raw_value in value.items():
        if not raw_key.startswith("@"):
            continue
        key = raw_key[1:]
        if key == "unit":
            continue
        code = str(raw_value)
        label = class_label(mapping, key, code)
        if label:
            row[key] = label
            row[f"{key}_code"] = code
        else:
            row[key] = code
        unit = unit or class_unit(mapping, key, code)
    row["unit"] = unit
    row["value"] = value.get("$")
    return row


def latest_time_code(data: dict[str, Any]) -> str | None:
    summary = metadata_summary(data, limit=1)
    container = metadata_container(data)
    for obj in class_objects(container):
        if obj.get("@id") == "time":
            classes = [item for item in as_list(obj.get("CLASS")) if isinstance(item, dict)]
            if classes:
                return classes[-1].get("@code")
    # Keep summary referenced so changes in metadata shape are easier to debug under --json.
    _ = summary
    return None


def data_summary(data: dict[str, Any], request_params: dict[str, Any], limit: int) -> dict[str, Any]:
    result = result_of(data)
    container = stats_data_container(data)
    table = table_info(container)
    mapping = class_map(container)
    values = values_list(container)
    rows = [flatten_value(item, mapping) for item in values]
    return {
        "ok": status_ok(result.get("STATUS")),
        "status": result.get("STATUS"),
        "error": result.get("ERROR_MSG"),
        "endpoint": "getStatsData",
        "request": {
            key: value
            for key, value in request_params.items()
            if key != "appId" and value is not None
        },
        "table": {
            "statsDataId": table.get("@id"),
            "statName": stat_name(table),
            "title": title_text(table),
        },
        "rowCount": len(rows),
        "rows": rows[:limit],
    }


def render_search(summary: dict[str, Any]) -> str:
    lines = ["# e-Stat Search", ""]
    lines.append(f"- Endpoint: `{summary['endpoint']}`")
    lines.append(f"- Query: `{summary['query']}`")
    lines.append(f"- Status: {summary['status']} {summary.get('error') or ''}".rstrip())
    if summary.get("number") is not None:
        lines.append(f"- Matched tables: {summary['number']}")
    lines.append("")
    lines.append("## Tables")
    if summary["tables"]:
        for item in summary["tables"]:
            lines.append(
                f"- `{item.get('statsDataId')}` | {item.get('statName')} | "
                f"{item.get('title')} | updated {item.get('updatedDate')}"
            )
    else:
        lines.append("- No tables returned.")
    return "\n".join(lines)


def render_meta(summary: dict[str, Any]) -> str:
    table = summary["table"]
    lines = ["# e-Stat Metadata", ""]
    lines.append(f"- Endpoint: `{summary['endpoint']}`")
    lines.append(f"- Table ID: `{table.get('statsDataId')}`")
    lines.append(f"- Statistic: {table.get('statName')}")
    lines.append(f"- Title: {table.get('title')}")
    lines.append(f"- Status: {summary['status']} {summary.get('error') or ''}".rstrip())
    lines.append("")
    if summary.get("matches"):
        lines.append("## Matching Classes")
        for item in summary["matches"]:
            unit = f" ({item.get('unit')})" if item.get("unit") else ""
            lines.append(
                f"- `{item.get('classId')}` `{item.get('code')}` {item.get('name')}{unit}"
            )
        lines.append("")
    lines.append("## Classes")
    for obj in summary["classes"]:
        lines.append(f"### {obj.get('id')} - {obj.get('name')} ({obj.get('count')})")
        for item in obj.get("firstClasses", []):
            unit = f" ({item.get('unit')})" if item.get("unit") else ""
            lines.append(f"- `{item.get('code')}` {item.get('name')}{unit}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_data(summary: dict[str, Any]) -> str:
    table = summary["table"]
    lines = ["# e-Stat Data", ""]
    lines.append(f"- Endpoint: `{summary['endpoint']}`")
    lines.append(f"- Table ID: `{table.get('statsDataId')}`")
    lines.append(f"- Statistic: {table.get('statName')}")
    lines.append(f"- Title: {table.get('title')}")
    lines.append(f"- Status: {summary['status']} {summary.get('error') or ''}".rstrip())
    lines.append(f"- Rows returned: {summary['rowCount']}")
    lines.append(f"- Request: `{summary['request']}`")
    lines.append("")
    lines.append("## Rows")
    if not summary["rows"]:
        lines.append("- No rows returned.")
        return "\n".join(lines)
    for row in summary["rows"]:
        dims = []
        for key, value in row.items():
            if key.endswith("_code") or key in {"unit", "value"}:
                continue
            code = row.get(f"{key}_code")
            dims.append(f"{key}={value}" + (f" [{code}]" if code else ""))
        unit = f" {row.get('unit')}" if row.get("unit") else ""
        lines.append(f"- {', '.join(dims)}: {row.get('value')}{unit}")
    return "\n".join(lines)


def write_csv(summary: dict[str, Any]) -> None:
    rows = summary.get("rows") or []
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
    client = EStatClient(env_path=args.env)
    try:
        data = client.request("getMetaInfo", {"statsDataId": DEFAULT_CHECK_STATS_DATA_ID, "lang": args.lang})
        result = result_of(data)
        summary = {
            "checks": [
                {
                    "auth": "app_id",
                    "endpoint": "getMetaInfo",
                    "statsDataId": DEFAULT_CHECK_STATS_DATA_ID,
                    "ok": status_ok(result.get("STATUS")),
                    "status": result.get("STATUS"),
                    "error": result.get("ERROR_MSG"),
                }
            ]
        }
    except EStatApiError as exc:
        summary = {
            "checks": [
                {
                    "auth": "app_id",
                    "endpoint": "getMetaInfo",
                    "statsDataId": DEFAULT_CHECK_STATS_DATA_ID,
                    "ok": False,
                    "status": exc.status,
                    "error": exc.data,
                }
            ]
        }
    print_json(summary)


def command_search(args: argparse.Namespace) -> None:
    client = EStatClient(env_path=args.env)
    params: dict[str, Any] = {
        "lang": args.lang,
        "searchWord": args.query,
        "limit": args.limit,
        "startPosition": args.start_position,
        "statsCode": args.stats_code,
        "collectArea": args.collect_area,
        "surveyYears": args.survey_years,
    }
    params.update(parse_kv(args.param))
    data = client.request("getStatsList", params)
    summary = search_summary(data, args.query)
    print_json(summary) if args.json else print(render_search(summary))


def command_meta(args: argparse.Namespace) -> None:
    client = EStatClient(env_path=args.env)
    params = {"lang": args.lang, "statsDataId": args.stats_data_id}
    params.update(parse_kv(args.param))
    data = client.request("getMetaInfo", params)
    summary = metadata_summary(data, find=args.find, class_id=args.class_id, limit=args.limit)
    print_json(summary) if args.json else print(render_meta(summary))


def command_data(args: argparse.Namespace) -> None:
    client = EStatClient(env_path=args.env)
    params: dict[str, Any] = {
        "lang": args.lang,
        "statsDataId": args.stats_data_id,
        "limit": args.api_limit,
        "startPosition": args.start_position,
    }
    params.update(parse_kv(args.filter))
    params.update(parse_kv(args.param))
    if args.latest_time and "cdTime" not in params:
        meta = client.request("getMetaInfo", {"lang": args.lang, "statsDataId": args.stats_data_id})
        latest = latest_time_code(meta)
        if latest:
            params["cdTime"] = latest
    data = client.request("getStatsData", params)
    summary = data_summary(data, params, args.limit)
    if args.csv:
        write_csv(summary)
    elif args.json:
        print_json(summary)
    else:
        print(render_data(summary))


def command_request(args: argparse.Namespace) -> None:
    client = EStatClient(env_path=args.env)
    params = {"lang": args.lang}
    params.update(parse_kv(args.param))
    data = client.request(args.endpoint, params)
    print_json(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only e-Stat API research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check ESTAT_APP_ID with a minimal metadata request.")
    p.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    p.add_argument("--lang", choices=["J", "E"], default="J")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("search", help="Search e-Stat statistics tables with getStatsList.")
    p.add_argument("query", help="Search keyword. Japanese terms usually work best.")
    p.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    p.add_argument("--lang", choices=["J", "E"], default="J")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--start-position", type=int)
    p.add_argument("--stats-code")
    p.add_argument("--collect-area")
    p.add_argument("--survey-years")
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_search)

    p = sub.add_parser("meta", help="Inspect dimensions and class codes for a statsDataId.")
    p.add_argument("stats_data_id")
    p.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    p.add_argument("--lang", choices=["J", "E"], default="J")
    p.add_argument("--find", help="Find matching code or class label.")
    p.add_argument("--class-id", help="Only show one class dimension, such as cat01 or area.")
    p.add_argument("--limit", type=int, default=12)
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_meta)

    p = sub.add_parser("data", help="Fetch data values with getStatsData.")
    p.add_argument("stats_data_id")
    p.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    p.add_argument("--lang", choices=["J", "E"], default="J")
    p.add_argument("--filter", action="append", help="Filter parameter as KEY=VALUE, e.g. cdCat01=098.")
    p.add_argument("--param", action="append", help="Extra parameter as KEY=VALUE.")
    p.add_argument("--latest-time", action="store_true", help="Use the latest time code from metadata when cdTime is absent.")
    p.add_argument("--api-limit", type=int, help="Pass e-Stat limit parameter to the API.")
    p.add_argument("--start-position", type=int)
    p.add_argument("--limit", type=int, default=20, help="Maximum rows to print.")
    p.add_argument("--csv", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_data)

    p = sub.add_parser("request", help="Call a read-only e-Stat endpoint directly.")
    p.add_argument("endpoint", choices=["getStatsList", "getMetaInfo", "getStatsData"])
    p.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    p.add_argument("--lang", choices=["J", "E"], default="J")
    p.add_argument("--param", action="append", help="Endpoint parameter as KEY=VALUE.")
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except EStatApiError as exc:
        print_json({"ok": False, "status": exc.status, "error": exc.data})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
