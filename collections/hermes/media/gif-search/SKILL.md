---
name: gif-search
description: "Search/download GIFs from GIPHY via curl + jq."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [GIPHY_API_KEY]
  commands: [curl, jq]
metadata:
  hermes:
    tags: [GIF, Media, Search, GIPHY, API]
---

# GIF Search (GIPHY API)

Search and download GIFs directly via the GIPHY API using curl. No extra tools needed.

> The Tenor API that earlier versions of this skill used was shut down by Google on
> 2026-06-30; calls to `tenor.googleapis.com` now fail. Use GIPHY as below.

## When to use

Useful for finding reaction GIFs, creating visual content, and sending GIFs in chat.

## Setup

Set your GIPHY API key in your environment (add to `${HERMES_HOME:-~/.hermes}/.env`):

```bash
GIPHY_API_KEY=your_key_here
```

Create an app at https://developers.giphy.com/dashboard/ to get a key. New keys start as
rate-limited "beta" keys (max `limit` of 50); check the dashboard for the current quota.
GIPHY's terms ask apps to show "Powered by GIPHY" attribution where results are displayed.

If `GIPHY_API_KEY` is unset, tell the user a key is needed and stop; do not fall back to
scraping websites.

## Prerequisites

- `curl` and `jq` (both standard on macOS/Linux)
- `GIPHY_API_KEY` environment variable

## Search for GIFs

```bash
# Search and get GIF URLs (rating=g keeps results safe for work)
curl -sG "https://api.giphy.com/v1/gifs/search" \
  --data-urlencode "q=thumbs up" -d limit=5 -d rating=g -d "api_key=${GIPHY_API_KEY}" \
  | jq -r '.data[].images.original.url'

# Get smaller versions (200px tall)
curl -sG "https://api.giphy.com/v1/gifs/search" \
  --data-urlencode "q=nice work" -d limit=3 -d rating=g -d "api_key=${GIPHY_API_KEY}" \
  | jq -r '.data[].images.fixed_height.url'
```

`curl -G --data-urlencode` handles URL encoding of the query for you.

## Download a GIF

```bash
# Search and download the top result
URL=$(curl -sG "https://api.giphy.com/v1/gifs/search" \
  --data-urlencode "q=celebration" -d limit=1 -d rating=g -d "api_key=${GIPHY_API_KEY}" \
  | jq -r '.data[0].images.original.url')
[ -n "$URL" ] && [ "$URL" != "null" ] && curl -sL "$URL" -o celebration.gif
```

## Get Full Metadata

```bash
curl -sG "https://api.giphy.com/v1/gifs/search" \
  --data-urlencode "q=cat" -d limit=3 -d rating=g -d "api_key=${GIPHY_API_KEY}" \
  | jq '.data[] | {title, page: .url, gif: .images.original.url, preview: .images.fixed_height_small.url, mp4: .images.original.mp4, width: .images.original.width, height: .images.original.height}'
```

Check `.meta.status` (200 on success) and `.meta.msg` when results are empty; a 401/403
means the key is missing or invalid, 429 means the key's rate limit was hit.

## API Parameters

| Parameter | Description |
|-----------|-------------|
| `api_key` | API key (from `$GIPHY_API_KEY`), required |
| `q` | Search query, required (max 50 characters) |
| `limit` | Max results (default 25; beta keys max 50) |
| `offset` | Pagination offset (default 0) |
| `rating` | Content rating: `g`, `pg`, `pg-13`, `r` (omit = all ratings) |
| `lang` | Two-letter language code, e.g. `en`, `es`, `fr` |

Stickers use the same parameters at `https://api.giphy.com/v1/stickers/search`.

## Common Renditions

Each result has multiple renditions under `.images`:

| Rendition | Use case |
|-----------|----------|
| `original` | Full quality GIF (`.url`), plus `.mp4` / `.webp` variants |
| `fixed_height` | 200px tall, good default for chat |
| `fixed_height_small` | 100px tall preview |
| `downsized` | Size-capped GIF for upload limits |
| `preview_gif` | Very small preview |

## Notes

- Default to `rating=g` unless the user asks otherwise.
- For sending in chat, `fixed_height` URLs are lighter weight than `original`.
- GIF URLs can be used directly in markdown, e.g. `![thumbs up](https://media.giphy.com/media/<id>/giphy.gif)`.
