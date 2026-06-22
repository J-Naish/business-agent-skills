# GDELT Workflows

Use `scripts/gdelt_api.py` for no-key GDELT news/media signal research.

## Scope

- Coverage: global online news and media signals, not official government statistics.
- Credential: none.
- Output: every command writes to stdout only.
- Strengths: trend scanning, geopolitical/media risk, article discovery, timeline volume, and event/context research.

## Commands

```bash
python3 skills/public-data-research/scripts/gdelt_api.py check-auth
python3 skills/public-data-research/scripts/gdelt_api.py doc "supply chain" --timespan 7d --maxrecords 10
python3 skills/public-data-research/scripts/gdelt_api.py doc "Japan tourism" --mode timelinevol --timespan 1m --json
python3 skills/public-data-research/scripts/gdelt_api.py request /doc/doc --param query=semiconductor --param mode=artlist --param format=json --param maxrecords=5
```

## Notes

- GDELT can return rate-limit responses during repeated probing. Keep `maxrecords` small and retry later when needed.
- Treat GDELT as media-derived signal data, not as official statistics.
- For article lists, report query, mode, timespan/date range, max records, and visible domains/countries/languages.

## Official Docs

- GDELT data and APIs: https://www.gdeltproject.org/data.html
