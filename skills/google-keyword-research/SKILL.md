---
name: google-keyword-research
description: "Research search demand using Google Ads Keyword Planner and the Google Ads API: generate keyword ideas, inspect historical search volume, monthly trends, competition, top-of-page bid ranges, CPC signals, geo/language targeting constants, and GAQL-backed Google Ads account lookup data. Use when the user asks for Keyword Planner research, keyword research, SEO/SEM demand research, search volume, related keyword discovery, CPC or competition estimates, market demand by region/language, or API-backed Google Ads keyword planning investigation."
---

# Google Keyword Research

Use the Google Ads API Keyword Planner services for read-only research into search demand, keyword ideas, historical metrics, monthly volume patterns, CPC ranges, competition, and geo/language targeting constants. Prefer API-backed evidence over browser scraping, and keep the exact seed keywords, URL, geo, language, network, customer ID, and sampling limits visible in the final answer.

## Directory Layout

```text
google-keyword-research/
├── SKILL.md
├── scripts/
│   ├── google_keyword_api.py  # Generic Keyword Planner + GAQL CLI
│   └── keyword_scan.py        # Topic scan combining ideas and historical metrics
└── references/
    └── workflows.md           # Command patterns, endpoint map, and caveats
```

## Prerequisites

- **Python 3.10+** must be installed.
- Google Ads API credentials are assumed to already be available from the OS environment or a nearby `.env` file.
- Do not print, inspect, edit, or commit secret values.

Supported environment variables:

```text
GOOGLE_ADS_DEVELOPER_TOKEN
GOOGLE_ADS_CLIENT_ID
GOOGLE_ADS_CLIENT_SECRET
GOOGLE_ADS_REFRESH_TOKEN
GOOGLE_ADS_CUSTOMER_ID
GOOGLE_ADS_LOGIN_CUSTOMER_ID
```

The scripts intentionally use these Google Ads variable names only. `GOOGLE_ADS_CUSTOMER_ID` is the customer being researched; `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is used when access flows through a manager account.

### How to run the scripts

The scripts are written as PEP 723 inline scripts. Their dependencies (`google-ads`, `python-dotenv`) are declared at the top of each file. Any of the following invocation styles works:

```bash
# Option A: uv (recommended)
uv run <skill-dir>/scripts/google_keyword_api.py check-auth

# Option B: pipx
pipx run <skill-dir>/scripts/google_keyword_api.py check-auth

# Option C: pip + plain python
pip install google-ads python-dotenv
python3 <skill-dir>/scripts/google_keyword_api.py check-auth
```

The command examples below use `uv run`, but plain `python3` runs the same scripts when dependencies are already available.

## Quick Start

```bash
uv run skills/google-keyword-research/scripts/google_keyword_api.py check-auth

uv run skills/google-keyword-research/scripts/keyword_scan.py \
  "AI agent" \
  --geo JP \
  --language ja \
  --max-ideas 50 \
  --max-historical-keywords 25

uv run skills/google-keyword-research/scripts/google_keyword_api.py ideas \
  "生成AI" "AIエージェント" \
  --geo JP \
  --language ja \
  --max-results 50

uv run skills/google-keyword-research/scripts/google_keyword_api.py historical \
  "生成AI" "AIエージェント" \
  --geo JP \
  --language ja \
  --include-average-cpc
```

For details, endpoint selection, query constants, and caveats, read [references/workflows.md](references/workflows.md).

## Workflow

1. Translate the request into a research unit:
   - Broad topic, market, or product category: use `keyword_scan.py`.
   - Related keyword discovery: use `google_keyword_api.py ideas`.
   - Exact terms, volume, CPC, competition, and monthly trends: use `google_keyword_api.py historical`.
   - Geo or language constants: use `google_keyword_api.py geo-targets` or `languages`.
   - Other read-only Google Ads lookup data: use `google_keyword_api.py gaql`.
2. Make the narrowest useful request first. Start with a small topic scan or exact keyword list before expanding to many ideas.
3. Preserve the research parameters:
   - Seed keywords and optional URL seed
   - Endpoint names
   - Customer ID, geo target IDs, language ID, and search network
   - Result count and keyword sample size
   - Whether CPC was requested
4. Analyze returned data:
   - Average monthly searches
   - Monthly search volume series
   - Competition level and competition index
   - Top-of-page bid low/high ranges and average CPC when available
   - Close variants returned by historical metrics
   - Related keyword clusters from generated ideas
5. Report caveats clearly. Keyword Planner metrics are approximate, often grouped with close variants, affected by account/API access, and not a complete census of all search behavior.

## Script Selection

| Task | Script | Notes |
|---|---|---|
| Check credentials | `google_keyword_api.py check-auth` | Tests OAuth refresh-token auth and customer access without printing secrets. |
| Topic demand scan | `keyword_scan.py TOPIC` | Generates ideas, fetches historical metrics for seed+top ideas, and prints a summary JSON. |
| Related keyword ideas | `google_keyword_api.py ideas` | Wraps `GenerateKeywordIdeas`; accepts keyword seed, URL seed, or both. |
| Exact historical metrics | `google_keyword_api.py historical` | Wraps `GenerateKeywordHistoricalMetrics`; use for exact term comparisons. |
| Geo target lookup | `google_keyword_api.py geo-targets QUERY` | Finds targetable country, region, city, DMA, or other geo constants. |
| Language lookup | `google_keyword_api.py languages QUERY` | Finds targetable language constants. |
| Read-only GAQL lookup | `google_keyword_api.py gaql QUERY` | Escape hatch for account/customer metadata and constants. |

## Output Standards

When answering the user, include:

- The exact seed keywords or URL seed.
- The endpoint used: keyword ideas, historical metrics, geo targets, language constants, or GAQL.
- The geo target IDs, language ID, network, customer ID, and sample size.
- Findings separated from caveats.
- Whether volume, CPC, and competition are exact-keyword metrics or generated idea metrics.

Do not claim Keyword Planner output represents exact total Google search demand. Treat it as approximate planning data shaped by the requested region, language, network, close-variant grouping, and account/API access.
