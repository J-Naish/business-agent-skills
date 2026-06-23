#!/usr/bin/env python3
"""Read-only Google Maps Platform helper for research workflows.

Loads the API key from GOOGLE_MAPS_API in the environment or a nearby .env file.
Credential values and request URLs containing keys are never printed.
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


ENV_KEY = "GOOGLE_MAPS_API"
USER_AGENT = "codex-google-maps-research/1.0.0"

PLACES_SEARCH_FIELD_SETS = {
    "ids": "places.id,places.name,nextPageToken",
    "basic": (
        "places.id,places.name,places.displayName,places.formattedAddress,"
        "places.location,places.primaryType,places.types,places.googleMapsUri,nextPageToken"
    ),
    "research": (
        "places.id,places.name,places.displayName,places.formattedAddress,places.shortFormattedAddress,"
        "places.location,places.viewport,places.primaryType,places.types,places.businessStatus,"
        "places.rating,places.userRatingCount,places.priceLevel,places.priceRange,places.websiteUri,"
        "places.googleMapsUri,places.nationalPhoneNumber,places.internationalPhoneNumber,"
        "places.currentOpeningHours,places.regularOpeningHours,places.utcOffsetMinutes,places.timeZone,"
        "nextPageToken"
    ),
    "atmosphere": (
        "places.id,places.name,places.displayName,places.formattedAddress,places.location,"
        "places.primaryType,places.types,places.businessStatus,places.rating,places.userRatingCount,"
        "places.priceLevel,places.priceRange,places.websiteUri,places.googleMapsUri,"
        "places.nationalPhoneNumber,places.currentOpeningHours,places.regularOpeningHours,"
        "places.editorialSummary,places.reviews,places.reviewSummary,places.generativeSummary,"
        "places.goodForChildren,places.goodForGroups,places.outdoorSeating,places.parkingOptions,"
        "places.paymentOptions,places.reservable,places.delivery,places.dineIn,places.takeout,"
        "nextPageToken"
    ),
    "all": "*",
}

PLACE_DETAIL_FIELD_SETS = {
    "ids": "id,name",
    "basic": "id,name,displayName,formattedAddress,location,primaryType,types,googleMapsUri",
    "research": (
        "id,name,displayName,formattedAddress,shortFormattedAddress,location,viewport,primaryType,types,"
        "businessStatus,rating,userRatingCount,priceLevel,priceRange,websiteUri,googleMapsUri,"
        "nationalPhoneNumber,internationalPhoneNumber,currentOpeningHours,regularOpeningHours,"
        "utcOffsetMinutes,timeZone"
    ),
    "atmosphere": (
        "id,name,displayName,formattedAddress,location,primaryType,types,businessStatus,rating,"
        "userRatingCount,priceLevel,priceRange,websiteUri,googleMapsUri,nationalPhoneNumber,"
        "currentOpeningHours,regularOpeningHours,editorialSummary,reviews,reviewSummary,"
        "generativeSummary,goodForChildren,goodForGroups,outdoorSeating,parkingOptions,"
        "paymentOptions,reservable,delivery,dineIn,takeout"
    ),
    "all": "*",
}

ROUTE_FIELD_SET = (
    "routes.distanceMeters,routes.duration,routes.staticDuration,routes.description,"
    "routes.localizedValues,routes.legs.distanceMeters,routes.legs.duration,"
    "routes.legs.localizedValues,routes.travelAdvisory"
)
ROUTE_MATRIX_FIELD_SET = (
    "originIndex,destinationIndex,status,condition,distanceMeters,duration,staticDuration,"
    "localizedValues,travelAdvisory"
)


class MapsApiError(Exception):
    def __init__(self, status: int | None, data: Any, headers: dict[str, str] | None = None):
        super().__init__(f"Google Maps API request failed with status {status}")
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


def require_api_key(env_path: str | None = None) -> str:
    load_env(env_path)
    key = os.environ.get(ENV_KEY)
    if not key:
        print_json(
            {
                "ok": False,
                "error": "missing_google_maps_api_key",
                "missing": [ENV_KEY],
                "detail": "Define GOOGLE_MAPS_API in the OS environment or a nearby .env file.",
            }
        )
        raise SystemExit(1)
    return key


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def print_jsonl(items: Iterable[Any]) -> None:
    for item in items:
        print(json.dumps(item, ensure_ascii=False, sort_keys=False))


def parse_kv(items: list[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def parse_json(value: str | None) -> Any:
    if not value:
        return None
    if value.startswith("@"):
        return json.loads(Path(value[1:]).expanduser().read_text(encoding="utf-8"))
    return json.loads(value)


def comma_list(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        result.extend(part.strip() for part in value.split(",") if part.strip())
    return result


def parse_lat_lng(value: str) -> tuple[float, float]:
    if "," not in value:
        raise SystemExit(f"Expected LAT,LNG, got: {value}")
    lat, lng = value.split(",", 1)
    return float(lat.strip()), float(lng.strip())


def lat_lng_dict(value: str) -> dict[str, float]:
    lat, lng = parse_lat_lng(value)
    return {"latitude": lat, "longitude": lng}


def lat_lng_object(value: str) -> dict[str, Any]:
    return {"location": {"latLng": lat_lng_dict(value)}}


def sanitize_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    pairs = []
    for key, value in urllib.parse.parse_qsl(parts.query, keep_blank_values=True):
        pairs.append((key, "REDACTED" if key.lower() in {"key", "api_key"} else value))
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(pairs), parts.fragment)
    )


def sanitize_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("REDACTED" if key.lower() in {"key", "x-goog-api-key"} else sanitize_data(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [sanitize_data(item) for item in value]
    return value


def http_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    body: Any = None,
    headers: dict[str, str] | None = None,
    key: str | None = None,
    key_mode: str = "query",
    expect_stream: bool = False,
) -> dict[str, Any]:
    params = {k: v for k, v in (params or {}).items() if v is not None}
    headers = dict(headers or {})
    headers.setdefault("User-Agent", USER_AGENT)
    headers.setdefault("Accept", "application/json")
    if body is not None:
        headers.setdefault("Content-Type", "application/json")
    if key:
        if key_mode == "query":
            params.setdefault("key", key)
        elif key_mode == "header":
            headers.setdefault("X-Goog-Api-Key", key)
        elif key_mode == "both":
            params.setdefault("key", key)
            headers.setdefault("X-Goog-Api-Key", key)

    parts = urllib.parse.urlsplit(url)
    existing = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    query = urllib.parse.urlencode(existing + [(k, str(v)) for k, v in params.items()])
    final_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(final_url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", "replace")
            response_headers = {k.lower(): v for k, v in resp.headers.items()}
            if expect_stream:
                stripped = raw.strip()
                parsed = (
                    json.loads(stripped)
                    if stripped.startswith("[")
                    else [json.loads(line) for line in raw.splitlines() if line.strip()]
                )
            else:
                parsed = json.loads(raw) if raw else {}
            return {
                "status": resp.status,
                "data": parsed,
                "request": {
                    "method": method.upper(),
                    "url": sanitize_url(final_url),
                    "body": sanitize_data(body),
                    "headers": sanitize_data(headers),
                },
                "headers": response_headers,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:2000]}
        raise MapsApiError(
            exc.code,
            {
                "error": sanitize_data(parsed),
                "request": {
                    "method": method.upper(),
                    "url": sanitize_url(final_url),
                    "body": sanitize_data(body),
                    "headers": sanitize_data(headers),
                },
            },
            {k.lower(): v for k, v in exc.headers.items()},
        ) from exc
    except urllib.error.URLError as exc:
        raise MapsApiError(None, {"error": str(exc.reason), "request": {"url": sanitize_url(final_url)}}) from exc


def output_response(response: dict[str, Any], include_request: bool = False) -> None:
    data = response["data"]
    api_status = data.get("status") if isinstance(data, dict) else None
    ok = response["status"] == 200 and api_status in {None, "OK", "ZERO_RESULTS"}
    payload = {
        "ok": ok,
        "status": response["status"],
        "data": data,
    }
    if api_status is not None:
        payload["api_status"] = api_status
    if include_request:
        payload["request"] = response["request"]
    print_json(payload)


def field_mask(value: str | None, field_set: str, sets: dict[str, str]) -> str:
    return value or sets[field_set]


def remove_field_paths(mask: str, paths: set[str]) -> str:
    if mask == "*":
        return mask
    return ",".join(part for part in (item.strip() for item in mask.split(",")) if part and part not in paths)


def output_status_response(response: dict[str, Any], *, endpoint: str) -> None:
    data = response["data"]
    api_status = data.get("status") if isinstance(data, dict) else None
    ok = response["status"] == 200 and api_status in {None, "OK", "ZERO_RESULTS"}
    print_json(
        {
            "ok": ok,
            "status": response["status"],
            "api_status": api_status,
            "endpoint": endpoint,
            "data": data,
        }
    )


def location_bias_or_restriction(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if args.location_bias_circle:
        latlng, radius = args.location_bias_circle.split(":", 1)
        body["locationBias"] = {
            "circle": {"center": lat_lng_dict(latlng), "radius": float(radius)}
        }
    if args.location_restriction_circle:
        latlng, radius = args.location_restriction_circle.split(":", 1)
        body["locationRestriction"] = {
            "circle": {"center": lat_lng_dict(latlng), "radius": float(radius)}
        }
    if body.get("locationBias") and body.get("locationRestriction"):
        raise SystemExit("Use either --location-bias-circle or --location-restriction-circle, not both.")
    return body


def place_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get("places"), list):
        return [item for item in data["places"] if isinstance(item, dict)]
    return []


def command_check_auth(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    response = http_json(
        "GET",
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": args.address, "language": args.language, "region": args.region},
        key=key,
    )
    data = response["data"]
    ok = response["status"] == 200 and isinstance(data, dict) and data.get("status") == "OK"
    print_json(
        {
            "ok": ok,
            "auth": "api_key",
            "env_var": ENV_KEY,
            "endpoint": "Geocoding API",
            "http_status": response["status"],
            "api_status": data.get("status") if isinstance(data, dict) else None,
            "sample_result": (data.get("results") or [{}])[0] if isinstance(data, dict) and data.get("results") else None,
        }
    )


def command_places_text(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    body: dict[str, Any] = {
        "textQuery": args.query,
        "languageCode": args.language_code,
        "regionCode": args.region_code,
        "includedType": args.included_type,
        "strictTypeFiltering": args.strict_type_filtering or None,
        "openNow": args.open_now or None,
        "minRating": args.min_rating,
        "pageSize": args.page_size,
        "pageToken": args.page_token,
        "rankPreference": args.rank_preference,
        "includePureServiceAreaBusinesses": args.include_pure_service_area_businesses or None,
        "includeFutureOpeningBusinesses": args.include_future_opening_businesses or None,
    }
    if args.price_level:
        body["priceLevels"] = comma_list(args.price_level)
    body.update(location_bias_or_restriction(args))
    extra = parse_json(args.body)
    if isinstance(extra, dict):
        body.update(extra)
    body = {k: v for k, v in body.items() if v is not None}
    fields = field_mask(args.fields, args.field_set, PLACES_SEARCH_FIELD_SETS)

    pages = []
    for page_idx in range(max(1, args.max_pages)):
        response = http_json(
            "POST",
            "https://places.googleapis.com/v1/places:searchText",
            body=body,
            headers={"X-Goog-FieldMask": fields},
            key=key,
            key_mode="header",
        )
        pages.append(response["data"])
        token = response["data"].get("nextPageToken") if isinstance(response["data"], dict) else None
        if not token or page_idx + 1 >= args.max_pages:
            break
        body["pageToken"] = token
        time.sleep(args.page_delay)

    if args.jsonl:
        for page in pages:
            print_jsonl(place_items(page))
    else:
        print_json(
            {
                "ok": True,
                "endpoint": "Places API Text Search (New)",
                "query": args.query,
                "field_mask": fields,
                "request_body": sanitize_data(body),
                "pages": pages,
            }
        )


def command_places_nearby(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    body: dict[str, Any] = {
        "locationRestriction": {
            "circle": {"center": lat_lng_dict(args.center), "radius": args.radius}
        },
        "maxResultCount": args.max_results,
        "rankPreference": args.rank_preference,
    }
    if args.included_type:
        body["includedTypes"] = comma_list(args.included_type)
    if args.excluded_type:
        body["excludedTypes"] = comma_list(args.excluded_type)
    if args.included_primary_type:
        body["includedPrimaryTypes"] = comma_list(args.included_primary_type)
    if args.excluded_primary_type:
        body["excludedPrimaryTypes"] = comma_list(args.excluded_primary_type)
    extra = parse_json(args.body)
    if isinstance(extra, dict):
        body.update(extra)
    fields = remove_field_paths(field_mask(args.fields, args.field_set, PLACES_SEARCH_FIELD_SETS), {"nextPageToken"})
    response = http_json(
        "POST",
        "https://places.googleapis.com/v1/places:searchNearby",
        body=body,
        headers={"X-Goog-FieldMask": fields},
        key=key,
        key_mode="header",
    )
    if args.jsonl:
        print_jsonl(place_items(response["data"]))
    else:
        print_json(
            {
                "ok": True,
                "endpoint": "Places API Nearby Search (New)",
                "field_mask": fields,
                "request_body": sanitize_data(body),
                "data": response["data"],
            }
        )


def command_place_details(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    place_id = args.place
    if place_id.startswith("places/"):
        place_id = place_id.split("/", 1)[1]
    fields = field_mask(args.fields, args.field_set, PLACE_DETAIL_FIELD_SETS)
    response = http_json(
        "GET",
        f"https://places.googleapis.com/v1/places/{urllib.parse.quote(place_id)}",
        params={"languageCode": args.language_code, "regionCode": args.region_code, "sessionToken": args.session_token},
        headers={"X-Goog-FieldMask": fields},
        key=key,
        key_mode="header",
    )
    print_json(
        {
            "ok": True,
            "endpoint": "Places API Place Details (New)",
            "place_id": place_id,
            "field_mask": fields,
            "data": response["data"],
        }
    )


def command_places_autocomplete(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    body: dict[str, Any] = {
        "input": args.input,
        "languageCode": args.language_code,
        "regionCode": args.region_code,
        "includedPrimaryTypes": comma_list(args.included_primary_type) or None,
        "includePureServiceAreaBusinesses": args.include_pure_service_area_businesses or None,
        "includeQueryPredictions": args.include_query_predictions or None,
        "sessionToken": args.session_token,
    }
    if args.origin:
        body["origin"] = lat_lng_dict(args.origin)
    body.update(location_bias_or_restriction(args))
    extra = parse_json(args.body)
    if isinstance(extra, dict):
        body.update(extra)
    body = {k: v for k, v in body.items() if v is not None}
    response = http_json(
        "POST",
        "https://places.googleapis.com/v1/places:autocomplete",
        body=body,
        key=key,
        key_mode="header",
    )
    print_json(
        {
            "ok": True,
            "endpoint": "Places API Autocomplete (New)",
            "request_body": sanitize_data(body),
            "data": response["data"],
        }
    )


def command_places_aggregate(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    if args.body:
        body = parse_json(args.body)
    else:
        body = {
            "insights": comma_list(args.insight) or ["INSIGHT_COUNT"],
            "filter": {
                "locationFilter": {
                    "circle": {
                        "latLng": lat_lng_dict(args.center),
                        "radius": args.radius,
                    }
                },
                "typeFilter": {
                    "includedTypes": comma_list(args.included_type) or ["restaurant"],
                },
            },
        }
        if args.min_rating or args.max_rating:
            body["filter"]["ratingFilter"] = {
                "minRating": args.min_rating,
                "maxRating": args.max_rating,
            }
        if args.price_level:
            body["filter"]["priceLevels"] = comma_list(args.price_level)
        if args.operating_status:
            body["filter"]["operatingStatus"] = comma_list(args.operating_status)
    response = http_json(
        "POST",
        "https://areainsights.googleapis.com/v1:computeInsights",
        body=body,
        key=key,
        key_mode="header",
    )
    print_json(
        {
            "ok": True,
            "endpoint": "Places Aggregate API computeInsights",
            "request_body": sanitize_data(body),
            "data": response["data"],
        }
    )


def command_geocode(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    response = http_json(
        "GET",
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "address": args.address,
            "components": args.components,
            "bounds": args.bounds,
            "language": args.language,
            "region": args.region,
            **parse_kv(args.param),
        },
        key=key,
    )
    output_status_response(response, endpoint="Geocoding API")


def command_reverse_geocode(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    response = http_json(
        "GET",
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "latlng": args.latlng,
            "place_id": args.place_id,
            "result_type": args.result_type,
            "location_type": args.location_type,
            "language": args.language,
            "region": args.region,
            **parse_kv(args.param),
        },
        key=key,
    )
    output_status_response(response, endpoint="Geocoding API reverse geocode")


def command_address_validate(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    body = {
        "address": {
            "regionCode": args.region_code,
            "locality": args.locality,
            "administrativeArea": args.administrative_area,
            "postalCode": args.postal_code,
            "addressLines": args.address_line,
        },
        "enableUspsCass": args.enable_usps_cass or None,
        "previousResponseId": args.previous_response_id,
    }
    extra = parse_json(args.body)
    if isinstance(extra, dict):
        body.update(extra)
    body["address"] = {k: v for k, v in body["address"].items() if v}
    body = {k: v for k, v in body.items() if v is not None}
    response = http_json(
        "POST",
        "https://addressvalidation.googleapis.com/v1:validateAddress",
        body=body,
        key=key,
    )
    print_json({"ok": True, "endpoint": "Address Validation API", "request_body": body, "data": response["data"]})


def waypoint(value: str) -> dict[str, Any]:
    if "," in value and not value.startswith("place_id:") and not value.startswith("address:"):
        return lat_lng_object(value)
    if value.startswith("place_id:"):
        return {"placeId": value.split(":", 1)[1]}
    if value.startswith("address:"):
        return {"address": value.split(":", 1)[1]}
    return {"address": value}


def command_route(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    body: dict[str, Any] = {
        "origin": waypoint(args.origin),
        "destination": waypoint(args.destination),
        "travelMode": args.travel_mode,
        "routingPreference": args.routing_preference,
        "computeAlternativeRoutes": args.alternatives,
        "languageCode": args.language_code,
        "regionCode": args.region_code,
        "units": args.units,
        "departureTime": args.departure_time,
        "arrivalTime": args.arrival_time,
    }
    if args.intermediate:
        body["intermediates"] = [waypoint(item) for item in args.intermediate]
    extra = parse_json(args.body)
    if isinstance(extra, dict):
        body.update(extra)
    body = {k: v for k, v in body.items() if v is not None}
    fields = args.fields or ROUTE_FIELD_SET
    response = http_json(
        "POST",
        "https://routes.googleapis.com/directions/v2:computeRoutes",
        body=body,
        headers={"X-Goog-FieldMask": fields},
        key=key,
        key_mode="header",
    )
    print_json(
        {
            "ok": True,
            "endpoint": "Routes API computeRoutes",
            "field_mask": fields,
            "request_body": sanitize_data(body),
            "data": response["data"],
        }
    )


def matrix_point(value: str) -> dict[str, Any]:
    return {"waypoint": waypoint(value)}


def command_route_matrix(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    body: dict[str, Any] = {
        "origins": [matrix_point(item) for item in args.origin],
        "destinations": [matrix_point(item) for item in args.destination],
        "travelMode": args.travel_mode,
        "routingPreference": args.routing_preference,
        "departureTime": args.departure_time,
        "arrivalTime": args.arrival_time,
        "languageCode": args.language_code,
        "regionCode": args.region_code,
        "units": args.units,
    }
    extra = parse_json(args.body)
    if isinstance(extra, dict):
        body.update(extra)
    body = {k: v for k, v in body.items() if v is not None}
    fields = args.fields or ROUTE_MATRIX_FIELD_SET
    response = http_json(
        "POST",
        "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
        body=body,
        headers={"X-Goog-FieldMask": fields},
        key=key,
        key_mode="header",
        expect_stream=True,
    )
    print_json(
        {
            "ok": True,
            "endpoint": "Routes API computeRouteMatrix",
            "field_mask": fields,
            "request_body": sanitize_data(body),
            "items": response["data"],
        }
    )


def command_distance_matrix(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    response = http_json(
        "GET",
        "https://maps.googleapis.com/maps/api/distancematrix/json",
        params={
            "origins": "|".join(args.origin),
            "destinations": "|".join(args.destination),
            "mode": args.mode,
            "language": args.language,
            "region": args.region,
            "units": args.units,
            "departure_time": args.departure_time,
            "arrival_time": args.arrival_time,
            "traffic_model": args.traffic_model,
            **parse_kv(args.param),
        },
        key=key,
    )
    output_response(response)


def command_elevation(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    response = http_json(
        "GET",
        "https://maps.googleapis.com/maps/api/elevation/json",
        params={
            "locations": "|".join(args.location) if args.location else None,
            "path": "|".join(args.path) if args.path else None,
            "samples": args.samples,
        },
        key=key,
    )
    output_response(response)


def command_timezone(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    timestamp = str(int(time.time())) if args.timestamp == "now" else args.timestamp
    response = http_json(
        "GET",
        "https://maps.googleapis.com/maps/api/timezone/json",
        params={
            "location": args.location,
            "timestamp": timestamp,
            "language": args.language,
        },
        key=key,
    )
    output_response(response)


def air_quality_body(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {
        "location": lat_lng_dict(args.location),
        "languageCode": args.language_code,
        "universalAqi": args.universal_aqi if args.universal_aqi else None,
        "extraComputations": comma_list(args.extra_computation) or None,
        "uaqiColorPalette": args.uaqi_color_palette,
        "pageSize": args.page_size,
        "pageToken": args.page_token,
    }
    if args.period_start or args.period_end:
        body["period"] = {"startTime": args.period_start, "endTime": args.period_end}
    if args.date_time:
        body["dateTime"] = args.date_time
    extra = parse_json(args.body)
    if isinstance(extra, dict):
        body.update(extra)
    return {k: v for k, v in body.items() if v is not None}


def command_air_quality(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    endpoint_map = {
        "current": "https://airquality.googleapis.com/v1/currentConditions:lookup",
        "forecast": "https://airquality.googleapis.com/v1/forecast:lookup",
        "history": "https://airquality.googleapis.com/v1/history:lookup",
    }
    body = air_quality_body(args)
    response = http_json("POST", endpoint_map[args.kind], body=body, key=key)
    print_json(
        {
            "ok": True,
            "endpoint": f"Air Quality API {args.kind}",
            "request_body": sanitize_data(body),
            "data": response["data"],
        }
    )


def command_pollen(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    lat, lng = parse_lat_lng(args.location)
    response = http_json(
        "GET",
        "https://pollen.googleapis.com/v1/forecast:lookup",
        params={
            "location.latitude": lat,
            "location.longitude": lng,
            "days": args.days,
            "languageCode": args.language_code,
            "plantsDescription": str(args.plants_description).lower() if args.plants_description is not None else None,
            "pageSize": args.page_size,
            "pageToken": args.page_token,
        },
        key=key,
    )
    output_response(response)


def command_weather_current(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    lat, lng = parse_lat_lng(args.location)
    response = http_json(
        "GET",
        "https://weather.googleapis.com/v1/currentConditions:lookup",
        params={
            "location.latitude": lat,
            "location.longitude": lng,
            "unitsSystem": args.units_system,
            "languageCode": args.language_code,
        },
        key=key,
    )
    output_response(response)


def command_weather(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    lat, lng = parse_lat_lng(args.location)
    endpoint_map = {
        "current": "https://weather.googleapis.com/v1/currentConditions:lookup",
        "hourly": "https://weather.googleapis.com/v1/forecast/hours:lookup",
        "daily": "https://weather.googleapis.com/v1/forecast/days:lookup",
    }
    params = {
        "location.latitude": lat,
        "location.longitude": lng,
        "unitsSystem": args.units_system,
        "languageCode": args.language_code,
        "hours": args.hours,
        "days": args.days,
        "pageSize": args.page_size,
        "pageToken": args.page_token,
    }
    response = http_json("GET", endpoint_map[args.kind], params=params, key=key)
    print_json(
        {
            "ok": True,
            "endpoint": f"Weather API {args.kind}",
            "parameters": {key: value for key, value in params.items() if value is not None},
            "data": response["data"],
        }
    )


def command_solar(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    lat, lng = parse_lat_lng(args.location)
    if args.kind == "building":
        url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
    else:
        url = "https://solar.googleapis.com/v1/dataLayers:get"
    response = http_json(
        "GET",
        url,
        params={
            "location.latitude": lat,
            "location.longitude": lng,
            "requiredQuality": args.required_quality,
            "radiusMeters": args.radius_meters,
            "pixelSizeMeters": args.pixel_size_meters,
            "view": args.view,
        },
        key=key,
    )
    output_response(response)


def command_street_view_metadata(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    response = http_json(
        "GET",
        "https://maps.googleapis.com/maps/api/streetview/metadata",
        params={
            "location": args.location,
            "pano": args.pano,
            "radius": args.radius,
            "source": args.source,
        },
        key=key,
    )
    output_response(response)


def command_roads(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    endpoint_map = {
        "snap": "https://roads.googleapis.com/v1/snapToRoads",
        "nearest": "https://roads.googleapis.com/v1/nearestRoads",
    }
    params = {"path": "|".join(args.path), "interpolate": str(args.interpolate).lower() if args.interpolate else None}
    response = http_json("GET", endpoint_map[args.kind], params=params, key=key)
    output_response(response)


def command_request(args: argparse.Namespace) -> None:
    key = require_api_key(args.env)
    body = parse_json(args.body)
    params = parse_kv(args.param)
    key_mode = args.key_mode
    response = http_json(
        args.method,
        args.url,
        params=params,
        body=body,
        headers=parse_kv(args.header),
        key=key if not args.no_key else None,
        key_mode=key_mode,
        expect_stream=args.stream,
    )
    output_response(response, include_request=args.include_request)


def add_env_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env", help="Path to .env. Defaults to the nearest .env from cwd.")


def add_places_common(parser: argparse.ArgumentParser) -> None:
    add_env_arg(parser)
    parser.add_argument("--field-set", choices=sorted(PLACES_SEARCH_FIELD_SETS), default="research")
    parser.add_argument("--fields", help="Explicit X-Goog-FieldMask. Overrides --field-set.")
    parser.add_argument("--language-code")
    parser.add_argument("--region-code")
    parser.add_argument("--jsonl", action="store_true", help="Print place items as JSON Lines.")
    parser.add_argument("--body", help="Extra JSON object or @file to merge into request body.")


def add_location_bias_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--location-bias-circle", help="LAT,LNG:RADIUS_METERS. Biases results.")
    parser.add_argument("--location-restriction-circle", help="LAT,LNG:RADIUS_METERS. Restricts results.")


def add_route_common(parser: argparse.ArgumentParser) -> None:
    add_env_arg(parser)
    parser.add_argument("--travel-mode", default="DRIVE")
    parser.add_argument("--routing-preference")
    parser.add_argument("--departure-time")
    parser.add_argument("--arrival-time")
    parser.add_argument("--language-code")
    parser.add_argument("--region-code")
    parser.add_argument("--units")
    parser.add_argument("--fields")
    parser.add_argument("--body", help="Extra JSON object or @file to merge into request body.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Google Maps Platform research helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-auth", help="Validate GOOGLE_MAPS_API with a small geocoding request.")
    add_env_arg(p)
    p.add_argument("--address", default="Tokyo Station")
    p.add_argument("--language", default="ja")
    p.add_argument("--region", default="jp")
    p.set_defaults(func=command_check_auth)

    p = sub.add_parser("places-text", help="Places API Text Search (New).")
    add_places_common(p)
    add_location_bias_args(p)
    p.add_argument("query")
    p.add_argument("--included-type")
    p.add_argument("--strict-type-filtering", action="store_true")
    p.add_argument("--open-now", action="store_true")
    p.add_argument("--min-rating", type=float)
    p.add_argument("--price-level", action="append")
    p.add_argument("--rank-preference")
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--page-token")
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--page-delay", type=float, default=2.0)
    p.add_argument("--include-pure-service-area-businesses", action="store_true")
    p.add_argument("--include-future-opening-businesses", action="store_true")
    p.set_defaults(func=command_places_text)

    p = sub.add_parser("places-nearby", help="Places API Nearby Search (New).")
    add_places_common(p)
    p.add_argument("center", help="LAT,LNG")
    p.add_argument("--radius", type=float, default=1000)
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--included-type", action="append")
    p.add_argument("--excluded-type", action="append")
    p.add_argument("--included-primary-type", action="append")
    p.add_argument("--excluded-primary-type", action="append")
    p.add_argument("--rank-preference")
    p.set_defaults(func=command_places_nearby)

    p = sub.add_parser("place-details", help="Places API Place Details (New).")
    add_env_arg(p)
    p.add_argument("place", help="Place ID or places/PLACE_ID resource.")
    p.add_argument("--field-set", choices=sorted(PLACE_DETAIL_FIELD_SETS), default="research")
    p.add_argument("--fields")
    p.add_argument("--language-code")
    p.add_argument("--region-code")
    p.add_argument("--session-token")
    p.set_defaults(func=command_place_details)

    p = sub.add_parser("places-autocomplete", help="Places API Autocomplete (New).")
    add_env_arg(p)
    add_location_bias_args(p)
    p.add_argument("input")
    p.add_argument("--language-code")
    p.add_argument("--region-code")
    p.add_argument("--included-primary-type", action="append")
    p.add_argument("--origin", help="LAT,LNG")
    p.add_argument("--include-pure-service-area-businesses", action="store_true")
    p.add_argument("--include-query-predictions", action="store_true")
    p.add_argument("--session-token")
    p.add_argument("--body")
    p.set_defaults(func=command_places_autocomplete)

    p = sub.add_parser("places-aggregate", help="Places Aggregate API computeInsights.")
    add_env_arg(p)
    p.add_argument("--body", help="Full JSON request body or @file.")
    p.add_argument("--center", default="35.681236,139.767125", help="LAT,LNG, used when --body is omitted.")
    p.add_argument("--radius", type=float, default=1000)
    p.add_argument("--included-type", action="append")
    p.add_argument("--insight", action="append", default=["INSIGHT_COUNT"])
    p.add_argument("--min-rating", type=float)
    p.add_argument("--max-rating", type=float)
    p.add_argument("--price-level", action="append")
    p.add_argument("--operating-status", action="append")
    p.set_defaults(func=command_places_aggregate)

    p = sub.add_parser("geocode", help="Forward geocode an address.")
    add_env_arg(p)
    p.add_argument("address")
    p.add_argument("--components")
    p.add_argument("--bounds")
    p.add_argument("--language")
    p.add_argument("--region")
    p.add_argument("--param", action="append")
    p.set_defaults(func=command_geocode)

    p = sub.add_parser("reverse-geocode", help="Reverse geocode coordinates or a place_id.")
    add_env_arg(p)
    p.add_argument("--latlng", help="LAT,LNG")
    p.add_argument("--place-id")
    p.add_argument("--result-type")
    p.add_argument("--location-type")
    p.add_argument("--language")
    p.add_argument("--region")
    p.add_argument("--param", action="append")
    p.set_defaults(func=command_reverse_geocode)

    p = sub.add_parser("address-validate", help="Address Validation API.")
    add_env_arg(p)
    p.add_argument("address_line", nargs="+")
    p.add_argument("--region-code")
    p.add_argument("--locality")
    p.add_argument("--administrative-area")
    p.add_argument("--postal-code")
    p.add_argument("--enable-usps-cass", action="store_true")
    p.add_argument("--previous-response-id")
    p.add_argument("--body")
    p.set_defaults(func=command_address_validate)

    p = sub.add_parser("route", help="Routes API computeRoutes.")
    add_route_common(p)
    p.add_argument("origin", help="Address, LAT,LNG, place_id:ID, or address:TEXT.")
    p.add_argument("destination", help="Address, LAT,LNG, place_id:ID, or address:TEXT.")
    p.add_argument("--intermediate", action="append")
    p.add_argument("--alternatives", action="store_true")
    p.set_defaults(func=command_route)

    p = sub.add_parser("route-matrix", help="Routes API computeRouteMatrix.")
    add_route_common(p)
    p.add_argument("--origin", action="append", required=True)
    p.add_argument("--destination", action="append", required=True)
    p.set_defaults(func=command_route_matrix)

    p = sub.add_parser("distance-matrix", help="Distance Matrix API (Legacy), useful for address strings.")
    add_env_arg(p)
    p.add_argument("--origin", action="append", required=True)
    p.add_argument("--destination", action="append", required=True)
    p.add_argument("--mode")
    p.add_argument("--language")
    p.add_argument("--region")
    p.add_argument("--units")
    p.add_argument("--departure-time")
    p.add_argument("--arrival-time")
    p.add_argument("--traffic-model")
    p.add_argument("--param", action="append")
    p.set_defaults(func=command_distance_matrix)

    p = sub.add_parser("elevation", help="Elevation API for points or paths.")
    add_env_arg(p)
    p.add_argument("--location", action="append", help="LAT,LNG. Repeatable.")
    p.add_argument("--path", action="append", help="LAT,LNG path point. Repeatable.")
    p.add_argument("--samples", type=int)
    p.set_defaults(func=command_elevation)

    p = sub.add_parser("timezone", help="Time Zone API.")
    add_env_arg(p)
    p.add_argument("location", help="LAT,LNG")
    p.add_argument("--timestamp", default="now")
    p.add_argument("--language")
    p.set_defaults(func=command_timezone)

    p = sub.add_parser("air-quality", help="Air Quality API current, forecast, or history.")
    add_env_arg(p)
    p.add_argument("kind", choices=["current", "forecast", "history"])
    p.add_argument("location", help="LAT,LNG")
    p.add_argument("--language-code")
    p.add_argument("--universal-aqi", action="store_true")
    p.add_argument("--extra-computation", action="append")
    p.add_argument("--uaqi-color-palette")
    p.add_argument("--date-time")
    p.add_argument("--period-start")
    p.add_argument("--period-end")
    p.add_argument("--page-size", type=int)
    p.add_argument("--page-token")
    p.add_argument("--body")
    p.set_defaults(func=command_air_quality)

    p = sub.add_parser("pollen", help="Pollen API forecast.")
    add_env_arg(p)
    p.add_argument("location", help="LAT,LNG")
    p.add_argument("--days", type=int, default=1)
    p.add_argument("--language-code")
    p.add_argument("--plants-description", type=lambda v: v.lower() in {"1", "true", "yes"}, default=None)
    p.add_argument("--page-size", type=int)
    p.add_argument("--page-token")
    p.set_defaults(func=command_pollen)

    p = sub.add_parser("weather", help="Weather API current conditions, hourly forecast, or daily forecast.")
    add_env_arg(p)
    p.add_argument("kind", choices=["current", "hourly", "daily"])
    p.add_argument("location", help="LAT,LNG")
    p.add_argument("--units-system")
    p.add_argument("--language-code")
    p.add_argument("--hours", type=int)
    p.add_argument("--days", type=int)
    p.add_argument("--page-size", type=int)
    p.add_argument("--page-token")
    p.set_defaults(func=command_weather)

    p = sub.add_parser("weather-current", help="Weather API current conditions. Prefer `weather current`.")
    add_env_arg(p)
    p.add_argument("location", help="LAT,LNG")
    p.add_argument("--units-system")
    p.add_argument("--language-code")
    p.set_defaults(func=command_weather_current)

    p = sub.add_parser("solar", help="Solar API building insights or data layers.")
    add_env_arg(p)
    p.add_argument("kind", choices=["building", "data-layers"])
    p.add_argument("location", help="LAT,LNG")
    p.add_argument("--required-quality")
    p.add_argument("--radius-meters", type=float)
    p.add_argument("--pixel-size-meters", type=float)
    p.add_argument("--view")
    p.set_defaults(func=command_solar)

    p = sub.add_parser("street-view-metadata", help="Street View Static API metadata.")
    add_env_arg(p)
    p.add_argument("--location")
    p.add_argument("--pano")
    p.add_argument("--radius", type=int)
    p.add_argument("--source")
    p.set_defaults(func=command_street_view_metadata)

    p = sub.add_parser("roads", help="Roads API snapToRoads or nearestRoads.")
    add_env_arg(p)
    p.add_argument("kind", choices=["snap", "nearest"])
    p.add_argument("--path", action="append", required=True, help="LAT,LNG. Repeatable.")
    p.add_argument("--interpolate", action="store_true")
    p.set_defaults(func=command_roads)

    p = sub.add_parser("request", help="Generic read-only Google Maps Platform JSON request.")
    add_env_arg(p)
    p.add_argument("method", choices=["GET", "POST"])
    p.add_argument("url")
    p.add_argument("--param", action="append")
    p.add_argument("--header", action="append")
    p.add_argument("--body", help="JSON body or @file.")
    p.add_argument("--key-mode", choices=["query", "header", "both"], default="query")
    p.add_argument("--no-key", action="store_true")
    p.add_argument("--stream", action="store_true")
    p.add_argument("--include-request", action="store_true")
    p.set_defaults(func=command_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
        return 0
    except SystemExit:
        raise
    except MapsApiError as exc:
        print_json({"ok": False, "status": exc.status, "error": exc.data})
        return 1
    except Exception as exc:
        print_json({"ok": False, "error_type": exc.__class__.__name__, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
