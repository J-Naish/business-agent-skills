# YouTube Research Workflows

Use this reference when choosing an endpoint, composing a query, or reporting YouTube Data API-backed research.

## Research Stance

- Prefer read-only endpoints.
- Start with a small search or lookup, then fetch details, comments, or more pages only when useful.
- Keep the original query, endpoint, filters, and sampling limits in the answer.
- Treat API results as a bounded sample. YouTube search ranking is not a census.
- Do not expose `.env` values, API keys, request URLs containing keys, or request headers.
- Do not perform write actions from this skill without explicit user confirmation.

## Command Patterns

### Credential check

```bash
uv run skills/youtube-research/scripts/youtube_api.py check-auth --region JP
```

### Topic scan

```bash
uv run skills/youtube-research/scripts/trend_scan.py \
  "AI agents" \
  --region-code JP \
  --relevance-language ja \
  --published-after 2026-06-01T00:00:00Z \
  --max-videos 50
```

### Raw video search

```bash
uv run skills/youtube-research/scripts/youtube_api.py search \
  "ChatGPT" \
  --type video \
  --order viewCount \
  --region-code JP \
  --relevance-language ja \
  --max-results 10 \
  --max-pages 1
```

### Channel scan

```bash
uv run skills/youtube-research/scripts/channel_scan.py "@YouTubeCreators" \
  --max-videos 20
```

### Video and comments scan

```bash
uv run skills/youtube-research/scripts/video_scan.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-comments 50 \
  --comment-order relevance
```

### Popular videos

```bash
uv run skills/youtube-research/scripts/youtube_api.py popular \
  --region-code JP \
  --max-results 10
```

### Generic read-only endpoint

```bash
uv run skills/youtube-research/scripts/youtube_api.py request GET /channels \
  --param part=snippet,statistics \
  --param forHandle=@YouTubeCreators
```

## Endpoint Map

| Research need | Default command or endpoint |
|---|---|
| Search videos/channels/playlists | `youtube_api.py search QUERY` -> `GET /youtube/v3/search` |
| Video details and metrics | `youtube_api.py videos VIDEO_ID_OR_URL` -> `GET /youtube/v3/videos` |
| Channel profile and metrics | `youtube_api.py channels VALUE` -> `GET /youtube/v3/channels` |
| Recent channel uploads | `channel_scan.py VALUE` -> `channels.list` uploads playlist + `playlistItems.list` + `videos.list` |
| Popular videos by region/category | `youtube_api.py popular` -> `GET /youtube/v3/videos?chart=mostPopular` |
| Comment threads for a video | `youtube_api.py comment-threads VIDEO_ID_OR_URL` -> `GET /youtube/v3/commentThreads` |
| Replies to a comment | `youtube_api.py comments PARENT_COMMENT_ID` -> `GET /youtube/v3/comments` |
| Playlist items | `youtube_api.py playlist-items PLAYLIST_ID` -> `GET /youtube/v3/playlistItems` |
| Video categories | `youtube_api.py video-categories` -> `GET /youtube/v3/videoCategories` |
| Newly added or uncommon GET endpoint | `youtube_api.py request GET PATH` | Generic read-only escape hatch. |

## Query Guidance

Keep comparisons controlled:

- Use the same `publishedAfter` / `publishedBefore` window.
- Use the same `regionCode`, `relevanceLanguage`, `safeSearch`, `order`, `videoDuration`, and sample sizes.
- Prefer `order=date` for freshness and `order=viewCount` for high-reach samples.
- Use `type=video` for topic scans unless the user asks for channels or playlists.
- Use `channelId` to restrict search to one channel when comparing uploads around a topic.
- Use `videoCategoryId` for category-specific research, and document the region used for category names.

Search and result filters commonly useful for research:

- `q`: search text
- `type`: `video`, `channel`, or `playlist`
- `order`: `date`, `rating`, `relevance`, `title`, `videoCount`, `viewCount`
- `publishedAfter`, `publishedBefore`: RFC 3339 timestamps
- `regionCode`: ISO 3166-1 alpha-2 country code
- `relevanceLanguage`: ISO language code
- `videoDuration`: `short`, `medium`, or `long`
- `videoDefinition`: `high` or `standard`
- `videoCategoryId`: category filter
- `eventType`: `live`, `upcoming`, or `completed`

## Reporting Caveats

Always state the main constraints:

- `search.list` is ranked and sampled; it is not a complete census of YouTube.
- `pageInfo.totalResults` is an estimate and can change between calls.
- Search results can omit private, deleted, age-restricted, region-blocked, or otherwise unavailable videos.
- Public metrics are snapshots at retrieval time and may omit hidden or unavailable fields.
- Comment sampling depends on comments being enabled and accessible.
- API quota cost differs by endpoint; search requests are comparatively expensive.
- Channel subscriber counts may be hidden.

## Official Docs

- YouTube Data API overview: https://developers.google.com/youtube/v3
- Search: list: https://developers.google.com/youtube/v3/docs/search/list
- Videos: list: https://developers.google.com/youtube/v3/docs/videos/list
- Channels: list: https://developers.google.com/youtube/v3/docs/channels/list
- CommentThreads: list: https://developers.google.com/youtube/v3/docs/commentThreads/list
- Comments: list: https://developers.google.com/youtube/v3/docs/comments/list
- PlaylistItems: list: https://developers.google.com/youtube/v3/docs/playlistItems/list
- VideoCategories: list: https://developers.google.com/youtube/v3/docs/videoCategories/list
- Quota costs: https://developers.google.com/youtube/v3/determine_quota_cost
