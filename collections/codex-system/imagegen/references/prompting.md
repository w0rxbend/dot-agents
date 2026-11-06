# Prompting best practices

Shared by both top-level skill modes:
- built-in `image_gen` tool (default)
- explicit `scripts/image_gen.py` CLI fallback

## Contents
- [Structure](#structure)
- [Specificity policy](#specificity-policy)
- [Allowed and disallowed augmentation](#allowed-and-disallowed-augmentation)
- [Composition and layout](#composition-and-layout)
- [Constraints and invariants](#constraints-and-invariants)
- [Text in images](#text-in-images)
- [Input images and references](#input-images-and-references)
- [Iterate deliberately](#iterate-deliberately)
- [Transparent images](#transparent-images)
- [Fallback-only execution controls](#fallback-only-execution-controls)
- [Use-case tips](#use-case-tips)
- [Where to find copy/paste recipes](#where-to-find-copypaste-recipes)

## Structure
- Keep consistent order: scene/backdrop, subject, key details, constraints, output intent.
- State intended use (ad, UI mock, infographic) to set polish level.
- Complex requests: short labeled lines, not one long paragraph.

## Specificity policy
- Specific, detailed prompt: normalize into clean spec. Add no creative requirements.
- Generic prompt: may add tasteful detail when it materially improves output.
- Examples in `sample-prompts.md` are fully-authored recipes, not default augmentation for every request.
- Photorealism goal: include `photorealistic` directly, plus concrete real-world texture (pores, wrinkles, fabric wear, material grain, imperfect everyday detail).

## Allowed and disallowed augmentation

Allowed for generic prompts:
- composition and framing cues
- intended-use or polish-level hints
- practical layout guidance
- reasonable scene concreteness supporting request

Do not add:
- extra characters, props, or objects not implied
- brand palettes, slogans, or story beats not implied
- arbitrary side-specific placement unless surrounding layout supports it

## Composition and layout
- Specify framing, viewpoint (close-up, wide, top-down), and placement only when it materially helps.
- Call out negative space if asset clearly needs room for UI or copy.
- Avoid left/right layout decisions unless user or surrounding layout supports them.
- People: describe body framing, scale, gaze, object interactions when they matter (`full body visible`, `looking down at the book`, `hands naturally gripping the handlebars`).

## Constraints and invariants
- State what must not change (`keep background unchanged`).
- Edits: say `change only X; keep Y unchanged`. Repeat invariants every iteration to reduce drift.

## Text in images
- Literal text in quotes or ALL CAPS. Specify typography (font style, size, color, placement).
- Spell uncommon words letter-by-letter if accuracy matters.
- In-image copy: require verbatim rendering, no extra characters.
- CLI fallback mode: `medium` or `high` quality for small text, dense infographics, data-heavy slides, multi-font layouts, legends, axes, footnotes.

## Input images and references
- Do not assume every provided image is an edit target.
- Label each image by index and role (`Image 1: edit target`, `Image 2: style reference`).
- Images given for style, composition, or mood guidance, with no request to modify them: treat as generation with references.
- User asks to preserve existing image while changing specific parts: treat as edit.
- Compositing: describe how images interact (`place the subject from Image 2 into Image 1`).

## Iterate deliberately
- Start with clean base prompt, then small single-change edits.
- Re-specify critical constraints each iteration.
- Prefer one targeted follow-up at a time over rewriting whole prompt.

## Transparent images
- Ask built-in `image_gen` for genuinely transparent background; preserve its alpha.

## Fallback-only execution controls
- `quality`, `input_fidelity`, explicit masks, output format, output paths: fallback-only execution controls.
- Do not assume they are built-in `image_gen` tool arguments.
- User explicitly chooses CLI fallback: see `references/cli.md` and `references/image-api.md` for those controls.
- CLI fallback default: `gpt-image-2`. Supports `quality=low|medium|high|auto`. `low` for fast drafts and thumbnails; `medium`, `high`, or `auto` for final assets.
- `gpt-image-2` always uses high fidelity for image inputs. Do not set `input_fidelity` with it.
- CLI `gpt-image-2` does not support `background=transparent`. Ask before using `gpt-image-1.5` unless user explicitly requested that model.
- 4K-style output with `gpt-image-2`: `3840x2160` landscape, `2160x3840` portrait.

## Use-case tips
Generate:
- photorealistic-natural: prompt as real photo captured in the moment. Photography language (lens, lighting, framing); real texture; avoid over-stylized polish unless requested.
- product-mockup: describe product/packaging and materials; clean silhouette, clear label. In-image text: require verbatim rendering, specify typography.
- ui-mockup: state target fidelity first (shippable mockup or low-fi wireframe), then layout, hierarchy, practical UI elements. Avoid concept-art language.
- infographic-diagram: define audience and layout flow; label parts explicitly; require verbatim text; prefer higher quality in CLI mode for dense labels.
- logo-brand: simple, scalable; strong silhouette, balanced negative space; avoid decorative flourishes unless requested.
- ads-marketing: write like creative brief: brand positioning, audience, desired vibe, scene, exact tagline if text must appear.
- productivity-visual: name exact artifact (slide, chart, workflow diagram); define canvas and hierarchy; give real labels/data; ask for readable typography, polished spacing.
- scientific-educational: define audience, lesson objective, required labels, scientific constraints, arrows, scan-friendly whitespace.
- illustration-story: define panels or scene beats; keep each action concrete.
- stylized-concept: specify style cues, material finish, rendering approach (3D, painterly, clay). Invent no new story elements.
- historical-scene: state location/date and required period accuracy; constrain clothing, props, environment to era.

Edit:
- text-localization: change only text; preserve layout, typography, spacing, hierarchy; no extra words or reflow unless needed.
- identity-preserve: lock identity (face, body, pose, hair, expression); change only specified elements; match lighting and shadows.
- precise-object-edit: specify exactly what to remove/replace; preserve surrounding texture and lighting; keep everything else unchanged.
- lighting-weather: change only environmental conditions (light, shadows, atmosphere, precipitation); keep geometry, framing, subject identity.
- background-extraction: request clean cutout on genuinely transparent background; preserve fine edges and label text; no halos or restyling.
- style-transfer: name style cues to preserve (palette, texture, brushwork) and what must change; add `no extra elements` to prevent drift.
- compositing: reference inputs by index; say what moves where; match lighting, perspective, scale; keep base framing unchanged.
- sketch-to-render: preserve layout, proportions, perspective; pick materials and lighting that fit supplied sketch; add no new elements.

## Where to find copy/paste recipes
Copy/paste prompt specs (examples only): `references/sample-prompts.md`.
