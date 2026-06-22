# e-Stat Workflows

Use this reference when researching Japanese official statistics with `scripts/estat_api.py`.

## Research Stance

- Prefer `getStatsList -> getMetaInfo -> getStatsData`.
- Search broadly only once, then work from stable `statsDataId` values.
- Cache or record useful table IDs in notes when a table is found; e-Stat keyword search can be slow.
- Always inspect class codes before fetching data.
- Treat units and labels as table-specific. The same table can mix yen, percent, counts, or index units.
- All commands write fetched data to stdout only.
- Do not expose `ESTAT_APP_ID`, full signed request URLs, or `.env` values.

## Command Patterns

### Credential check

```bash
python3 skills/public-data-research/scripts/estat_api.py check-auth
```

### Search statistics tables

```bash
python3 skills/public-data-research/scripts/estat_api.py search "家計調査" --limit 10
python3 skills/public-data-research/scripts/estat_api.py search "住宅・土地統計調査" --limit 10
```

Use Japanese search terms when possible. English terms can work poorly because e-Stat metadata is often Japanese.

### Inspect table metadata

```bash
python3 skills/public-data-research/scripts/estat_api.py meta 0002070001
python3 skills/public-data-research/scripts/estat_api.py meta 0002070001 --find "外食"
python3 skills/public-data-research/scripts/estat_api.py meta 0002070001 --class-id cat01 --limit 30
```

### Fetch data with explicit codes

```bash
python3 skills/public-data-research/scripts/estat_api.py data 0002070001 \
  --filter cdCat01=098 \
  --filter cdCat02=03 \
  --filter cdArea=00000 \
  --latest-time
```

### Export data

```bash
python3 skills/public-data-research/scripts/estat_api.py data 0002070001 \
  --filter cdCat01=098 \
  --filter cdCat02=03 \
  --filter cdArea=00000 \
  --csv
```

### Direct read-only endpoint

```bash
python3 skills/public-data-research/scripts/estat_api.py request getStatsData \
  --param statsDataId=0002070001 \
  --param cdCat01=098 \
  --param cdCat02=03 \
  --param cdArea=00000
```

## Endpoint Map

| Research need | Default command or endpoint |
|---|---|
| Find tables | `estat_api.py search QUERY` -> `getStatsList` |
| Inspect dimensions/codes | `estat_api.py meta STATS_DATA_ID` -> `getMetaInfo` |
| Fetch values | `estat_api.py data STATS_DATA_ID` -> `getStatsData` |
| Direct endpoint | `estat_api.py request ENDPOINT` | Use for supported read-only e-Stat endpoints. |

## Useful Starting Tables

These IDs are examples discovered from the API and should still be verified with `meta` before use.

| Topic | statsDataId | Notes |
|---|---|---|
| Family Income and Expenditure Survey, two-or-more-person households | `0002070001` | Monthly household spending categories; useful for dining out, beauty services, communications, tobacco, alcohol, rent, education, recreation. |
| Housing and Land Survey | `0000081942` and nearby IDs | Housing counts, vacant housing, ownership, building type, household type, regional tables. |
| Population Estimates | `0000150002` | Population by age group, sex, year, national. Basic but useful for sanity checks. |

## Reporting Caveats

Always state:

- `statsDataId`, endpoint, filters, and labels.
- Whether data is monthly, annual, national, prefectural, municipal, or another geography.
- Unit and whether the unit is attached to the value, category, or time class.
- Revision/update date if relevant.
- Whether the table is a survey estimate, administrative count, index, percentage, or currency value.
- That keyword search can miss tables; table IDs and metadata inspection are more reliable than search snippets.

## Official Docs

- e-Stat API: https://www.e-stat.go.jp/api/
- e-Stat API developer guide: https://www.e-stat.go.jp/api/api-dev/dev_guide
