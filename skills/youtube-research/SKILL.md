---
name: youtube-research
description: "Research YouTube using the YouTube Data API: investigate videos, search queries, channels, creators, competitors, comments, playlists, popular videos, public performance metrics, publishing patterns, topic samples, and API-backed video platform signals. Use when the user asks for YouTube research, creator or channel analysis, video lookup, comment analysis, topic discovery, competitor research, public video performance analysis, or any read-only YouTube Data API investigation."
---

# YouTube Research

Use the YouTube Data API for read-only research into videos, channels, creators, comments, playlists, topic search results, and public performance patterns. Prefer API-backed evidence over browser scraping, and keep the exact query, endpoint, filters, time window, and sampling limits visible in the final answer.

## Directory Layout

```text
youtube-research/
├── SKILL.md
├── scripts/
│   ├── youtube_api.py      # Generic YouTube Data API CLI + reusable client
│   ├── trend_scan.py       # Topic/query video sample analysis
│   ├── channel_scan.py     # Channel profile and recent upload analysis
│   └── video_scan.py       # Video detail and comment-thread analysis
└── references/
    └── workflows.md        # Endpoint map, command patterns, and guardrails
```

## Prerequisites

- **Python 3.10+** must be installed.
- YouTube Data API credentials are assumed to already be available from the OS environment or a nearby `.env` file.
- Do not print, inspect, edit, or commit secret values.

Supported environment variable:

```text
YOUTUBE_API_KEY
```

Use API-key authentication for public read endpoints. This skill is intentionally read-only; do not use it for uploads, mutations, rating, moderation, or account-specific reads unless the user explicitly asks and confirms the side effect or OAuth requirement.

### How to run the scripts

The scripts are written as PEP 723 inline scripts. Their dependency (`python-dotenv`) is declared at the top of each file. Any of the following invocation styles works:

```bash
# Option A: uv (recommended)
uv run <skill-dir>/scripts/youtube_api.py check-auth

# Option B: pipx
pipx run <skill-dir>/scripts/youtube_api.py check-auth

# Option C: pip + plain python
pip install python-dotenv
python3 <skill-dir>/scripts/youtube_api.py check-auth
```

The command examples below use `uv run`, but plain `python3` runs the same scripts when dependencies are already available.

## Quick Start

```bash
uv run skills/youtube-research/scripts/youtube_api.py check-auth --region JP
uv run skills/youtube-research/scripts/trend_scan.py "AI agents" --region-code JP --relevance-language ja --max-videos 25
uv run skills/youtube-research/scripts/channel_scan.py "@YouTubeCreators" --max-videos 20
uv run skills/youtube-research/scripts/video_scan.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --max-comments 50
```

For details, examples, endpoint selection, and caveats, read [references/workflows.md](references/workflows.md).

## Workflow

1. Translate the user request into a research unit:
   - Topic, keyword, category, or trend sample: use `trend_scan.py`.
   - Channel, creator, competitor, or brand: use `channel_scan.py`.
   - Specific video, comments, or public engagement: use `video_scan.py`.
   - Anything else supported by YouTube Data API GET endpoints: use `youtube_api.py request`.
2. Make the narrowest useful API request first. Start with a small search, channel lookup, or video lookup before fetching comments or multiple pages.
3. Preserve the research parameters:
   - Search query and filters
   - Endpoint names
   - Published time window
   - Region, language, category, order, result count, and page count
   - API key authentication mode
4. Analyze returned data:
   - Search result estimate and sampled videos
   - View, like, and comment metrics when returned
   - Publishing dates, duration buckets, channels, tags, hashtags, and categories
   - Channel posture, recent uploads, and public subscriber/video/view counts
   - Comment themes, top comments by like count, and commenter frequency
5. Report caveats clearly. YouTube API quota, search ranking, missing private/deleted data, disabled comments, hidden subscriber counts, unavailable like counts, and query design can materially affect findings.

## Script Selection

| Task | Script | Notes |
|---|---|---|
| Check credentials | `youtube_api.py check-auth` | Uses a minimal public `videos.list` request without printing secrets. |
| Search videos | `youtube_api.py search` | Direct `search.list` wrapper; useful for raw pages or JSONL. |
| Lookup videos | `youtube_api.py videos` | Accepts video IDs and common YouTube URLs. |
| Lookup channels | `youtube_api.py channels` | Supports channel IDs, handles, and legacy usernames. |
| Popular videos | `youtube_api.py popular` | `videos.list chart=mostPopular` by region/category. |
| Topic trend summary | `trend_scan.py` | Combines search results, video details, channel details, categories, and sample analysis. |
| Channel/competitor analysis | `channel_scan.py` | Resolves a channel, then analyzes recent uploads. |
| Video/comment analysis | `video_scan.py` | Looks up a video and samples comment threads. |
| Comments only | `youtube_api.py comment-threads` | Fetches comment threads for a video. |
| Playlists/uploads | `youtube_api.py playlist-items` | Fetches playlist items, including upload playlists. |
| Uncommon GET endpoint | `youtube_api.py request` | Generic escape hatch for read-only Data API endpoints. |

## Output Standards

When answering the user, include:

- The exact YouTube query or endpoint used.
- The date/time window and whether data came from search results, video lookup, channel lookup, popular chart, playlist items, or comments.
- The region, language, order, category, page count, and number of videos/comments/channels sampled.
- Findings separated from caveats.
- Links to representative videos and channels when IDs are available.

Do not claim that sampled API results represent all of YouTube. `search.list` ranking and `pageInfo.totalResults` are API estimates and depend on query, filters, quota, access, and ranking behavior.
