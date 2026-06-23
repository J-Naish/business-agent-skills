---
name: google-maps-research
description: "Research locations, local markets, competitors, routes, addresses, amenities, and environmental context using Google Maps Platform APIs. Use when the user asks for Google Maps API research, Places/Maps business or facility lookup, local competitor scans, store density, ratings and review counts, opening hours, geocoding, reverse geocoding, address validation, travel time or route matrix comparison, elevation, timezone, Street View metadata, roads, air quality, pollen, weather, solar, or any read-only location intelligence investigation backed by Google Maps Platform."
---

# Google Maps Research

Use Google Maps Platform APIs for read-only local and geospatial research: place discovery, competitor lists, ratings, review counts, opening hours, websites, phone numbers, geocoding, route and travel-time comparison, local density counts, address validation, terrain, timezone, road, Street View metadata, and environmental context.

Prefer API-backed evidence over browser scraping. Keep the exact query, endpoint, field mask, geo/radius, route mode, language/region, and sample limits visible in the final answer.

## Directory Layout

```text
google-maps-research/
├── SKILL.md
├── scripts/
│   ├── google_maps_api.py    # Generic Google Maps Platform CLI
│   └── local_market_scan.py  # Places-based local competitor/market summary
└── references/
    └── workflows.md          # Command patterns, endpoint map, and caveats
```

## Prerequisites

- **Python 3.10+** must be installed.
- Google Maps Platform credentials are assumed to already be available from the OS environment or a nearby `.env` file.
- Do not print, inspect, edit, or commit secret values.

Supported environment variable:

```text
GOOGLE_MAPS_API
```

This skill intentionally uses `GOOGLE_MAPS_API` only. Do not fall back to other variable names unless the user explicitly requests it.

### How to run the scripts

The scripts are written as PEP 723 inline scripts. Their dependency (`python-dotenv`) is declared at the top of each file. Any of the following invocation styles works:

```bash
# Option A: uv (recommended)
uv run <skill-dir>/scripts/google_maps_api.py check-auth

# Option B: pipx
pipx run <skill-dir>/scripts/google_maps_api.py check-auth

# Option C: pip + plain python
pip install python-dotenv
python3 <skill-dir>/scripts/google_maps_api.py check-auth
```

The command examples below use `uv run`, but plain `python3` runs the same scripts when dependencies are already available.

## Quick Start

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py check-auth

uv run skills/google-maps-research/scripts/local_market_scan.py \
  "渋谷駅 カフェ" \
  --center 35.658034,139.701636 \
  --radius 1000 \
  --included-type cafe

uv run skills/google-maps-research/scripts/google_maps_api.py places-text \
  "美容クリニック 新宿" \
  --language-code ja \
  --region-code JP \
  --page-size 20

uv run skills/google-maps-research/scripts/google_maps_api.py route-matrix \
  --origin "東京駅" \
  --destination "渋谷駅" \
  --destination "新宿駅" \
  --travel-mode TRANSIT
```

For endpoint selection, field-mask guidance, and caveats, read [references/workflows.md](references/workflows.md).

## Workflow

1. Translate the request into a research unit:
   - Local competitors, facility lists, ratings, and opening hours: use `local_market_scan.py` or `google_maps_api.py places-text`.
   - Nearby amenities around a coordinate: use `google_maps_api.py places-nearby`.
   - Store/facility detail by Place ID: use `google_maps_api.py place-details`.
   - Place density/counts by area/type/rating: use `google_maps_api.py places-aggregate`.
   - Address normalization: use `geocode`, `reverse-geocode`, or `address-validate`.
   - Travel-time/access comparison: use `route`, `route-matrix`, or `distance-matrix`.
   - Terrain/local context: use `elevation`, `timezone`, `street-view-metadata`, `roads`, `air-quality`, `pollen`, `weather`, or `solar`.
   - Newly added or uncommon read-only endpoint: use `google_maps_api.py request`.
2. Start narrow. Request only the fields needed for the task. Places APIs require field masks; field selection affects response size and billing.
3. Preserve the research parameters:
   - Query or Place ID
   - Endpoint and field mask
   - Coordinate, radius, bias/restriction, region/language
   - Route origins/destinations, mode, departure/arrival time
   - Page size, page count, and sample size
4. Analyze returned data:
   - Place names, categories, addresses, coordinates, business status
   - Ratings, review counts, price levels, websites, phone numbers, opening hours
   - Local density/counts from Places Aggregate
   - Travel time, distance, route alternatives, route matrix comparisons
   - Address validity, geocode precision, elevation, timezone, weather, air quality, pollen, solar, and Street View availability
5. Report caveats clearly. Google Maps results are sampled/ranked, field masks and enabled APIs matter, Places data has caching/display restrictions, and public metrics are point-in-time snapshots.

## Script Selection

| Task | Script | Notes |
|---|---|---|
| Check API key | `google_maps_api.py check-auth` | Uses a minimal Geocoding request without printing the key. |
| Local competitor scan | `local_market_scan.py QUERY` | Summarizes Places results: count, rating, review count, types, websites, top places. |
| Text place search | `google_maps_api.py places-text QUERY` | Places Text Search (New). Supports field sets, location bias/restriction, type, pages, JSONL. |
| Nearby place search | `google_maps_api.py places-nearby LAT,LNG` | Places Nearby Search (New). Good for amenities around a point. |
| Place details | `google_maps_api.py place-details PLACE_ID` | Fetch details for a known Place ID. |
| Autocomplete | `google_maps_api.py places-autocomplete INPUT` | Useful for place/entity disambiguation. |
| Aggregate counts | `google_maps_api.py places-aggregate` | Count or identify places by area/type/rating/price. |
| Geocode | `google_maps_api.py geocode ADDRESS` | Address to coordinates and structured address components. |
| Reverse geocode | `google_maps_api.py reverse-geocode --latlng LAT,LNG` | Coordinates to address candidates. |
| Address validation | `google_maps_api.py address-validate` | Validate/standardize postal addresses. |
| Route | `google_maps_api.py route ORIGIN DESTINATION` | Single route and travel-time analysis. |
| Route matrix | `google_maps_api.py route-matrix` | Many origins/destinations comparison. |
| Distance matrix | `google_maps_api.py distance-matrix` | Legacy but convenient for address-string matrices. |
| Elevation / Timezone | `google_maps_api.py elevation`, `timezone` | Terrain and local time context. |
| Environment | `google_maps_api.py air-quality`, `pollen`, `weather`, `solar` | Air quality, pollen, current/hourly/daily weather, building solar data. |
| Road/Street View | `google_maps_api.py roads`, `street-view-metadata` | Road matching and Street View availability. |
| Raw endpoint | `google_maps_api.py request` | Generic read-only escape hatch for supported JSON endpoints. |

## Output Standards

When answering the user, include:

- The exact endpoint/script used.
- The query, place ID, address, coordinates, radius, route origins/destinations, and filters.
- The field mask or field set used.
- The number of returned places/routes/items and page count.
- Findings separated from caveats.
- Links to Google Maps when `googleMapsUri` or Place IDs are available.

Do not claim the result is a complete census unless the endpoint and pagination semantics support that claim. Do not expose API keys, request URLs containing keys, or secret-bearing headers.
