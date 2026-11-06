# Image API quick reference

Fallback CLI mode only. Use when user explicitly asks for `scripts/image_gen.py` / CLI / API / model controls, or explicitly confirms transparent-output request should use `gpt-image-1.5` true-transparency fallback path.

## Scope
- Fallback CLI targets GPT Image models (`gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, and `gpt-image-1-mini`).

## Model summary

| Model | Quality | Input fidelity | Resolutions | Recommended use |
| --- | --- | --- | --- | --- |
| `gpt-image-2` | `low`, `medium`, `high`, `auto` | Always high for image inputs; do not set `input_fidelity` | `auto` or flexible sizes meeting constraints below | Default for new CLI/API workflows: high-quality generation and editing, text-heavy images, photorealism, compositing, identity-sensitive edits, workflows where fewer retries matter |
| `gpt-image-1.5` | `low`, `medium`, `high`, `auto` | `low`, `high` | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | True transparent-background fallback, backward-compatible workflows |
| `gpt-image-1` | `low`, `medium`, `high`, `auto` | `low`, `high` | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | Legacy compatibility |
| `gpt-image-1-mini` | `low`, `medium`, `high`, `auto` | `low`, `high` | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | Cost-sensitive draft batches, lower-stakes previews |

## gpt-image-2 sizes

`gpt-image-2` accepts `auto` or any `WIDTHxHEIGHT` size meeting all constraints:

- Max edge length at most `3840px`.
- Both edges must be multiples of `16px`.
- Long-to-short edge ratio must not exceed `3:1`.
- Total pixels must be at least `655,360` and no more than `8,294,400`.

Popular sizes:

| Label | Size | Notes |
| --- | --- | --- |
| Square | `1024x1024` | Typical fast default |
| Landscape | `1536x1024` | Standard landscape |
| Portrait | `1024x1536` | Standard portrait |
| 2K square | `2048x2048` | Larger square output |
| 2K landscape | `2048x1152` | Widescreen output |
| 4K landscape | `3840x2160` | Widescreen 4K output |
| 4K portrait | `2160x3840` | Vertical 4K output |
| Auto | `auto` | Default size |

## Endpoints
- Generate: `POST /v1/images/generations` (`client.images.generate(...)`)
- Edit: `POST /v1/images/edits` (`client.images.edit(...)`)

## Core parameters for GPT Image models
- `prompt`: text prompt
- `model`: image model
- `n`: number of images (1-10)
- `size`: `auto` by default for `gpt-image-2`. Flexible `WIDTHxHEIGHT` sizes allowed only for `gpt-image-2`. Older GPT Image models: `1024x1024`, `1536x1024`, `1024x1536`, or `auto`
- `quality`: `low`, `medium`, `high`, or `auto`
- `background`: generated-output transparency (`transparent`, `opaque`, or `auto`). Not the prompt's visual scene/backdrop
- `output_format`: `png` (default), `jpeg`, `webp`
- `output_compression`: 0-100 (jpeg/webp only)
- `moderation`: `auto` (default) or `low`

## Edit-specific parameters
- `image`: one or more input images; up to 16 for GPT Image models.
- `mask`: optional mask image
- `input_fidelity`: `low` or `high`, only on models that support it

Model-specific note for `input_fidelity`:
- `gpt-image-2` always uses high fidelity for image inputs; setting `input_fidelity` not supported.
- `gpt-image-1` and `gpt-image-1-mini` preserve all input images; first image gets richer textures and finer details.
- `gpt-image-1.5` preserves first 5 input images with higher fidelity.

## Transparent backgrounds

`gpt-image-2` does not currently support Image API `background=transparent`. In explicit CLI/API fallback mode, keep `gpt-image-2` when flat chroma-key background plus local alpha extraction via `python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py"` is acceptable.

Use CLI `gpt-image-1.5` with `background=transparent` and transparent-capable output format (such as `png` or `webp`) only after user explicitly confirms that fallback. Exception: user already requested `gpt-image-1.5`, `scripts/image_gen.py`, or CLI fallback. If user asks for true/native transparency, subject is too complex for clean chroma-key removal, or local background removal fails validation: explain tradeoff, ask before switching.

## Output
- `data[]` list with `b64_json` per image
- Bundled `scripts/image_gen.py` CLI decodes `b64_json` and writes output files.

## Limits and notes
- Input images and masks must be under 50MB.
- Use edits endpoint when user requests changes to existing image.
- Masking is prompt-guided; exact shapes not guaranteed.
- Large sizes and high quality raise latency and cost.
- `quality=low`: fast drafts, thumbnails, quick iterations. `medium` or `high`: final assets, dense text, diagrams, identity-sensitive edits, high-resolution outputs.
- High `input_fidelity` can materially raise input token usage on models supporting it.
- Request fails because selected GPT Image model does not support an option: retry manually without it only when user does not require it. If true transparent CLI output is required, ask before switching to `gpt-image-1.5` rather than dropping `background=transparent`, unless user already explicitly chose that fallback.

## Important boundary
- `quality`, `input_fidelity`, explicit masks, `background`, `output_format`, and related parameters are fallback-only execution controls.
- Do not assume they are built-in `image_gen` tool arguments.
