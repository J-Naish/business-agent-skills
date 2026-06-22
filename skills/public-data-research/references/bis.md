# BIS Workflows

Use `scripts/bis_api.py` for no-key BIS statistics research.

## Scope

- Coverage: international banking, credit, debt securities, derivatives, property prices, exchange rates, policy rates, CPI, central bank assets, and payment statistics.
- Credential: none.
- Output: every command writes to stdout only.

## Commands

```bash
python3 skills/public-data-research/scripts/bis_api.py check-auth
python3 skills/public-data-research/scripts/bis_api.py dataflows property --limit 10
python3 skills/public-data-research/scripts/bis_api.py bulk-list "policy rates" --limit 10
python3 skills/public-data-research/scripts/bis_api.py bulk-fetch "policy rates" --limit 50
python3 skills/public-data-research/scripts/bis_api.py bulk-fetch "property prices" --filter REF_AREA=JP --limit 50
```

## Notes

- `dataflows` lists SDMX dataflows from `stats.bis.org`.
- `bulk-list` and `bulk-fetch` use BIS Data Portal ZIP downloads. ZIPs are held in memory and printed to stdout; no files are created.
- Prefer `(CSV, flat)` downloads for AI parsing and shell pipelines.
- Bulk datasets can be large. Use `--limit` and `--filter COLUMN=VALUE` before piping into downstream tools.

## Official Docs

- BIS statistics access page: https://www.bis.org/statistics/index.htm
- BIS bulk downloads: https://data.bis.org/bulkdownload
