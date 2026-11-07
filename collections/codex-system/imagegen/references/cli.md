# CLI reference (`scripts/image_gen.py`)

Fallback CLI mode only. Read when user explicitly asks for `scripts/image_gen.py` / CLI / API / model controls, or explicitly confirms transparent-output request should use `gpt-image-1.5` true-transparency fallback.

`generate-batch` is CLI subcommand of this fallback path, not top-level skill mode.
Word `batch` in user request alone is not CLI opt-in.

## What this CLI does
- `generate`: new image from prompt
- `edit`: edit one or more existing images
- `generate-batch`: many generation jobs from JSONL file, after user explicitly chooses CLI/API/model controls

Real API calls need **network access** + `OPENAI_API_KEY`. `--dry-run` does not.

## Quick start (works from any repo)
Set stable path to skill CLI (default `CODEX_HOME` is `~/.codex`):

```
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export IMAGE_GEN="$CODEX_HOME/skills/.system/imagegen/scripts/image_gen.py"
```

Install dependencies with that environment's package manager. uv-managed environments: prefer `uv pip install ...`.

Dry-run (no API call, no network, no `openai` package needed):

```bash
python "$IMAGE_GEN" generate \
  --prompt "Test" \
  --out output/imagegen/test.png \
  --dry-run
```

Notes:
- One-off dry-runs print API payload and computed output path(s).

Generate:

```bash
python "$IMAGE_GEN" generate \
  --prompt "A cozy alpine cabin at dawn" \
  --size 1024x1024 \
  --out output/imagegen/alpine-cabin.png
```

Edit:

```bash
python "$IMAGE_GEN" edit \
  --image input.png \
  --prompt "Replace only the background with a warm sunset" \
  --out output/imagegen/sunset-edit.png
```

## Guardrails
- Run bundled CLI directly (`python "$IMAGE_GEN" ...`) after activating correct environment.
- Do **not** write one-off runners (for example `gen_images.py`) unless user explicitly asks for custom wrapper.
- **Never modify** `scripts/image_gen.py`. If something is missing, ask user before anything else.
- Do not silently downgrade from CLI `gpt-image-2` or built-in `image_gen` to CLI `gpt-image-1.5`. Ask first unless user explicitly requested `gpt-image-1.5`.

## Defaults
- Model: `gpt-image-2`
- Supported model family: GPT Image models (`gpt-image-*`)
- Size: `auto`
- Quality: `medium`
- Output format: `png`
- Default one-off output path: `output/imagegen/output.png`
- Background: unspecified unless `--background` set

## gpt-image-2 size and model guidance

- `--quality low`: fast drafts, thumbnails, quick iterations.
- `--quality medium`, `--quality high`, or `--quality auto`: final assets, dense text, diagrams, identity-sensitive edits, high-resolution outputs.
- Square images usually fastest. Quick square drafts: `--size 1024x1024`.
- If user asks for 4K-style output, use `--size 3840x2160` (landscape) or `--size 2160x3840` (portrait).
- Do not pass `--input-fidelity` with `gpt-image-2`; it always uses high fidelity for image inputs.
- Do not use `--background transparent` with CLI `gpt-image-2`. Ask before using `gpt-image-1.5` unless user explicitly requested that model.

Popular `gpt-image-2` sizes:
- `1024x1024`
- `1536x1024`
- `1024x1536`
- `2048x2048`
- `2048x1152`
- `3840x2160`
- `2160x3840`
- `auto`

`gpt-image-2` size constraints:
- max edge `<= 3840px`
- both edges multiples of `16px`
- long edge to short edge ratio `<= 3:1`
- total pixels between `655,360` and `8,294,400`
- outputs above `2560x1440` total pixels experimental

Final 2K landscape:

```bash
python "$IMAGE_GEN" generate \
  --prompt "A polished landing-page hero image of a matte ceramic mug on a stone surface" \
  --quality high \
  --size 2048x1152 \
  --out output/imagegen/mug-hero.png
```

True transparent fallback request:

Confirm with user before running this command unless they explicitly requested `gpt-image-1.5`.

```bash
python "$IMAGE_GEN" generate \
  --model gpt-image-1.5 \
  --prompt "A clean product cutout on a transparent background" \
  --background transparent \
  --output-format png \
  --out output/imagegen/product-cutout.png
```

Explain: CLI `gpt-image-2` does not support `background=transparent`, so transparent CLI output needs confirmed `gpt-image-1.5` fallback.

## Quality, input fidelity, and masks (CLI fallback only)
Explicit CLI controls, not built-in `image_gen` tool arguments.

- `--quality` works for `generate`, `edit`, `generate-batch`: `low|medium|high|auto`
- `--input-fidelity` is **edit-only**, validated as `low|high`
- `--mask` is **edit-only**

Example:

```bash
python "$IMAGE_GEN" edit \
  --model gpt-image-1.5 \
  --image input.png \
  --prompt "Change only the background" \
  --quality high \
  --input-fidelity high \
  --out output/imagegen/background-edit.png
```

Mask notes:
- Multi-image edits: repeat `--image` flags. Order matters; describe each image by index and role in prompt.
- CLI accepts a single `--mask`.
- Image and mask must be same size and format, each under 50MB.
- Masks must include alpha channel.
- Multiple input images: mask applies to first image.
- Masking is prompt-guided. Do not promise exact pixel-perfect mask boundaries.
- Prefer PNG mask. Script mask handling is best-effort: no full preflight validation beyond file checks/warnings.
- Repeat invariants in edit prompt (`change only the background; keep the subject unchanged`) to reduce drift.

## Output handling
- `tmp/imagegen/`: temporary JSONL inputs, scratch files.
- `output/imagegen/`: final outputs.
- Reruns fail on existing target file unless you pass `--force`.
- `--out-dir` switches one-off naming to `image_1.<ext>`, `image_2.<ext>`, and so on.
- Downscaled copies get default suffix `-web` unless overridden.

## Common recipes

Generate with augmentation fields:

```bash
python "$IMAGE_GEN" generate \
  --prompt "A minimal hero image of a ceramic coffee mug" \
  --use-case "product-mockup" \
  --style "clean product photography" \
  --composition "wide product shot with usable negative space for page copy" \
  --constraints "no logos, no text" \
  --out output/imagegen/mug-hero.png
```

Generate and also write downscaled copy for fast web loading:

```bash
python "$IMAGE_GEN" generate \
  --prompt "A cozy alpine cabin at dawn" \
  --size 1024x1024 \
  --downscale-max-dim 1024 \
  --out output/imagegen/alpine-cabin.png
```

Generate multiple prompts concurrently (async batch):

```bash
mkdir -p tmp/imagegen output/imagegen/batch
cat > tmp/imagegen/prompts.jsonl << 'EOF'
{"prompt":"Cavernous hangar interior with a compact shuttle parked near the center","use_case":"stylized-concept","composition":"wide-angle, low-angle","lighting":"volumetric light rays through drifting fog","constraints":"no logos or trademarks; no watermark","size":"1536x1024"}
{"prompt":"Gray wolf in profile in a snowy forest","use_case":"photorealistic-natural","composition":"eye-level","constraints":"no logos or trademarks; no watermark","size":"1024x1024"}
EOF

python "$IMAGE_GEN" generate-batch \
  --input tmp/imagegen/prompts.jsonl \
  --out-dir output/imagegen/batch \
  --concurrency 5

rm -f tmp/imagegen/prompts.jsonl
```

Notes:
- `generate-batch` requires `--out-dir`.
- `--concurrency` sets parallelism (default `5`).
- JSONL supports per-job overrides (for example `size`, `quality`, `background`, `output_format`, `output_compression`, `moderation`, `n`, `model`, `out`, and prompt-augmentation fields).
- `--n`: multiple variants of one prompt. `generate-batch`: many different prompts.
- Batch mode: per-job `out` is filename under `--out-dir`.
- Many requested deliverable assets: one prompt/job per distinct asset, semantic filenames when possible.

## CLI notes
- Supported sizes depend on model. `gpt-image-2`: flexible constrained sizes. Older GPT Image models: `1024x1024`, `1536x1024`, `1024x1536`, or `auto`.
- True transparent CLI output requires `output_format` `png` or `webp`.
- Supported: `--prompt-file`, `--output-compression`, `--moderation`, `--max-attempts`, `--fail-fast`, `--force`, `--no-augment`.
- Do not assume older non-GPT image-model behavior applies.

## See also
- API parameter quick reference for fallback CLI mode: `references/image-api.md`
- Prompt examples shared across both top-level modes: `references/sample-prompts.md`
- Network/sandbox notes for fallback CLI mode: `references/codex-network.md`
- Built-in-first transparent image workflow: `SKILL.md`
