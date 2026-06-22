#!/usr/bin/env python3
"""Read-only X API helper for research workflows.

Loads X API credentials from environment variables or a nearby .env file.
Credential values are never printed.
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


API_BASE = "https://api.x.com"
USER_AGENT = "codex-x-research/1.0"

DEFAULT_TWEET_FIELDS = (
    "attachments,author_id,context_annotations,conversation_id,created_at,"
    "entities,geo,id,in_reply_to_user_id,lang,possibly_sensitive,public_metrics,"
    "referenced_tweets,reply_settings,text,withheld"
)
DEFAULT_USER_FIELDS = (
    "created_at,description,entities,id,location,name,pinned_tweet_id,"
    "profile_image_url,protected,public_metrics,url,username,verified,"
    "verified_type,withheld"
)
DEFAULT_MEDIA_FIELDS = (
    "alt_text,duration_ms,height,media_key,preview_image_url,public_metrics,type,url,width"
)
DEFAULT_PLACE_FIELDS = "contained_within,country,country_code,full_name,geo,id,name,place_type"
DEFAULT_POLL_FIELDS = "duration_minutes,end_datetime,id,options,voting_status"
DEFAULT_TWEET_EXPANSIONS = (
    "author_id,referenced_tweets.id,referenced_tweets.id.author_id,"
    "in_reply_to_user_id,attachments.media_keys,attachments.poll_ids,geo.place_id"
)


class XApiError(Exception):
    def __init__(self, status: int | None, data: Any, headers: dict[str, str] | None = None):
        super().__init__(f"X API request failed with status {status}")
        self.status = status
        self.data = data
        self.headers = headers or {}


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
    """Load X API credentials from os.environ first, then a .env file.

    The lookup order matches the image-generation skill:
      1. os.environ, including external loaders and inline prefixes
      2. The nearest .env file walking up from the current working directory

    When python-dotenv is unavailable, fall back to a minimal parser so direct
    python3 execution still works for simple KEY=VALUE .env files.
    """
    path: Path | None = None
    if env_path:
        path = Path(env_path).expanduser()
    else:
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


def pct(value: Any) -> str:
    return urllib.parse.quote(str(value), safe="~")


def parse_kv(items: list[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def parse_post_ids(values: Iterable[str]) -> list[str]:
    ids: list[str] = []
    for value in values:
        matches = re.findall(r"(?:status/|statuses/)?(\d{5,})", value)
        if matches:
            ids.extend(matches)
        elif value.strip():
            ids.append(value.strip())
    return ids


def rate_limit_headers(headers: dict[str, str]) -> dict[str, str]:
    wanted = {
        "x-rate-limit-limit",
        "x-rate-limit-remaining",
        "x-rate-limit-reset",
    }
    return {k: v for k, v in headers.items() if k.lower() in wanted}


def missing_credentials_message(missing: list[str]) -> str:
    missing_lines = "\n".join(f"  - {key}" for key in missing)
    exports = "\n".join(f"    export {key}=your-value-here" for key in missing)
    env_lines = "\n".join(f"    echo '{key}=your-value-here' >> .env" for key in missing)
    return (
        "ERROR: Required X API credential variables are not set.\n\n"
        f"Missing:\n{missing_lines}\n\n"
        "Set them in one of these ways:\n\n"
        "  Option 1: Create a .env file in your project root\n"
        f"{env_lines}\n"
        "    (and add .env to .gitignore)\n\n"
        "  Option 2: Export them in your shell\n"
        f"{exports}\n\n"
        "  Option 3: Set them inline\n"
        "    X_API_BEARER_TOKEN=your-token-here uv run <command>\n\n"
        "Create and manage keys at https://developer.x.com/."
    )


class XApiClient:
    def __init__(
        self,
        auth: str = "bearer",
        env_path: str | None = None,
        base_url: str = API_BASE,
    ):
        load_env(env_path)
        self.auth = auth
        self.base_url = base_url.rstrip("/")

    def require_auth(self, auth: str | None = None) -> None:
        mode = auth or self.auth
        if mode == "bearer":
            if not os.environ.get("X_API_BEARER_TOKEN"):
                raise SystemExit(missing_credentials_message(["X_API_BEARER_TOKEN"]))
            return
        required = [
            "X_API_CONSUMER_KEY",
            "X_API_CONSUMER_KEY_SECRET",
            "X_API_ACCESS_TOKEN",
            "X_API_ACCESS_TOKEN_SECRET",
        ]
        missing = [key for key in required if not os.environ.get(key)]
        if missing:
            raise SystemExit(missing_credentials_message(missing))

    def _authorization_header(
        self,
        method: str,
        url_without_query: str,
        query_items: list[tuple[str, str]],
        auth: str,
    ) -> str:
        self.require_auth(auth)
        if auth == "bearer":
            return "Bearer " + os.environ["X_API_BEARER_TOKEN"]

        oauth = {
            "oauth_consumer_key": os.environ["X_API_CONSUMER_KEY"],
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": os.environ["X_API_ACCESS_TOKEN"],
            "oauth_version": "1.0",
        }
        signature_items = list(query_items) + list(oauth.items())
        normalized = "&".join(
            f"{pct(key)}={pct(value)}"
            for key, value in sorted(signature_items, key=lambda item: (item[0], item[1]))
        )
        signature_base = "&".join([method.upper(), pct(url_without_query), pct(normalized)])
        signing_key = (
            pct(os.environ["X_API_CONSUMER_KEY_SECRET"])
            + "&"
            + pct(os.environ["X_API_ACCESS_TOKEN_SECRET"])
        )
        digest = hmac.new(signing_key.encode(), signature_base.encode(), hashlib.sha1).digest()
        oauth["oauth_signature"] = base64.b64encode(digest).decode()
        return "OAuth " + ", ".join(
            f'{pct(key)}="{pct(value)}"' for key, value in sorted(oauth.items())
        )

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        auth: str | None = None,
        json_body: Any | None = None,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        method = method.upper()
        if method != "GET":
            raise SystemExit("This research helper only allows GET requests.")
        auth_mode = auth or self.auth
        params = {key: value for key, value in (params or {}).items() if value is not None}

        if path.startswith("http://") or path.startswith("https://"):
            raw_url = path
        else:
            root = (base_url or self.base_url).rstrip("/")
            raw_url = root + (path if path.startswith("/") else "/" + path)

        parts = urllib.parse.urlsplit(raw_url)
        existing_items = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)]
        param_items = existing_items + [(str(k), str(v)) for k, v in params.items()]
        query = urllib.parse.urlencode(param_items)
        url_without_query = urllib.parse.urlunsplit(
            (parts.scheme, parts.netloc, parts.path, "", parts.fragment)
        )
        final_url = urllib.parse.urlunsplit(
            (parts.scheme, parts.netloc, parts.path, query, parts.fragment)
        )

        headers = {
            "Authorization": self._authorization_header(
                method, url_without_query, param_items, auth_mode
            ),
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        body_bytes = None
        if json_body is not None:
            headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(json_body).encode("utf-8")

        req = urllib.request.Request(final_url, data=body_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8", "replace")
                data = json.loads(text) if text else {}
                headers_out = {k.lower(): v for k, v in resp.headers.items()}
                return {
                    "status": resp.status,
                    "data": data,
                    "rate_limit": rate_limit_headers(headers_out),
                }
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace")
            try:
                data = json.loads(text) if text else {}
            except json.JSONDecodeError:
                data = {"raw": text[:2000]}
            headers_out = {k.lower(): v for k, v in exc.headers.items()}
            raise XApiError(exc.code, data, headers_out) from exc
        except urllib.error.URLError as exc:
            raise XApiError(None, {"error": str(exc.reason)}) from exc


def with_default_tweet_params(params: dict[str, Any], no_defaults: bool = False) -> dict[str, Any]:
    if no_defaults:
        return params
    params.setdefault("tweet.fields", DEFAULT_TWEET_FIELDS)
    params.setdefault("user.fields", DEFAULT_USER_FIELDS)
    params.setdefault("media.fields", DEFAULT_MEDIA_FIELDS)
    params.setdefault("place.fields", DEFAULT_PLACE_FIELDS)
    params.setdefault("poll.fields", DEFAULT_POLL_FIELDS)
    params.setdefault("expansions", DEFAULT_TWEET_EXPANSIONS)
    return params


def with_default_user_params(params: dict[str, Any], no_defaults: bool = False) -> dict[str, Any]:
    if no_defaults:
        return params
    params.setdefault("user.fields", DEFAULT_USER_FIELDS)
    params.setdefault("tweet.fields", DEFAULT_TWEET_FIELDS)
    params.setdefault("expansions", "pinned_tweet_id")
    return params


def paginate(
    client: XApiClient,
    path: str,
    params: dict[str, Any],
    max_pages: int,
    auth: str,
    base_url: str | None = None,
) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    next_token: str | None = None
    for _ in range(max_pages):
        page_params = dict(params)
        if next_token:
            page_params["pagination_token"] = next_token
        response = client.request("GET", path, page_params, auth=auth, base_url=base_url)
        pages.append(response)
        data = response.get("data", {})
        meta = data.get("meta", {}) if isinstance(data, dict) else {}
        next_token = meta.get("next_token")
        if not next_token:
            break
    return pages


def collect_data_items(pages: list[dict[str, Any]]) -> list[Any]:
    items: list[Any] = []
    for page in pages:
        data = page.get("data", {})
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            items.extend(data["data"])
    return items


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def print_jsonl_from_pages(pages: list[dict[str, Any]]) -> None:
    for item in collect_data_items(pages):
        print(json.dumps(item, ensure_ascii=False, sort_keys=False))


def client_from_args(args: argparse.Namespace) -> XApiClient:
    return XApiClient(auth=getattr(args, "auth", "bearer"), env_path=getattr(args, "env", None))


def resolve_user_id(client: XApiClient, value: str, auth: str, is_id: bool = False) -> str:
    if is_id or value.isdigit():
        return value
    response = client.request(
        "GET",
        f"/2/users/by/username/{value.lstrip('@')}",
        with_default_user_params({}),
        auth=auth,
    )
    data = response.get("data", {}).get("data", {})
    user_id = data.get("id")
    if not user_id:
        raise SystemExit(f"Could not resolve username to user ID: {value}")
    return user_id


def command_check_auth(args: argparse.Namespace) -> None:
    results: dict[str, Any] = {"checks": []}

    bearer_client = XApiClient(auth="bearer", env_path=args.env)
    try:
        response = bearer_client.request(
            "GET",
            "/2/users/by/username/xdevelopers",
            {"user.fields": "id,username,name"},
            auth="bearer",
        )
        results["checks"].append(
            {
                "auth": "bearer",
                "endpoint": "/2/users/by/username/xdevelopers",
                "ok": True,
                "status": response["status"],
            }
        )
    except XApiError as exc:
        results["checks"].append(
            {
                "auth": "bearer",
                "endpoint": "/2/users/by/username/xdevelopers",
                "ok": False,
                "status": exc.status,
                "error": exc.data,
            }
        )

    oauth_client = XApiClient(auth="oauth1", env_path=args.env)
    try:
        response = oauth_client.request(
            "GET",
            "/1.1/account/verify_credentials.json",
            {"skip_status": "true", "include_entities": "false"},
            auth="oauth1",
        )
        results["checks"].append(
            {
                "auth": "oauth1",
                "endpoint": "/1.1/account/verify_credentials.json",
                "ok": True,
                "status": response["status"],
            }
        )
    except XApiError as exc:
        results["checks"].append(
            {
                "auth": "oauth1",
                "endpoint": "/1.1/account/verify_credentials.json",
                "ok": False,
                "status": exc.status,
                "error": exc.data,
            }
        )

    print_json(results)


def command_request(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = parse_kv(args.param)
    if args.paginate:
        pages = paginate(client, args.path, params, args.max_pages, args.auth, args.base_url)
        if args.jsonl:
            print_jsonl_from_pages(pages)
        else:
            print_json({"pages": pages})
        return
    response = client.request("GET", args.path, params, auth=args.auth, base_url=args.base_url)
    print_json(response if args.include_status else response["data"])


def command_search(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    path = "/2/tweets/search/all" if args.all else "/2/tweets/search/recent"
    params: dict[str, Any] = {
        "query": args.query,
        "max_results": args.max_results,
        "sort_order": args.sort_order,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "since_id": args.since_id,
        "until_id": args.until_id,
    }
    params.update(parse_kv(args.param))
    with_default_tweet_params(params, no_defaults=args.no_default_fields)
    pages = paginate(client, path, params, args.max_pages, args.auth)
    if args.jsonl:
        print_jsonl_from_pages(pages)
    else:
        print_json({"endpoint": path, "query": args.query, "pages": pages})


def command_counts(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    path = "/2/tweets/counts/all" if args.all else "/2/tweets/counts/recent"
    params: dict[str, Any] = {
        "query": args.query,
        "granularity": args.granularity,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "since_id": args.since_id,
        "until_id": args.until_id,
    }
    params.update(parse_kv(args.param))
    pages = paginate(client, path, params, args.max_pages, args.auth)
    print_json({"endpoint": path, "query": args.query, "pages": pages})


def command_user(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = with_default_user_params(parse_kv(args.param), no_defaults=args.no_default_fields)
    if args.me:
        response = client.request("GET", "/2/users/me", params, auth=args.auth)
        print_json(response if args.include_status else response["data"])
        return

    values = [value.lstrip("@") for value in args.values]
    if not values:
        raise SystemExit("Provide at least one username or ID, or use --me.")
    if args.by == "id":
        path = "/2/users" if len(values) > 1 else f"/2/users/{values[0]}"
        if len(values) > 1:
            params["ids"] = ",".join(values)
    else:
        path = "/2/users/by" if len(values) > 1 else f"/2/users/by/username/{values[0]}"
        if len(values) > 1:
            params["usernames"] = ",".join(values)
    response = client.request("GET", path, params, auth=args.auth)
    print_json(response if args.include_status else response["data"])


def command_timeline(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    user_id = resolve_user_id(client, args.user, args.auth, args.id)
    if args.mentions:
        path = f"/2/users/{user_id}/mentions"
    elif args.liked:
        path = f"/2/users/{user_id}/liked_tweets"
    else:
        path = f"/2/users/{user_id}/tweets"
    params: dict[str, Any] = {
        "max_results": args.max_results,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "since_id": args.since_id,
        "until_id": args.until_id,
        "exclude": args.exclude,
    }
    params.update(parse_kv(args.param))
    with_default_tweet_params(params, no_defaults=args.no_default_fields)
    pages = paginate(client, path, params, args.max_pages, args.auth)
    print_json({"endpoint": path, "user_id": user_id, "pages": pages})


def command_post(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    ids = parse_post_ids(args.values)
    if not ids:
        raise SystemExit("Provide at least one post ID or URL.")
    params = {"ids": ",".join(ids)}
    params.update(parse_kv(args.param))
    with_default_tweet_params(params, no_defaults=args.no_default_fields)
    response = client.request("GET", "/2/tweets", params, auth=args.auth)
    print_json(response if args.include_status else response["data"])


def command_post_engagement(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    post_id = parse_post_ids([args.post])[0]
    path_by_type = {
        "liking-users": f"/2/tweets/{post_id}/liking_users",
        "reposted-by": f"/2/tweets/{post_id}/retweeted_by",
        "quotes": f"/2/tweets/{post_id}/quote_tweets",
    }
    path = path_by_type[args.type]
    params: dict[str, Any] = {"max_results": args.max_results}
    params.update(parse_kv(args.param))
    if args.type == "quotes":
        with_default_tweet_params(params, no_defaults=args.no_default_fields)
    else:
        with_default_user_params(params, no_defaults=args.no_default_fields)
    pages = paginate(client, path, params, args.max_pages, args.auth)
    print_json({"endpoint": path, "post_id": post_id, "pages": pages})


def command_follow(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    user_id = resolve_user_id(client, args.user, args.auth, args.id)
    path = f"/2/users/{user_id}/{args.type}"
    params: dict[str, Any] = {"max_results": args.max_results}
    params.update(parse_kv(args.param))
    with_default_user_params(params, no_defaults=args.no_default_fields)
    pages = paginate(client, path, params, args.max_pages, args.auth)
    print_json({"endpoint": path, "user_id": user_id, "pages": pages})


def command_list_posts(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    path = f"/2/lists/{args.list_id}/tweets"
    params: dict[str, Any] = {"max_results": args.max_results}
    params.update(parse_kv(args.param))
    with_default_tweet_params(params, no_defaults=args.no_default_fields)
    pages = paginate(client, path, params, args.max_pages, args.auth)
    print_json({"endpoint": path, "list_id": args.list_id, "pages": pages})


def command_spaces(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params: dict[str, Any] = {
        "query": args.query,
        "state": args.state,
        "max_results": args.max_results,
        "space.fields": (
            "created_at,creator_id,ended_at,host_ids,id,invited_user_ids,is_ticketed,"
            "lang,participant_count,scheduled_start,speaker_ids,started_at,state,"
            "subscriber_count,title,topic_ids,updated_at"
        ),
        "expansions": "creator_id,host_ids,speaker_ids",
        "user.fields": DEFAULT_USER_FIELDS,
    }
    params.update(parse_kv(args.param))
    response = client.request("GET", "/2/spaces/search", params, auth=args.auth)
    print_json(response if args.include_status else response["data"])


def command_trends(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    if args.personalized:
        path = "/2/trends/personalized"
    else:
        path = f"/2/trends/by/woeid/{args.woeid}"
    response = client.request("GET", path, parse_kv(args.param), auth=args.auth)
    print_json(response if args.include_status else response["data"])


def command_news(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params: dict[str, Any] = {"query": args.query, "max_results": args.max_results}
    params.update(parse_kv(args.param))
    response = client.request("GET", "/2/news/search", params, auth=args.auth)
    print_json(response if args.include_status else response["data"])


def command_usage(args: argparse.Namespace) -> None:
    client = client_from_args(args)
    params = parse_kv(args.param)
    response = client.request("GET", "/2/usage/tweets", params, auth=args.auth)
    print_json(response if args.include_status else response["data"])


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    parser.add_argument(
        "--auth",
        choices=["bearer", "oauth1"],
        default="bearer",
        help="Authentication mode. Defaults to bearer.",
    )
    parser.add_argument(
        "--include-status",
        action="store_true",
        help="Include HTTP status and rate-limit metadata in output.",
    )


def add_param_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--param",
        action="append",
        help="Extra query parameter as KEY=VALUE. May be repeated.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only X API research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Check Bearer and OAuth 1.0a credentials.")
    p.add_argument("--env", help="Path to .env file. Defaults to nearest .env.")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("request", help="Call any read-only X API GET endpoint.")
    add_common(p)
    p.add_argument("method", choices=["GET"])
    p.add_argument("path", help="Endpoint path such as /2/tweets/search/recent or full URL.")
    add_param_options(p)
    p.add_argument("--base-url", default=API_BASE)
    p.add_argument("--paginate", action="store_true")
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--jsonl", action="store_true", help="Print page data items as JSONL.")
    p.set_defaults(func=command_request)

    p = sub.add_parser("search", help="Search recent or full-archive posts.")
    add_common(p)
    p.add_argument("query")
    p.add_argument("--all", action="store_true", help="Use full-archive search.")
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--start-time")
    p.add_argument("--end-time")
    p.add_argument("--since-id")
    p.add_argument("--until-id")
    p.add_argument("--sort-order", choices=["recency", "relevancy"], default=None)
    p.add_argument("--no-default-fields", action="store_true")
    p.add_argument("--jsonl", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_search)

    p = sub.add_parser("counts", help="Count recent or full-archive posts by query.")
    add_common(p)
    p.add_argument("query")
    p.add_argument("--all", action="store_true", help="Use full-archive counts.")
    p.add_argument("--granularity", choices=["minute", "hour", "day"], default="hour")
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--start-time")
    p.add_argument("--end-time")
    p.add_argument("--since-id")
    p.add_argument("--until-id")
    add_param_options(p)
    p.set_defaults(func=command_counts)

    p = sub.add_parser("user", help="Look up users.")
    add_common(p)
    p.add_argument("values", nargs="*")
    p.add_argument("--by", choices=["username", "id"], default="username")
    p.add_argument("--me", action="store_true")
    p.add_argument("--no-default-fields", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_user)

    p = sub.add_parser("timeline", help="Fetch user posts, mentions, or liked posts.")
    add_common(p)
    p.add_argument("user")
    p.add_argument("--id", action="store_true", help="Treat user argument as a user ID.")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--mentions", action="store_true")
    group.add_argument("--liked", action="store_true")
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--start-time")
    p.add_argument("--end-time")
    p.add_argument("--since-id")
    p.add_argument("--until-id")
    p.add_argument("--exclude", help="Comma-separated retweets,replies.")
    p.add_argument("--no-default-fields", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_timeline)

    p = sub.add_parser("post", help="Look up posts by ID or URL.")
    add_common(p)
    p.add_argument("values", nargs="+")
    p.add_argument("--no-default-fields", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_post)

    p = sub.add_parser("post-engagement", help="Fetch liking users, reposting users, or quote posts.")
    add_common(p)
    p.add_argument("post")
    p.add_argument("--type", choices=["liking-users", "reposted-by", "quotes"], required=True)
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--no-default-fields", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_post_engagement)

    p = sub.add_parser("follow", help="Fetch followers or following for a user.")
    add_common(p)
    p.add_argument("user")
    p.add_argument("--id", action="store_true")
    p.add_argument("--type", choices=["followers", "following"], required=True)
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--no-default-fields", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_follow)

    p = sub.add_parser("list-posts", help="Fetch posts from an X List.")
    add_common(p)
    p.add_argument("list_id")
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--no-default-fields", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_list_posts)

    p = sub.add_parser("spaces", help="Search Spaces.")
    add_common(p)
    p.add_argument("query")
    p.add_argument("--state", choices=["live", "scheduled", "all"], default="all")
    p.add_argument("--max-results", type=int, default=10)
    add_param_options(p)
    p.set_defaults(func=command_spaces)

    p = sub.add_parser("trends", help="Fetch trends by WOEID or personalized trends.")
    add_common(p)
    p.add_argument("--woeid", default="1", help="WOEID; 1 is worldwide.")
    p.add_argument("--personalized", action="store_true")
    add_param_options(p)
    p.set_defaults(func=command_trends)

    p = sub.add_parser("news", help="Search X News.")
    add_common(p)
    p.add_argument("query")
    p.add_argument("--max-results", type=int, default=10)
    add_param_options(p)
    p.set_defaults(func=command_news)

    p = sub.add_parser("usage", help="Fetch post usage/quota information when available.")
    add_common(p)
    add_param_options(p)
    p.set_defaults(func=command_usage)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except XApiError as exc:
        print_json(
            {
                "ok": False,
                "status": exc.status,
                "error": exc.data,
                "rate_limit": rate_limit_headers(exc.headers),
            }
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
