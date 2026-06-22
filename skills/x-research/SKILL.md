---
name: x-research
description: "Research X using the X API: investigate posts, search queries, topic volume, trends, news, users, accounts, competitors, conversations, Lists, Spaces, followers, mentions, engagement, and API-backed public discourse signals. Use when the user asks for X/Twitter research, trend discovery, social listening, account analysis, conversation analysis, audience or community research, post lookup, hashtag or keyword research, or any read-only X API investigation."
---

# X Research

Use the X API for read-only research into topics, posts, users, conversations, trends, news, Lists, Spaces, and public activity patterns. Prefer API-backed evidence over browser scraping, and keep the exact query, endpoint, time window, and sampling limits visible in the final answer.

## Directory Layout

```text
x-research/
├── SKILL.md
├── scripts/
│   ├── x_api.py              # Generic X API CLI + reusable client
│   ├── trend_scan.py         # Topic/query volume and post sample analysis
│   ├── account_scan.py       # Account profile, timeline, and mentions analysis
│   └── conversation_scan.py  # Post/conversation and reply/quote analysis
└── references/
    └── workflows.md          # Endpoint map, command patterns, and research guardrails
```

## Prerequisites

- **Python 3.10+** must be installed.
- X API credentials must be available to the scripts. They never print token values.

Supported environment variables:

```text
X_API_BEARER_TOKEN
X_API_CONSUMER_KEY
X_API_CONSUMER_KEY_SECRET
X_API_ACCESS_TOKEN
X_API_ACCESS_TOKEN_SECRET
```

Use Bearer auth for most public read endpoints. Use OAuth 1.0a only when an endpoint requires user context or owned reads. Never use this skill for write actions such as posting, liking, following, deleting, muting, blocking, or changing account state unless the user explicitly asks and confirms the side effect.

### How to run the scripts

The scripts are written as [PEP 723](https://peps.python.org/pep-0723/) inline scripts. Their dependency (`python-dotenv`) is declared at the top of each file. Any of the following invocation styles works:

```bash
# Option A: uv (recommended — fastest, auto-resolves dependencies)
uv run <skill-dir>/scripts/x_api.py check-auth

# Option B: pipx (when uv isn't available)
pipx run <skill-dir>/scripts/x_api.py check-auth

# Option C: pip + plain python (most universal — install dependencies once)
pip install python-dotenv
python3 <skill-dir>/scripts/x_api.py check-auth
```

The command examples below use the shortest form, `uv run`, but Options B and C run the same scripts identically.

### Passing X API credentials

Each script looks up credentials in this order and uses the first match:

1. **`os.environ`** — Variables set by `export`, by an external loader (direnv, 1Password, etc.), or prefixed inline on the command.
2. **`.env` file** — Walks up from the current working directory and loads the first `.env` it finds.

Pick whichever fits your setup:

```bash
# Option 1: drop a .env in the project root (easiest)
echo 'X_API_BEARER_TOKEN=your-token-here' >> .env
echo 'X_API_CONSUMER_KEY=your-key-here' >> .env
echo 'X_API_CONSUMER_KEY_SECRET=your-secret-here' >> .env
echo 'X_API_ACCESS_TOKEN=your-access-token-here' >> .env
echo 'X_API_ACCESS_TOKEN_SECRET=your-access-token-secret-here' >> .env
# Add .env to .gitignore so it doesn't get committed.

# Option 2: export in your shell
export X_API_BEARER_TOKEN=your-token-here
export X_API_CONSUMER_KEY=your-key-here
export X_API_CONSUMER_KEY_SECRET=your-secret-here
export X_API_ACCESS_TOKEN=your-access-token-here
export X_API_ACCESS_TOKEN_SECRET=your-access-token-secret-here

# Option 3: prefix inline on the command
X_API_BEARER_TOKEN=your-token-here uv run ...
```

## Quick Start

```bash
uv run skills/x-research/scripts/x_api.py check-auth
uv run skills/x-research/scripts/trend_scan.py "AI agents lang:ja -is:retweet" --max-posts 50
uv run skills/x-research/scripts/account_scan.py xdevelopers --timeline-pages 1 --mentions-pages 1
uv run skills/x-research/scripts/conversation_scan.py 1460323737035677698 --max-posts 50
```

For details, examples, endpoint selection, and caveats, read [references/workflows.md](references/workflows.md).

## Workflow

1. Translate the user request into a research unit:
   - Topic or trend: use `trend_scan.py`.
   - Account, competitor, creator, or brand: use `account_scan.py`.
   - Specific post, thread, replies, or quote activity: use `conversation_scan.py`.
   - Anything else supported by X API GET endpoints: use `x_api.py request`.
2. Make the narrowest useful API request first. Start with counts or small samples before fetching large result sets.
3. Preserve the research parameters:
   - Query string and search operators
   - Endpoint names
   - Time window
   - Result count and page count
   - Auth mode
4. Analyze returned data:
   - Volume over time
   - Representative posts
   - Recurring hashtags, mentions, links, languages, and context annotations
   - Top authors by sample frequency and engagement metrics
   - Account posture, recent themes, mentions, and audience signals
5. Report caveats clearly. X API access level, rate limits, search-window limits, deleted/protected posts, personalization, and query design can materially affect findings.

## Script Selection

| Task | Script | Notes |
|---|---|---|
| Check credentials | `x_api.py check-auth` | Tests Bearer and OAuth 1.0a without printing secrets. |
| Search recent or full-archive posts | `x_api.py search` | Use `--all` only when the API plan allows full archive. |
| Count topic volume | `x_api.py counts` | Useful before collecting posts. |
| Topic trend summary | `trend_scan.py` | Combines counts, samples, hashtags, domains, mentions, and authors. |
| Account/competitor analysis | `account_scan.py` | Looks up profile, recent posts, and mention sample. |
| Conversation analysis | `conversation_scan.py` | Looks up a post and searches replies via `conversation_id`. |
| Lookup posts/users | `x_api.py post`, `x_api.py user` | Supports URLs and IDs for posts. |
| Lists, followers, following, Spaces, news, trends | `x_api.py` subcommands | Use purpose-built subcommands first. |
| Newly added or uncommon GET endpoint | `x_api.py request` | Generic escape hatch for read-only X API endpoints. |

## Output Standards

When answering the user, include:

- The exact X query or endpoint used.
- The date/time window and whether the data is recent search, full archive, timeline, mentions, trends, news, or another source.
- The number of posts/users/items sampled.
- Findings separated from caveats.
- Links to representative posts when usernames are available.

Do not claim that sampled API results represent all of X unless the endpoint and access tier support that claim.
