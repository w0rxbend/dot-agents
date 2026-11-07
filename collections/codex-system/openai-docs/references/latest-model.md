# Latest model fallback

Compact, non-authoritative fallback. Not a source for current availability, prices, aliases or defaults. First search and fetch current official model guidance at `https://developers.openai.com/api/docs/guides/latest-model` and relevant official model page. Fetched official docs win if snapshot drifted. Disclose any use of this fallback.

## Model roles

| Model ID | Documented workload (verify against current model page) |
| --- | --- |
| `gpt-6` | GPT-6 family alias. Verify currently documented routing and availability. |
| `gpt-6-astra` | Quality-first flagship, reasoning, difficult coding work. |
| `gpt-5.6-terra` | Balanced quality, latency, cost. |
| `gpt-5.6-luna` | Primary pick for faster or cheaper workloads. |

Actual GPT-6 migration: `https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#migration-quickstart`. Requested GPT-6 prompting: `https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#prompting-best-practices`. Open and read relevant page before recommending request shape, reasoning setting, endpoint, tool behavior or migration.

## Explicitly requested existing models

| Model ID | Boundary |
| --- | --- |
| `gpt-4.1` | Keep only when user explicitly requests this model or existing migration target. Search and fetch its own current official guide. |
| `gpt-5.4` | Keep only when user explicitly requests this model or existing migration target. Search and fetch its own current official guide. |

Do not promote legacy model as current default, substitute it into unrelated task, or replace explicitly requested legacy target with GPT-6 Astra. Recommend specialized image, audio, realtime, coding, moderation or embedding model only after verifying requested modality against current official docs.

Verify GPT-6 Pro against current official Responses and model docs before describing model IDs, reasoning modes, request parameters or account availability. Do not invent separate `gpt-6-pro` model slug.
