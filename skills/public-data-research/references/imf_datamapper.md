# IMF DataMapper Workflows

Use `scripts/imf_datamapper_api.py` for no-key IMF macro indicators from DataMapper.

## Scope

- Coverage: countries, regions, and IMF analytical groups.
- Credential: none.
- Output: every command writes to stdout only.
- Strengths: WEO-style GDP, inflation, current account, debt, unemployment, population, and related macro indicators.

## Commands

```bash
python3 skills/public-data-research/scripts/imf_datamapper_api.py check-auth
python3 skills/public-data-research/scripts/imf_datamapper_api.py indicators inflation --limit 10
python3 skills/public-data-research/scripts/imf_datamapper_api.py countries Japan
python3 skills/public-data-research/scripts/imf_datamapper_api.py data NGDP_RPCH JPN USA WEOWORLD --periods 2023,2024,2025
python3 skills/public-data-research/scripts/imf_datamapper_api.py data PCPIPCH JPN USA --periods 2024,2025 --csv
```

## Notes

- The script fetches the indicator series and applies country/period filters locally because DataMapper endpoint-side filtering can be inconsistent.
- The IMF site can block Python's standard HTTP client; the script falls back to local `curl` automatically when `urllib` receives 403.
- Always report the indicator code, entity codes, periods, source, dataset, unit, and last-modified date when available.
- IMF projections can be included in recent/future years. Check the indicator metadata's projection year and explain that values may be forecasts.

## Official Docs

- IMF DataMapper API: https://www.imf.org/external/datamapper/api/help
