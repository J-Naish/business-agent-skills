# Google Maps Research Workflows

Use this reference when choosing a Google Maps Platform endpoint, composing a request, or reporting API-backed local/geospatial research.

## Research Stance

- Prefer read-only endpoints.
- Print fetched data and errors to stdout only.
- Request only the fields needed for the research question.
- Keep endpoint, field mask, query, coordinates, radius, filters, route mode, and sample size in the answer.
- Do not expose `.env` values, API keys, request URLs containing keys, or secret-bearing headers.
- Respect Google Maps Platform terms and product policies; do not treat Places content as a free bulk database.

## Field Sets

Places commands support `--field-set`:

| Field set | Use |
|---|---|
| `ids` | Cheapest identity lookup: IDs/resource names only. |
| `basic` | Name, address, location, type, Google Maps URL. |
| `research` | Default. Adds business status, rating, review count, price, website, phone, hours, timezone. |
| `atmosphere` | Adds reviews/summaries and amenity-style attributes where available. More expensive. |
| `all` | Uses `*`; useful only for debugging. Avoid for routine research. |

Use `--fields` to pass an explicit field mask when cost or API behavior needs tighter control.

## Command Patterns

### Credential check

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py check-auth
```

### Local competitor or market scan

```bash
uv run skills/google-maps-research/scripts/local_market_scan.py \
  "渋谷駅 カフェ" \
  --center 35.658034,139.701636 \
  --radius 1000 \
  --included-type cafe \
  --language-code ja \
  --region-code JP
```

### Text place search

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py places-text \
  "美容クリニック 新宿" \
  --language-code ja \
  --region-code JP \
  --field-set research \
  --page-size 20 \
  --max-pages 1
```

### Nearby amenity search

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py places-nearby \
  35.681236,139.767125 \
  --radius 1000 \
  --included-type cafe \
  --rank-preference POPULARITY
```

### Place details

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py place-details \
  ChIJ51cu8IcbXWARiRtXIothAS4 \
  --field-set research \
  --language-code ja \
  --region-code JP
```

### Places Aggregate count

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py places-aggregate \
  --center 35.658034,139.701636 \
  --radius 1000 \
  --included-type cafe \
  --min-rating 4.0
```

For complex aggregate filters, pass the official JSON body:

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py places-aggregate \
  --body '{"insights":["INSIGHT_COUNT"],"filter":{"locationFilter":{"circle":{"latLng":{"latitude":35.658034,"longitude":139.701636},"radius":1000}},"typeFilter":{"includedTypes":["cafe"]}}}'
```

### Geocoding

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py geocode \
  "東京都千代田区丸の内1丁目"

uv run skills/google-maps-research/scripts/google_maps_api.py reverse-geocode \
  --latlng 35.681236,139.767125 \
  --language ja \
  --region jp
```

### Route and route matrix

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py route \
  "東京駅" "渋谷駅" \
  --travel-mode TRANSIT \
  --language-code ja

uv run skills/google-maps-research/scripts/google_maps_api.py route-matrix \
  --origin "東京駅" \
  --destination "渋谷駅" \
  --destination "新宿駅" \
  --travel-mode TRANSIT \
  --language-code ja
```

### Address validation

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py address-validate \
  "1600 Amphitheatre Pkwy" \
  --region-code US \
  --locality "Mountain View"
```

### Local environment and context

```bash
uv run skills/google-maps-research/scripts/google_maps_api.py elevation \
  --location 35.681236,139.767125

uv run skills/google-maps-research/scripts/google_maps_api.py timezone \
  35.681236,139.767125

uv run skills/google-maps-research/scripts/google_maps_api.py air-quality current \
  35.681236,139.767125 \
  --extra-computation LOCAL_AQI \
  --extra-computation POLLUTANT_CONCENTRATION \
  --language-code ja

uv run skills/google-maps-research/scripts/google_maps_api.py pollen \
  35.681236,139.767125 \
  --days 3 \
  --language-code ja

uv run skills/google-maps-research/scripts/google_maps_api.py weather-current \
  35.681236,139.767125 \
  --language-code ja

uv run skills/google-maps-research/scripts/google_maps_api.py weather hourly \
  35.681236,139.767125 \
  --hours 12 \
  --page-size 12 \
  --language-code ja

uv run skills/google-maps-research/scripts/google_maps_api.py weather daily \
  35.681236,139.767125 \
  --days 3 \
  --language-code ja

uv run skills/google-maps-research/scripts/google_maps_api.py street-view-metadata \
  --location 35.681236,139.767125 \
  --radius 50
```

## Endpoint Map

| Research need | Default command or API |
|---|---|
| Business/facility discovery by text | `places-text` -> Places API Text Search (New) |
| Amenities around a coordinate | `places-nearby` -> Places API Nearby Search (New) |
| Deep details for one place | `place-details` -> Places API Place Details (New) |
| Place disambiguation | `places-autocomplete` -> Places API Autocomplete (New) |
| Count/density by area/type/rating | `places-aggregate` -> Places Aggregate API |
| Address to coordinates | `geocode` -> Geocoding API |
| Coordinates to address | `reverse-geocode` -> Geocoding API |
| Address deliverability/standardization | `address-validate` -> Address Validation API |
| One route | `route` -> Routes API computeRoutes |
| Many origin/destination travel-time matrix | `route-matrix` -> Routes API computeRouteMatrix |
| Address-string matrix convenience | `distance-matrix` -> Distance Matrix API (Legacy) |
| Elevation/terrain | `elevation` -> Elevation API |
| Local timezone | `timezone` -> Time Zone API |
| Air quality now/forecast/history | `air-quality` -> Air Quality API |
| Pollen forecast | `pollen` -> Pollen API |
| Current/hourly/daily weather | `weather` -> Weather API currentConditions / forecast.hours / forecast.days |
| Solar/building data | `solar` -> Solar API |
| Street View availability | `street-view-metadata` -> Street View Static API metadata |
| Road snapping/nearest roads | `roads` -> Roads API |
| Uncommon JSON endpoint | `request` | Generic read-only escape hatch |

## Reporting Caveats

Always state the main constraints:

- Places search is ranked/sampled and not necessarily exhaustive.
- Places Text Search returns up to the documented page/result limits; pagination and ranking affect coverage.
- Ratings, review counts, business status, hours, and websites are point-in-time snapshots.
- Field masks affect both what is returned and billing.
- Some APIs must be enabled separately in Google Cloud; a valid key can still receive `REQUEST_DENIED` or permission errors for disabled APIs.
- Places Aggregate may return counts or Place IDs depending on insight type and result size.
- Distance Matrix is legacy; use Routes API route matrix when possible.
- Environment APIs have geographic coverage limits.
- Google Maps Platform data has terms and product-policy restrictions around caching, display, and attribution.

## Official Docs

- Google Maps Platform docs: https://developers.google.com/maps/documentation
- Places Text Search (New): https://developers.google.com/maps/documentation/places/web-service/text-search
- Places Nearby Search (New): https://developers.google.com/maps/documentation/places/web-service/nearby-search
- Places Details (New): https://developers.google.com/maps/documentation/places/web-service/place-details
- Places Aggregate API: https://developers.google.com/maps/documentation/places-aggregate/overview
- Geocoding API: https://developers.google.com/maps/documentation/geocoding
- Address Validation API: https://developers.google.com/maps/documentation/address-validation
- Routes API: https://developers.google.com/maps/documentation/routes
- Elevation API: https://developers.google.com/maps/documentation/elevation
- Time Zone API: https://developers.google.com/maps/documentation/timezone
- Air Quality API: https://developers.google.com/maps/documentation/air-quality
- Pollen API: https://developers.google.com/maps/documentation/pollen
- Weather API: https://developers.google.com/maps/documentation/weather
- Solar API: https://developers.google.com/maps/documentation/solar
- Street View Static API metadata: https://developers.google.com/maps/documentation/streetview/metadata
- Roads API: https://developers.google.com/maps/documentation/roads
