# Google Keyword Research Workflows

Use this reference when choosing a command, composing Keyword Planner requests, or reporting Google Ads API-backed search-demand research.

## Research Stance

- Prefer read-only calls.
- Start with a small seed list, then expand only when useful.
- Keep seed terms, URL seed, endpoint, geo, language, network, customer ID, and limits in the answer.
- Treat search volume, CPC, and competition as approximate planning signals, not exact market totals.
- Do not expose `.env` values, OAuth tokens, developer tokens, client secrets, or request headers.
- Do not create campaigns, ad groups, keywords, assets, budgets, or conversions from this skill.

## Command Patterns

### Credential check

```bash
uv run skills/google-keyword-research/scripts/google_keyword_api.py check-auth
```

### Topic scan

```bash
uv run skills/google-keyword-research/scripts/keyword_scan.py \
  "AI agent" \
  --geo JP \
  --language ja \
  --network GOOGLE_SEARCH \
  --max-ideas 50 \
  --max-historical-keywords 25 \
  --include-average-cpc
```

### Generate keyword ideas

```bash
uv run skills/google-keyword-research/scripts/google_keyword_api.py ideas \
  "CRM" "営業管理" \
  --url https://example.com/ \
  --geo JP \
  --language ja \
  --network GOOGLE_SEARCH \
  --max-results 50
```

### Historical metrics for exact terms

```bash
uv run skills/google-keyword-research/scripts/google_keyword_api.py historical \
  "CRM" "営業管理" "SFA" \
  --geo JP \
  --language ja \
  --include-average-cpc
```

### Geo target lookup

```bash
uv run skills/google-keyword-research/scripts/google_keyword_api.py geo-targets Tokyo --max-results 20
uv run skills/google-keyword-research/scripts/google_keyword_api.py geo-targets JP --max-results 20
```

### Language lookup

```bash
uv run skills/google-keyword-research/scripts/google_keyword_api.py languages Japanese
uv run skills/google-keyword-research/scripts/google_keyword_api.py languages ja
```

### Read-only GAQL lookup

```bash
uv run skills/google-keyword-research/scripts/google_keyword_api.py gaql \
  "SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone FROM customer LIMIT 1"
```

## Endpoint Map

| Research need | Default command or API method |
|---|---|
| Search demand summary for a theme | `keyword_scan.py TOPIC` |
| Related keyword discovery | `google_keyword_api.py ideas` -> `KeywordPlanIdeaService.GenerateKeywordIdeas` |
| Exact volume, CPC, competition, monthly trend | `google_keyword_api.py historical` -> `KeywordPlanIdeaService.GenerateKeywordHistoricalMetrics` |
| Country, region, or city targeting constants | `google_keyword_api.py geo-targets` -> GAQL on `geo_target_constant` |
| Language constants | `google_keyword_api.py languages` -> GAQL on `language_constant` |
| Customer/account metadata | `google_keyword_api.py gaql` -> `GoogleAdsService.Search` |

## Parameter Guidance

Default assumptions:

- `--geo JP`
- `--language ja`
- `--network GOOGLE_SEARCH`

Override these defaults for non-Japan or multilingual research. Use the same geo, language, network, and keyword list when comparing terms.

Useful geo shortcuts built into the scripts:

| Code | Geo target ID |
|---|---:|
| JP | 2392 |
| US | 2840 |
| GB | 2826 |
| CA | 2124 |
| AU | 2036 |
| DE | 2276 |
| FR | 2250 |
| IN | 2356 |
| KR | 2410 |
| TW | 2158 |
| SG | 2702 |

Useful language shortcuts built into the scripts:

| Code | Language ID |
|---|---:|
| ja | 1011 |
| en | 1000 |
| de | 1001 |
| fr | 1002 |
| es | 1003 |
| ko | 1012 |
| zh | 1017 |
| id | 1025 |
| vi | 1040 |
| th | 1044 |

When a geo or language is not in the shortcut table, pass a numeric ID or resource name directly, or use `geo-targets` / `languages` to look it up.

## Interpretation Guidance

Use `historical` for apples-to-apples comparisons between exact terms. Use `ideas` for discovery, then re-check promising ideas with `historical`.

For each keyword, inspect:

- `avg_monthly_searches`: approximate average volume.
- `monthly_search_volumes`: recent monthly pattern; compare same months for seasonal topics.
- `competition`: advertiser competition bucket.
- `competition_index`: 0-100 advertiser competition signal when available.
- `low_top_of_page_bid` / `high_top_of_page_bid`: bid range in the account currency.
- `average_cpc`: average CPC only when `--include-average-cpc` is requested and available.
- `close_variants`: returned by historical metrics; volume may include variants.

## Reporting Caveats

Always state the main constraints:

- Keyword Planner volumes are approximate planning metrics, not exact search counts.
- Historical metrics can include close variants.
- Results depend on geo target, language, search network, customer account, and API access.
- Low-volume terms may be rounded, bucketed, omitted, or shown as zero.
- CPC and bid ranges are advertising-market signals, not SEO difficulty.
- URL-seeded ideas depend on Google's crawl and interpretation of the page.
- Search partner inclusion changes the demand surface; document `GOOGLE_SEARCH` vs `GOOGLE_SEARCH_AND_PARTNERS`.

## Official Docs

- Keyword ideas: https://developers.google.com/google-ads/api/docs/keyword-planning/generate-keyword-ideas
- Historical metrics: https://developers.google.com/google-ads/api/docs/keyword-planning/generate-historical-metrics
- Python client authentication: https://developers.google.com/google-ads/api/docs/client-libs/python/authentication
- Python client configuration: https://developers.google.com/google-ads/api/docs/client-libs/python/configuration
- Geo target constants: https://developers.google.com/google-ads/api/reference/data/geotargets
- Language constants: https://developers.google.com/google-ads/api/reference/data/codes-formats#languages
