# OECD SDMX Workflows

Use `scripts/oecd_sdmx_api.py` for no-key OECD Data API / SDMX research.

## Scope

- Coverage: OECD countries and selected non-member economies, depending on dataflow.
- Credential: none.
- Output: every command writes to stdout only.
- Strengths: cross-country policy, economy, environment, labor, wellbeing, education, and sector datasets.

## Commands

```bash
python3 skills/public-data-research/scripts/oecd_sdmx_api.py check-auth
python3 skills/public-data-research/scripts/oecd_sdmx_api.py dataflows housing --limit 10
python3 skills/public-data-research/scripts/oecd_sdmx_api.py structure OECD.ENV.EPI 'DSD_ECH@EXT_DROUGHT' --version 1.0
python3 skills/public-data-research/scripts/oecd_sdmx_api.py data OECD.ENV.EPI 'DSD_ECH@EXT_DROUGHT' 'AUS.A.ED_CROP_ANOM.....' --version 1.0 --start-period 2018 --end-period 2021
```

## Notes

- Start with `dataflows QUERY` to find agency/dataflow/version.
- Then fetch structure XML to inspect dimensions and allowed codes.
- The `data` command is a thin SDMX v1 wrapper and prints raw SDMX-CSV by default. This makes it easy to pipe into `head`, `csvcut`, `python`, or other tools.
- SDMX filters are dataflow-specific. Do not guess dimension order; inspect structure or use the OECD Data Explorer API builder.

## Official Docs

- OECD Data API documentation: https://gitlab.algobank.oecd.org/public-documentation/dotstat-migration/-/raw/main/OECD_Data_API_documentation.pdf
