# Bank of Japan Workflows

Use `scripts/boj_api.py` for no-key Bank of Japan Time-Series Data Search API research.

## Scope

- Coverage: Japan-centered monetary, financial, price, Tankan, balance of payments, flow of funds, exchange-rate, and related time-series statistics.
- Credential: none.
- Output: every command writes to stdout only.

## Commands

```bash
python3 skills/public-data-research/scripts/boj_api.py check-auth
python3 skills/public-data-research/scripts/boj_api.py data-code --db FM01 --code STRDCLUCON --start-date 202606 --limit 20
python3 skills/public-data-research/scripts/boj_api.py metadata --db FM08 --format csv
python3 skills/public-data-research/scripts/boj_api.py request getDataCode --param db=FM01 --param code=STRDCLUCON --param startDate=202606
```

## Notes

- Use metadata first when the BOJ database or series code is unknown.
- The `data-code` command flattens BOJ JSON series into observation rows with `seriesCode`, `surveyDate`, `value`, unit, frequency, and last update.
- Date formats vary by database/frequency. Use BOJ examples or metadata when uncertain.
- Avoid high-frequency access.

## Official Docs

- BOJ API manual: https://www.stat-search.boj.or.jp/info/api_manual.pdf
