---
name: "imagegen"
description: "Generate or edit raster images when the task benefits from AI-created bitmap visuals such as photos, illustrations, textures, sprites, mockups, or transparent-background cutouts. Use when Codex should create a brand-new image, transform an existing image, or derive visual variants from references, and the output should be a bitmap asset rather than repo-native code or vector. Do not use when the task is better handled by editing existing SVG/vector/code-native assets, extending an established icon or logo system, or building the visual directly in HTML/CSS/canvas."
---

# Image Generation Skill

## Top-level modes and rules

Exactly two top-level modes:

- **Default built-in tool mode (preferred):** built-in `image_gen` tool for generation, edits, and transparent images. No `OPENAI_API_KEY` needed.
- **Fallback CLI mode:** `scripts/image_gen.py` CLI. Use when user explicitly asks for or confirms CLI/API/model path. Requires `OPENAI_API_KEY`.

CLI fallback subcommands:

- `generate`
- `edit`
- `generate-batch`

Rules:
- Do not switch to CLI fallback for ordinary quality, size, or file-path control.
- Transparent images: ask built-in `image_gen` for transparent background, preserve generated alpha.
- Never silently switch from built-in `image_gen` or CLI `gpt-image-2` to CLI `gpt-image-1.5`. Ask first unless user explicitly requested `gpt-image-1.5`.
- Word `batch` alone does not mean CLI fallback. Many assets or batch-generation without explicit ask for CLI/API/model controls: stay built-in, one call per requested asset or variant.
- Built-in tool fails or unavailable: tell user CLI fallback exists and requires `OPENAI_API_KEY`. Proceed only if user explicitly asks for it.
- User explicitly asks for CLI mode: use bundled `scripts/image_gen.py` workflow. Do not create one-off SDK runners.
- Never modify `scripts/image_gen.py`. Something missing: ask user before anything else.

Built-in save-path policy:
- Built-in mode: Codex saves generated images under `$CODEX_HOME/*` by default.
- Do not describe or rely on OS temp as default built-in destination.
- Do not describe or rely on any destination-path argument of built-in `image_gen`. Need specific location: generate first, then move or copy selected output from `$CODEX_HOME/generated_images/...`.
- Save-path precedence:
  1. User names destination: move or copy selected output there.
  2. Image for current project: move or copy final selected image into workspace before finishing.
  3. Only for preview or brainstorming: render inline. File can stay at default `$CODEX_HOME/*` path.
- Never leave project-referenced asset only at default `$CODEX_HOME/*` path.
- Do not overwrite existing asset unless user explicitly asked for replacement. Otherwise create sibling versioned filename such as `hero-v2.png` or `item-icon-edited.png`.

## When to use
- New image (concept art, product shot, cover, website hero)
- New image from one or more reference images for style, composition, or mood
- Edit existing image (inpainting, lighting or weather changes, background replacement, object removal, compositing, transparent background)
- Many assets or variants for one task

## When not to use
- Extending or matching existing SVG/vector icon set, logo system, or illustration library in repo
- Simple shapes, diagrams, wireframes, or icons better built directly in SVG, HTML/CSS, or canvas
- Small project-local asset edit when source file already exists in editable native format
- User clearly wants deterministic code-native output, not generated bitmap

## Decision tree

Two separate questions:

1. **Intent:** new image or edit of existing one?
2. **Execution strategy:** one asset or many assets/variants?

Intent:
- User wants to modify existing image while preserving parts of it: **edit**.
- User gives images only as references for style, composition, mood, or subject: **generate**.
- No images given: **generate**.

Built-in edit semantics:
- Built-in edit is for images already visible in conversation context: attachments or images generated earlier in thread.
- To edit local image file with built-in tool, first load it with built-in `view_image` tool so it enters conversation context, then run built-in edit flow.
- Do not promise arbitrary filesystem-path editing through built-in tool.
- Local file still needs direct file-path control, masks, or other CLI-only parameters: use CLI fallback only when user asks for it.
- Edits: preserve invariants aggressively, save non-destructively by default.

Execution strategy:
- Built-in default path: produce many assets or variants with one `image_gen` call per requested asset or variant.
- CLI fallback path: use `generate-batch` subcommand only when user explicitly chose CLI mode and needs many prompts/assets.
- Do not use `n` as substitute for separate prompts for distinct assets. `n` is for variants of one prompt. Distinct assets need distinct built-in calls or distinct CLI `generate-batch` jobs.

Assume new image unless user clearly asks to change existing one.

## Workflow
1. Pick top-level mode: built-in by default, including transparent output. Fallback CLI only if explicitly requested or confirmed.
2. Pick intent: `generate` or `edit`.
3. Decide: preview-only, or consumed by current project?
4. Pick execution strategy: single asset, repeated built-in calls, or CLI `generate-batch`.
5. Collect inputs up front: prompt(s), exact text (verbatim), constraints/avoid list, input images.
6. Label each input image's role explicitly:
   - reference image
   - edit target
   - supporting insert/style/compositing input
7. User asked for photo, illustration, sprite, product image, banner, or other explicitly raster asset: use `image_gen`, not SVG/HTML/CSS placeholders. Icon, logo, or UI graphic that should match existing repo-native SVG/vector/code assets: prefer editing those directly.
8. Augment prompt by specificity (Specificity policy below).
9. Inspect and validate outputs: subject, style, composition, text accuracy, invariants/avoid items.
10. Iterate with one targeted change, then re-check.
11. Project-bound work: move or copy selected artifact into workspace, update consuming code or references.
12. Batches or multi-asset requests: persist every requested final deliverable in workspace unless user explicitly asked for preview-only. Discarded variants need not be kept unless requested.
13. User explicitly chooses or confirms CLI fallback: use fallback-only docs for model, quality, size, `input_fidelity`, masks, output format, output paths, network setup.
14. Always report final saved path(s) for workspace-bound asset(s), final prompt or prompt set, and whether built-in tool or fallback CLI mode was used.

## Prompt augmentation

Reformat user prompts into structured, production-oriented spec. Make goal clearer and actionable; do not blindly add detail.

Prompt-shaping guidance, not closed schema. Use only lines that help. Add short extra labeled line when it materially improves clarity.

### Specificity policy

Prompt specificity sets how much to augment:

- Already specific and detailed: preserve that specificity, only normalize/structure it.
- Generic: may add tasteful augmentation when it materially improves result.

Allowed augmentations:
- composition or framing hints
- polish level or intended-use hints
- practical layout guidance
- reasonable scene concreteness supporting stated request

Not allowed augmentations:
- extra characters or objects not implied by request
- brand names, slogans, palettes, or narrative beats not implied
- arbitrary side-specific placement unless surrounding layout supports it

## Use-case taxonomy (exact slugs)

Classify each request into one of these buckets. Keep slug consistent across prompts and references.

Generate:
- photorealistic-natural — candid/editorial lifestyle scenes, real texture, natural lighting.
- product-mockup — product/packaging shots, catalog imagery, merch concepts.
- ui-mockup — app/web interface mockups and wireframes; specify desired fidelity.
- infographic-diagram — diagrams/infographics with structured layout and text.
- scientific-educational — classroom explainers, scientific diagrams, learning visuals with required labels and accuracy constraints.
- ads-marketing — campaign concepts, ad creatives with audience, brand position, scene, exact tagline/copy.
- productivity-visual — slide, chart, workflow, data-heavy business visuals.
- logo-brand — logo/mark exploration, vector-friendly.
- illustration-story — comics, children’s book art, narrative scenes.
- stylized-concept — style-driven concept art, 3D/stylized renders.
- historical-scene — period-accurate/world-knowledge scenes.

Edit:
- text-localization — translate/replace in-image text, preserve layout.
- identity-preserve — try-on, person-in-scene; lock face/body/pose.
- precise-object-edit — remove/replace specific element (including interior swaps).
- lighting-weather — time-of-day/season/atmosphere changes only.
- background-extraction — transparent background / clean cutout.
- style-transfer — apply reference style, change subject/scene.
- compositing — multi-image insert/merge, matched lighting/perspective.
- sketch-to-render — drawing/line art to photoreal render.

## Shared prompt schema

Shared labeled scaffolding for both top-level modes:

```text
Use case: <taxonomy slug>
Asset type: <where the asset will be used>
Primary request: <user's main prompt>
Input images: <Image 1: role; Image 2: role> (optional)
Scene/backdrop: <environment>
Subject: <main subject>
Style/medium: <photo/illustration/3D/etc>
Composition/framing: <wide/close/top-down; placement>
Lighting/mood: <lighting + mood>
Color palette: <palette notes>
Materials/textures: <surface details>
Text (verbatim): "<exact text>"
Constraints: <must keep/must avoid>
Avoid: <negative constraints>
```

Notes:
- `Asset type` and `Input images` are prompt scaffolding, not dedicated CLI flags.
- `Scene/backdrop` is visual setting. Not same as fallback CLI `background` parameter, which controls output transparency.
- Fallback-only execution notes (`Quality:`, `Input fidelity:`, masks, output format, output paths) belong in CLI path only. Do not treat them as built-in `image_gen` tool arguments.

Augmentation rules:
- Keep it short.
- Edits: list invariants explicitly (`change only X; keep Y unchanged`).
- Critical detail missing and blocking success: ask. Otherwise proceed.

## Examples

### Generation example (hero image)
```text
Use case: product-mockup
Asset type: landing page hero
Primary request: a minimal hero image of a ceramic coffee mug
Style/medium: clean product photography
Composition/framing: wide composition with usable negative space for page copy if needed
Lighting/mood: soft studio lighting
Constraints: no logos, no text, no watermark
```

### Edit example (invariants)
```text
Use case: precise-object-edit
Asset type: product photo background replacement
Primary request: replace only the background with a warm sunset gradient
Constraints: change only the background; keep the product and its edges unchanged; no text; no watermark
```

## Prompting best practices
- Structure prompt as scene/backdrop -> subject -> details -> constraints.
- State intended use (ad, UI mock, infographic) to set mode and polish level.
- Use camera/composition language for photorealism.
- Use SVG/vector stand-ins only when user explicitly asked for vector output or non-image placeholder.
- Quote exact text; specify typography + placement.
- Spell tricky words letter-by-letter; require verbatim rendering.
- Multi-image inputs: reference images by index, describe how to use each.
- Edits: repeat invariants every iteration to reduce drift.

## Guidance by asset type
Asset-type templates (website assets, game assets, wireframes, logo): `references/sample-prompts.md`.

## gpt-image-2 guidance for CLI fallback

Fallback CLI defaults to `gpt-image-2`.

- Use `gpt-image-2` for new CLI/API workflows unless user confirms different model.
- CLI `gpt-image-2` does not support `background=transparent`. Ask before using `gpt-image-1.5` unless user explicitly requested it.
- `gpt-image-2` always uses high fidelity for image inputs. Do not set `input_fidelity` with it.
- `gpt-image-2` supports `quality` values `low`, `medium`, `high`, and `auto`.
- Use `quality low` for fast drafts, thumbnails, quick iterations. Use `medium`, `high`, or `auto` for final assets, dense text, diagrams, identity-sensitive edits, high-resolution outputs.
- Square images usually generate fastest. Use `1024x1024` for fast square drafts.
- 4K-style output: `3840x2160` for landscape, `2160x3840` for portrait.
- `gpt-image-2` size may be `auto` or `WIDTHxHEIGHT` if all constraints hold: max edge `<= 3840px`, both edges multiples of `16px`, long-to-short ratio `<= 3:1`, total pixels between `655,360` and `8,294,400`.

Popular `gpt-image-2` sizes:
- `1024x1024` square
- `1536x1024` landscape
- `1024x1536` portrait
- `2048x2048` 2K square
- `2048x1152` 2K landscape
- `3840x2160` 4K landscape
- `2160x3840` 4K portrait
- `auto`

## Fallback CLI mode only

### Temp and output conventions
- Use `tmp/imagegen/` for intermediate files (for example JSONL batches). Delete when done.
- Write final artifacts under `output/imagegen/`.
- Control output paths with `--out` or `--out-dir`. Keep filenames stable and descriptive.

### Dependencies
Prefer `uv` for dependency management in this repo.

Required Python package:
```bash
uv pip install openai
```

Optional for image inspection and downscaling:
```bash
uv pip install pillow
```

Portability note:
- Installed skill outside this repo: install dependencies into that environment with its package manager.
- uv-managed environments: `uv pip install ...` stays preferred.

### Environment
- `OPENAI_API_KEY` must be set for live API calls.
- Do not ask user for `OPENAI_API_KEY` when using built-in `image_gen` tool.
- Never ask user to paste full key in chat. Ask them to set it locally and confirm when ready.

Key missing: give user these steps:
1. Create API key in OpenAI platform UI: https://platform.openai.com/api-keys
2. Set `OPENAI_API_KEY` as environment variable on their system.
3. Offer to guide them through setting it for their OS/shell if needed.

Installation not possible in this environment: tell user which dependency is missing and how to install it into their active environment.

## Reference map
- `references/prompting.md`: shared prompting principles, both modes.
- `references/sample-prompts.md`: shared copy/paste prompt recipes, both modes.
- `references/cli.md`: fallback-only CLI usage via `scripts/image_gen.py`.
- `references/image-api.md`: fallback-only API/CLI parameter reference.
- `references/codex-network.md`: fallback-only network/sandbox troubleshooting for CLI mode.
- `scripts/image_gen.py`: fallback-only CLI implementation. Use only when user explicitly chooses or confirms CLI mode.
