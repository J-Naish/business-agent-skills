---
name: public-data-research
description: "Research official statistics and public datasets using source-specific read-only APIs and public bulk data including Japan e-Stat, World Bank Indicators, IMF DataMapper, Bank of Japan, OECD SDMX, BIS, FAOSTAT, and GDELT. Use when the user asks for statistical data, government statistics, macro indicators, market or regional data, household spending, prices, employment, demographics, industry counts, international country indicators, GDP, development indicators, monetary/financial data, food/agriculture data, media/news signals, business environment analysis, time-series public data, e-Stat lookup, World Bank lookup, or any read-only public-data investigation."
---

# Public Data Research

Use official statistical APIs and public bulk downloads for read-only research into market conditions, regional indicators, household spending, prices, demographics, industries, international development indicators, monetary/financial data, agriculture/food data, and media/news signals. Prefer API-backed evidence over browser snippets, and keep the exact provider, endpoint, dataset ID, filters, time window, units, and sampling limits visible in the final answer.

Keep data sources independent. Use each provider's dedicated script and reference. Do not create a unified `public_data.py` layer.

All provider scripts must print fetched data or errors to standard output only. Do not write result files from these scripts; pipe stdout to another command when files, parsing, or post-processing are needed.

## Directory Layout

```text
public-data-research/
├── SKILL.md
├── scripts/
│   ├── bis_api.py        # BIS SDMX dataflows + bulk CSV ZIP stdout helper
│   ├── boj_api.py        # Bank of Japan Time-Series Data Search API helper
│   ├── estat_api.py       # Japan e-Stat API CLI + reusable client
│   ├── faostat_bulk.py   # FAOSTAT public bulk ZIP stdout helper
│   ├── gdelt_api.py      # GDELT DOC/request API helper
│   ├── imf_datamapper_api.py # IMF DataMapper API helper
│   ├── oecd_sdmx_api.py  # OECD SDMX API helper
│   └── world_bank_api.py # World Bank Indicators API helper
└── references/
    ├── bis.md
    ├── boj.md
    ├── estat.md          # e-Stat command patterns and guardrails
    ├── faostat.md
    ├── gdelt.md
    ├── imf_datamapper.md
    ├── oecd.md
    └── world_bank.md     # World Bank command patterns and guardrails
```

## Prerequisites

- **Python 3.10+** must be installed.
- e-Stat credentials are assumed to already be available from the OS environment or a nearby `.env` file.
- Do not print, inspect, edit, or commit secret values.

Supported environment variables:

```text
ESTAT_APP_ID
```

World Bank, IMF DataMapper, BOJ, OECD, BIS public endpoints/bulk downloads, FAOSTAT public bulk downloads, and GDELT do not require API keys for the supported commands. Future providers should add their own clearly named environment variables only if the provider requires credentials. Do not add fallback names unless the user explicitly asks for them.

## Quick Start

```bash
python3 skills/public-data-research/scripts/estat_api.py check-auth
python3 skills/public-data-research/scripts/estat_api.py search "家計調査" --limit 5
python3 skills/public-data-research/scripts/estat_api.py meta 0002070001 --find "外食"
python3 skills/public-data-research/scripts/estat_api.py data 0002070001 --filter cdCat01=098 --filter cdCat02=03 --filter cdArea=00000 --latest-time
python3 skills/public-data-research/scripts/world_bank_api.py check-auth
python3 skills/public-data-research/scripts/world_bank_api.py indicators "gdp per capita" --limit 10
python3 skills/public-data-research/scripts/world_bank_api.py data NY.GDP.PCAP.CD JPN KOR USA --date 2020:2024
python3 skills/public-data-research/scripts/imf_datamapper_api.py data NGDP_RPCH JPN USA WEOWORLD --periods 2023,2024,2025
python3 skills/public-data-research/scripts/boj_api.py data-code --db FM01 --code STRDCLUCON --start-date 202606 --limit 20
python3 skills/public-data-research/scripts/oecd_sdmx_api.py dataflows housing --limit 10
python3 skills/public-data-research/scripts/bis_api.py bulk-list "policy rates" --limit 10
python3 skills/public-data-research/scripts/faostat_bulk.py fetch production-crops-livestock --filter "Area=Japan" --limit 20
python3 skills/public-data-research/scripts/gdelt_api.py doc "supply chain" --timespan 7d --maxrecords 10
```

For details, examples, endpoint selection, and caveats, read the provider-specific reference:

- [references/estat.md](references/estat.md) for Japan e-Stat.
- [references/world_bank.md](references/world_bank.md) for World Bank Indicators.
- [references/imf_datamapper.md](references/imf_datamapper.md) for IMF DataMapper macro indicators.
- [references/boj.md](references/boj.md) for Bank of Japan time-series data.
- [references/oecd.md](references/oecd.md) for OECD SDMX.
- [references/bis.md](references/bis.md) for BIS SDMX dataflows and bulk downloads.
- [references/faostat.md](references/faostat.md) for FAOSTAT public bulk data.
- [references/gdelt.md](references/gdelt.md) for GDELT news/media signal data.

## Workflow

1. Translate the user request into a data task:
   - Find relevant Japanese statistics: use `estat_api.py search`.
   - Inspect an e-Stat dataset's dimensions and codes: use `estat_api.py meta`.
   - Fetch filtered e-Stat values: use `estat_api.py data`.
   - Find international indicators: use `world_bank_api.py indicators`.
   - Fetch country-level international time series: use `world_bank_api.py data`.
   - Fetch IMF macro series: use `imf_datamapper_api.py data`.
   - Fetch Japanese monetary/financial series: use `boj_api.py data-code`.
   - Find OECD SDMX dataflows: use `oecd_sdmx_api.py dataflows`.
   - Fetch OECD SDMX data: use `oecd_sdmx_api.py data` after inspecting structure.
   - Find BIS datasets: use `bis_api.py dataflows` or `bis_api.py bulk-list`.
   - Fetch BIS bulk CSV rows: use `bis_api.py bulk-fetch`.
   - Fetch FAOSTAT bulk CSV rows: use `faostat_bulk.py fetch`.
   - Search GDELT article/timeline signals: use `gdelt_api.py doc`.
   - Export or pipe rows for analysis: use provider `--csv`/`--json` options or raw stdout.
2. Start broad, then narrow:
   - Search by survey/statistics name or topic.
   - Read metadata before fetching values.
   - Select only the needed area, item/category, time, and unit.
3. Preserve the research parameters:
   - Provider and endpoint
   - Dataset/statistics table ID
   - Filter codes and labels
   - Time range or latest time code
   - Units and row counts
4. Report findings separately from caveats. Public statistics are structured but still require careful interpretation of units, definitions, revisions, geography, missing values, and survey scope.

## Script Selection

| Task | Script | Notes |
|---|---|---|
| e-Stat credential check | `estat_api.py check-auth` | Uses a minimal metadata request without printing `ESTAT_APP_ID`. |
| e-Stat statistics search | `estat_api.py search QUERY` | Wraps `getStatsList`. |
| e-Stat metadata/code lookup | `estat_api.py meta STATS_DATA_ID` | Wraps `getMetaInfo`; use `--find` to search class labels. |
| e-Stat data fetch | `estat_api.py data STATS_DATA_ID` | Wraps `getStatsData`; pass filters such as `cdCat01=098`. |
| Direct e-Stat endpoint | `estat_api.py request ENDPOINT` | Read-only escape hatch for supported e-Stat endpoints. |
| World Bank check | `world_bank_api.py check-auth` | No API key required. |
| World Bank countries | `world_bank_api.py countries QUERY` | List/filter economies, regions, and income levels. |
| World Bank indicator search | `world_bank_api.py indicators QUERY` | Defaults to WDI source `2`; local filter over fetched indicator catalog. |
| World Bank data fetch | `world_bank_api.py data INDICATOR COUNTRIES...` | Fetch country/economy time series; supports `--date`, `--mrv`, and `--mrnev`. |
| Direct World Bank endpoint | `world_bank_api.py request PATH` | Read-only escape hatch for World Bank v2 paths. |
| IMF check | `imf_datamapper_api.py check-auth` | No API key required. |
| IMF catalogs | `imf_datamapper_api.py indicators/countries/regions/groups QUERY` | Search available codes locally. |
| IMF data fetch | `imf_datamapper_api.py data INDICATOR ENTITIES...` | Fetch one indicator and locally filter entities/periods. |
| BOJ check | `boj_api.py check-auth` | No API key required. |
| BOJ time series | `boj_api.py data-code --db DB --code CODE` | Flattens series values into observation rows. |
| BOJ metadata/layers | `boj_api.py metadata` / `boj_api.py layer` | Prints JSON/CSV stdout. |
| OECD check | `oecd_sdmx_api.py check-auth` | No API key required. |
| OECD dataflows | `oecd_sdmx_api.py dataflows QUERY` | Find agency/dataflow/version. |
| OECD data fetch | `oecd_sdmx_api.py data AGENCY DATAFLOW FILTER` | Prints raw SDMX-CSV/XML stdout. |
| BIS check | `bis_api.py check-auth` | No API key required. |
| BIS dataflows | `bis_api.py dataflows QUERY` | Lists SDMX dataflows. |
| BIS bulk rows | `bis_api.py bulk-list QUERY` / `bis_api.py bulk-fetch SOURCE` | Expands ZIP in memory and prints CSV stdout. |
| FAOSTAT catalog/fetch | `faostat_bulk.py catalog` / `faostat_bulk.py fetch SOURCE` | Expands public bulk ZIP in memory and prints CSV stdout. |
| GDELT check | `gdelt_api.py check-auth` | No API key required; can rate-limit. |
| GDELT DOC search | `gdelt_api.py doc QUERY` | Article/timeline media signal data. |

## Output Standards

Provider scripts print to stdout only. They must not create result files. If a file is needed, redirect stdout outside the script, for example:

```bash
python3 skills/public-data-research/scripts/world_bank_api.py data SP.POP.TOTL JPN --mrv 5 --csv > /tmp/worldbank_population.csv
```

When answering the user, include:

- Provider, endpoint, and dataset/table ID.
- For World Bank, include indicator code, country/economy codes, source ID, date range, and `lastupdated` when returned.
- For IMF, include indicator code, entity codes, source, dataset, unit, and projection caveat when relevant.
- For BOJ, include database, series code, frequency, date range, unit, and last update.
- For OECD/BIS SDMX, include agency, dataflow, version, filter expression, and whether the output was raw SDMX-CSV/XML or parsed bulk CSV.
- For FAOSTAT, include bulk URL/catalog key, CSV filters, row limit, and the fact that data came from public bulk data.
- For GDELT, include query, mode, timespan/date range, `maxrecords`, and note that it is media-derived signal data rather than official statistics.
- The exact filters used, including code labels when available.
- Time period, geography, unit, and number of rows returned.
- A compact table of the most relevant rows.
- Caveats about survey scope, units, revisions, missing values, and whether the table is monthly, annual, national, regional, or category-specific.

Do not treat one table or provider as all available official data. Keep data sources independent: use the provider's dedicated script and read only the provider-specific reference needed for the task.
