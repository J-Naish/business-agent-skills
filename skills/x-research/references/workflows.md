# X Research Workflows

Use this reference when choosing an endpoint, composing a query, or reporting X API-backed research.

## Research Stance

- Prefer read-only endpoints.
- Start with counts, then fetch samples.
- Keep the original query and endpoint in the answer.
- Treat API results as a bounded sample unless the endpoint explicitly returns a complete resource.
- Do not expose `.env` values or request headers.
- Do not perform write actions from this skill without explicit user confirmation.

## Command Patterns

### Credential check

```bash
uv run skills/x-research/scripts/x_api.py check-auth
```

### Topic scan

```bash
uv run skills/x-research/scripts/trend_scan.py \
  "AI agents lang:ja -is:retweet" \
  --max-posts 100 \
  --granularity hour
```

### Topic volume only

```bash
uv run skills/x-research/scripts/x_api.py counts \
  "AI agents lang:ja -is:retweet" \
  --granularity hour
```

### Recent search

```bash
uv run skills/x-research/scripts/x_api.py search \
  "from:xdevelopers -is:retweet" \
  --max-results 10 \
  --max-pages 1
```

### Full-archive search

```bash
uv run skills/x-research/scripts/x_api.py search \
  "openai lang:en -is:retweet" \
  --all \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z
```

Use `--all` only when the account plan has full-archive access.

### Account scan

```bash
uv run skills/x-research/scripts/account_scan.py xdevelopers \
  --timeline-pages 1 \
  --mentions-pages 1
```

### Conversation scan

```bash
uv run skills/x-research/scripts/conversation_scan.py \
  https://x.com/xdevelopers/status/1460323737035677698 \
  --max-posts 50
```

### Generic read-only endpoint

```bash
uv run skills/x-research/scripts/x_api.py request GET /2/users/by/username/xdevelopers \
  --param user.fields=created_at,description,public_metrics,verified
```

## Endpoint Map

| Research need | Default command or endpoint |
|---|---|
| Recent posts by query | `x_api.py search QUERY` -> `GET /2/tweets/search/recent` |
| Full archive posts by query | `x_api.py search QUERY --all` -> `GET /2/tweets/search/all` |
| Recent post volume | `x_api.py counts QUERY` -> `GET /2/tweets/counts/recent` |
| Full archive volume | `x_api.py counts QUERY --all` -> `GET /2/tweets/counts/all` |
| User by username or ID | `x_api.py user VALUE` -> user lookup endpoints |
| Authenticated user | `x_api.py user --me --auth oauth1` or `--auth bearer` if supported |
| Account timeline | `x_api.py timeline USERNAME` -> `GET /2/users/:id/tweets` |
| Mentions of account | `x_api.py timeline USERNAME --mentions` -> `GET /2/users/:id/mentions` |
| Liked posts by user | `x_api.py timeline USERNAME --liked` -> `GET /2/users/:id/liked_tweets` |
| Followers/following | `x_api.py follow USERNAME --type followers|following` |
| Post lookup | `x_api.py post POST_ID_OR_URL` |
| Users who liked or reposted | `x_api.py post-engagement POST_ID --type liking-users|reposted-by` |
| Quote posts | `x_api.py post-engagement POST_ID --type quotes` |
| List posts | `x_api.py list-posts LIST_ID` |
| Spaces search | `x_api.py spaces QUERY` |
| Trends by WOEID | `x_api.py trends --woeid 1` |
| Personalized trends | `x_api.py trends --personalized --auth oauth1` |
| News search | `x_api.py news QUERY` |
| Usage | `x_api.py usage` |

## Query Guidance

X search syntax is powerful but easy to bias. Prefer explicit operators:

- Language: `lang:ja`, `lang:en`
- Exclude reposts: `-is:retweet`
- Exclude replies: `-is:reply`
- Account: `from:username`, `to:username`, `@username`
- Hashtag: `#topic`
- URL/domain: `url:"example.com"`
- Conversation: `conversation_id:POST_ID`
- Engagement filters where supported: `min_faves:10`, `min_retweets:5`, `min_replies:3`

When comparing topics, keep query windows, language filters, exclusions, and sampling sizes identical.

## Reporting Caveats

Always state the main constraints:

- Recent search windows and full-archive access depend on the X API plan.
- Counts and search results can differ because of deleted, protected, withheld, or inaccessible posts.
- Engagement metrics are snapshots at retrieval time.
- Trends can be location-specific, personalized, or access-tier dependent.
- A small sample can identify themes but should not be treated as a census.

## Official Docs

- X Developer Platform overview: https://docs.x.com/overview
- Make your first request: https://docs.x.com/make-your-first-request
- X API index: https://docs.x.com/x-api/llms.txt
- Search Posts docs: https://docs.x.com/x-api/posts/search/introduction.md
- Search operators: https://docs.x.com/x-api/posts/search/integrate/operators.md
- Post counts: https://docs.x.com/x-api/posts/counts/introduction.md
- Users lookup: https://docs.x.com/x-api/users/lookup/introduction.md
- Trends: https://docs.x.com/x-api/trends/trends-by-woeid/introduction.md
