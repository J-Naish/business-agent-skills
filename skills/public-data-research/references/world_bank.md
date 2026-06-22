# World Bank Workflows

Use this reference when researching international country/economy indicators with `scripts/world_bank_api.py`.

## Research Stance

- No API key is required for the World Bank Indicators API.
- Use `format=json` and the v2 endpoint shape.
- All commands write fetched data to stdout only.
- Use source `2` for World Development Indicators unless another source is needed.
- Search indicators first, then fetch data by stable indicator code.
- Treat country and region aggregates as economies returned by the API; verify whether a code is a country, region, or income group before comparing.
- Always report `sourceid`, `lastupdated`, date range, and whether null values were returned.

## Command Patterns

### API check

```bash
python3 skills/public-data-research/scripts/world_bank_api.py check-auth
```

### Find countries or regions

```bash
python3 skills/public-data-research/scripts/world_bank_api.py countries Japan
python3 skills/public-data-research/scripts/world_bank_api.py countries "East Asia"
```

### Search indicators

```bash
python3 skills/public-data-research/scripts/world_bank_api.py indicators "gdp per capita" --limit 10
python3 skills/public-data-research/scripts/world_bank_api.py indicators "internet" --source 2 --limit 10
```

The indicator command fetches the indicator catalog, then filters locally. It defaults to source `2`, World Development Indicators.

### Fetch indicator data

```bash
python3 skills/public-data-research/scripts/world_bank_api.py data NY.GDP.PCAP.CD JPN KOR USA --date 2020:2024
python3 skills/public-data-research/scripts/world_bank_api.py data SP.POP.TOTL JPN --mrv 5
python3 skills/public-data-research/scripts/world_bank_api.py data IT.NET.USER.ZS JPN KOR USA --mrnev 5
```

### Export data

```bash
python3 skills/public-data-research/scripts/world_bank_api.py data NY.GDP.PCAP.CD JPN KOR USA --date 2020:2024 --csv
```

### Direct read-only endpoint

```bash
python3 skills/public-data-research/scripts/world_bank_api.py request /country/JPN/indicator/SP.POP.TOTL --param mrv=3
```

## Endpoint Map

| Research need | Default command or endpoint |
|---|---|
| API check | `world_bank_api.py check-auth` -> `/v2/country/JPN/indicator/SP.POP.TOTL` |
| Countries/economies | `world_bank_api.py countries` -> `/v2/country` |
| Sources | `world_bank_api.py sources` -> `/v2/source` |
| Indicators | `world_bank_api.py indicators QUERY` -> `/v2/source/2/indicator` by default |
| Data values | `world_bank_api.py data INDICATOR COUNTRIES...` -> `/v2/country/{codes}/indicator/{indicator}` |
| Direct endpoint | `world_bank_api.py request PATH` | Use for uncommon v2 paths. |

## Reporting Caveats

Always state:

- Indicator code and source ID, usually WDI source `2`.
- Countries/economies requested and whether any are aggregate regions.
- Date range, `mrv`, or `mrnev` parameter used.
- `lastupdated` from API metadata when returned.
- Null values and gaps in country-year coverage.
- That data definitions follow the indicator metadata and source organization.

## Official Docs

- World Bank Indicators API overview: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation
- World Bank API basic call structures: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures
