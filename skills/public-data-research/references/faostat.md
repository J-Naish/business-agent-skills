# FAOSTAT Workflows

Use `scripts/faostat_bulk.py` for no-key FAOSTAT public bulk data.

## Scope

- Coverage: world countries/areas and FAO regional groupings. The bundled verified catalog currently includes production crops and livestock.
- Credential: none for public bulk ZIPs.
- Output: every command writes to stdout only.

## Commands

```bash
python3 skills/public-data-research/scripts/faostat_bulk.py check-auth
python3 skills/public-data-research/scripts/faostat_bulk.py catalog
python3 skills/public-data-research/scripts/faostat_bulk.py fetch production-crops-livestock --limit 50
python3 skills/public-data-research/scripts/faostat_bulk.py fetch production-crops-livestock --filter "Area=Japan" --limit 50
python3 skills/public-data-research/scripts/faostat_bulk.py fetch 'https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip' --limit 10
```

## Notes

- The older FAOSTAT API/FENIX endpoints can be unstable or unavailable. This helper uses public bulk ZIPs and expands them in memory.
- Add a full FAOSTAT bulk ZIP URL when the needed domain is not in the local catalog.
- Use exact CSV column names for `--filter`. Run a small `--limit` fetch first to inspect headers.

## Official Docs

- FAOSTAT: https://www.fao.org/faostat/en/
