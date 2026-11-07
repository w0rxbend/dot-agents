---
name: ascii-video
description: "ASCII video: convert video/audio to colored ASCII MP4/GIF."
version: 1.0.0
author: SHL0MS, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ASCII, Video, FFmpeg, Terminal-Art]
    related_skills: []
---

# ASCII Video Production Pipeline

## When to use

Use when user requests: ASCII video, text art video, terminal-style video, character art animation, retro text visualization, audio visualizer in ASCII, converting video to ASCII art, matrix-style effects, or any animated ASCII output.

## What's inside

Pipeline for ASCII art video, any format: video/audio/images/generative input → colored ASCII character video (MP4, GIF, image sequence). Covers video-to-ASCII, audio-reactive music visualizers, generative ASCII animations, hybrid video+audio reactive, text/lyrics overlays, real-time terminal rendering.

## Creative Standard

Visual art. ASCII characters are medium; cinema is standard.

**User's prompt is a starting point.** Interpret with creative ambition, not literal transcription.

**First-render excellence is non-negotiable.** Output must be visually striking without revision rounds. If it looks generic, flat, or like "AI-generated ASCII art," it is wrong: rethink concept before shipping.

**Be proactively creative.** If references don't have what vision demands, build it. Add at least one visual moment user didn't ask for but will appreciate: transition, effect, or color choice that elevates the piece.

**Cohesive aesthetic over technical correctness.** All scenes must share one visual language: color temperature, related character palettes, consistent motion vocabulary. Every scene using a random different effect is aesthetic failure, even if technically correct.

**Dense, layered, considered.** Never flat black backgrounds. Always multi-grid composition, per-scene variation, intentional color.

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Video-to-ASCII** | Video file | ASCII recreation of source footage | `references/inputs.md` § Video Sampling |
| **Audio-reactive** | Audio file | Generative visuals driven by audio features | `references/inputs.md` § Audio Analysis |
| **Generative** | None (or seed params) | Procedural ASCII animation | `references/effects.md` |
| **Hybrid** | Video + audio | ASCII video with audio-reactive overlays | Both input refs |
| **Lyrics/text** | Audio + text/SRT | Timed text with visual effects | `references/inputs.md` § Text/Lyrics |
| **TTS narration** | Text quotes + TTS API | Narrated testimonial/quote video with typed text | `references/inputs.md` § TTS Integration |

## Stack

One self-contained Python script per project. No GPU required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | Python 3.10+, NumPy | Math, array ops, vectorized effects |
| Signal | SciPy | FFT, peak detection (audio modes) |
| Imaging | Pillow (PIL) | Font rasterization, frame decoding, image I/O |
| Video I/O | ffmpeg (CLI) | Decode input, encode output, mux audio |
| Parallel | concurrent.futures | N workers for batch/clip rendering |
| TTS | ElevenLabs API (optional) | Generate narration clips |
| Optional | OpenCV | Video frame sampling, edge detection |

## Pipeline Architecture

Every mode follows same 6-stage pipeline:

```
INPUT → ANALYZE → SCENE_FN → TONEMAP → SHADE → ENCODE
```

1. **INPUT** — Load/decode source (video frames, audio samples, images, or nothing)
2. **ANALYZE** — Extract per-frame features (audio bands, video luminance/edges, motion vectors)
3. **SCENE_FN** — Render to pixel canvas (`uint8 H,W,3`). Compose multiple character grids via `_render_vf()` + pixel blend modes. See `references/composition.md`
4. **TONEMAP** — Percentile-based adaptive brightness normalization. See `references/composition.md` § Adaptive Tonemap
5. **SHADE** — Post-processing via `ShaderChain` + `FeedbackBuffer`. See `references/shaders.md`
6. **ENCODE** — Pipe raw RGB frames to ffmpeg for H.264/GIF encoding

## Creative Direction

### Aesthetic Dimensions

| Dimension | Options | Reference |
|-----------|---------|-----------|
| **Character palette** | Density ramps, block elements, symbols, scripts (katakana, Greek, runes, braille), project-specific | `architecture.md` § Palettes |
| **Color strategy** | HSV, OKLAB/OKLCH, discrete RGB palettes, auto-generated harmony, monochrome, temperature | `architecture.md` § Color System |
| **Background texture** | Sine fields, fBM noise, domain warp, voronoi, reaction-diffusion, cellular automata, video | `effects.md` |
| **Primary effects** | Rings, spirals, tunnel, vortex, waves, interference, aurora, fire, SDFs, strange attractors | `effects.md` |
| **Particles** | Sparks, snow, rain, bubbles, runes, orbits, flocking boids, flow-field followers, trails | `effects.md` § Particles |
| **Shader mood** | Retro CRT, clean modern, glitch art, cinematic, dreamy, industrial, psychedelic | `shaders.md` |
| **Grid density** | xs(8px) through xxl(40px), mixed per layer | `architecture.md` § Grid System |
| **Coordinate space** | Cartesian, polar, tiled, rotated, fisheye, Möbius, domain-warped | `effects.md` § Transforms |
| **Feedback** | Zoom tunnel, rainbow trails, ghostly echo, rotating mandala, color evolution | `composition.md` § Feedback |
| **Masking** | Circle, ring, gradient, text stencil, animated iris/wipe/dissolve | `composition.md` § Masking |
| **Transitions** | Crossfade, wipe, dissolve, glitch cut, iris, mask-based reveal | `shaders.md` § Transitions |

### Per-Section Variation

Never reuse one config for whole video. Per section/scene:
- **Different background effect** (or compose 2-3)
- **Different character palette** (match mood)
- **Different color strategy** (or at least different hue)
- **Vary shader intensity** (more bloom in peaks, more grain in quiet)
- **Different particle types** if particles active

### Project-Specific Invention

Every project, invent at least one:
- Custom character palette matching theme
- Custom background effect (combine/modify existing blocks)
- Custom color palette (discrete RGB set matching brand/mood)
- Custom particle character set
- Novel scene transition or visual moment

Don't only pick from catalog. Catalog is vocabulary; you write the poem.

## Workflow

### Step 1: Creative Vision

Before any code, articulate concept:

- **Mood/atmosphere**: What should viewer feel? Energetic, meditative, chaotic, elegant, ominous?
- **Visual story**: What happens over time? Build tension? Transform? Dissolve?
- **Color world**: Warm/cool? Monochrome? Neon? Earth tones? Dominant hue?
- **Character texture**: Dense data? Sparse stars? Organic dots? Geometric blocks?
- **What makes THIS different**: One thing making this project unique?
- **Emotional arc**: Scene progression? Open with energy, build to climax, resolve?

Map user's prompt to aesthetic choices. A "chill lo-fi visualizer" needs different everything from a "glitch cyberpunk data stream."

### Step 2: Technical Design

- **Mode** — one of 6 modes above
- **Resolution** — landscape 1920x1080 (default), portrait 1080x1920, square 1080x1080 @ 24fps
- **Hardware detection** — auto-detect cores/RAM, set quality profile. See `references/optimization.md`
- **Sections** — map timestamps to scene functions, each with own effect/palette/color/shader config
- **Output format** — MP4 (default), GIF (640x360 @ 15fps), PNG sequence

### Step 3: Build the Script

Components (with references):

1. **Hardware detection + quality profile** — `references/optimization.md`
2. **Input loader** — mode-dependent; `references/inputs.md`
3. **Feature analyzer** — audio FFT, video luminance, or synthetic
4. **Grid + renderer** — multi-density grids with bitmap cache; `references/architecture.md`
5. **Character palettes** — multiple per project; `references/architecture.md` § Palettes
6. **Color system** — HSV + discrete RGB + harmony generation; `references/architecture.md` § Color
7. **Scene functions** — each returns `canvas (uint8 H,W,3)`; `references/scenes.md`
8. **Tonemap** — adaptive brightness normalization; `references/composition.md`
9. **Shader pipeline** — `ShaderChain` + `FeedbackBuffer`; `references/shaders.md`
10. **Scene table + dispatcher** — time → scene function + config; `references/scenes.md`
11. **Parallel encoder** — N-worker clip rendering via ffmpeg pipes
12. **Main** — orchestrate full pipeline

### Step 4: Quality Verification

- **Test frames first**: render single frames at key timestamps before full render
- **Brightness check**: `canvas.mean() > 8` for all ASCII content. If dark, lower gamma
- **Visual coherence**: all scenes feel like same video?
- **Creative vision check**: output matches Step 1 concept? If generic, go back

## Critical Implementation Notes

### Brightness — Use `tonemap()`, Not Linear Multipliers

Brightness is the #1 visual issue: ASCII on black is inherently dark. **Never use `canvas * N` multipliers**; they clip highlights. Use adaptive tonemap:

```python
def tonemap(canvas, gamma=0.75):
    f = canvas.astype(np.float32)
    lo, hi = np.percentile(f[::4, ::4], [1, 99.5])
    if hi - lo < 10: hi = lo + 10
    f = np.clip((f - lo) / (hi - lo), 0, 1) ** gamma
    return (f * 255).astype(np.uint8)
```

Pipeline: `scene_fn() → tonemap() → FeedbackBuffer → ShaderChain → ffmpeg`

Per-scene gamma: default 0.75, solarize 0.55, posterize 0.50, bright scenes 0.85. Use `screen` blend (not `overlay`) for dark layers.

### Font Cell Height

macOS Pillow: `textbbox()` returns wrong height. Use `font.getmetrics()`: `cell_height = ascent + descent`. See `references/troubleshooting.md`.

### ffmpeg Pipe Deadlock

Never use `stderr=subprocess.PIPE` with long-running ffmpeg: buffer fills at 64KB and deadlocks. Redirect to file. See `references/troubleshooting.md`.

### Font Compatibility

Not all Unicode chars render in all fonts. Validate palettes at init: render each char, check for blank output. See `references/troubleshooting.md`.

### Per-Clip Architecture

Segmented videos (quotes, scenes, chapters): render each segment as own clip file, for parallel rendering and selective re-rendering. See `references/scenes.md`.

## Performance Targets

~100-200ms/frame total; character render (80-150ms) is bottleneck. Per-component budget: `references/optimization.md` § Performance Budget.

## References

| File | Contents |
|------|----------|
| `references/architecture.md` | Grid system, resolution presets, font selection, character palettes (20+), color system (HSV + OKLAB + discrete RGB + harmony generation), `_render_vf()` helper, GridLayer class |
| `references/composition.md` | Pixel blend modes (20 modes), `blend_canvas()`, multi-grid composition, adaptive `tonemap()`, `FeedbackBuffer`, `PixelBlendStack`, masking/stencil system |
| `references/effects.md` | Effect building blocks: value field generators, hue fields, noise/fBM/domain warp, voronoi, reaction-diffusion, cellular automata, SDFs, strange attractors, particle systems, coordinate transforms, temporal coherence |
| `references/shaders.md` | `ShaderChain`, `_apply_shader_step()` dispatch, 38 shader catalog, audio-reactive scaling, transitions, tint presets, output format encoding, terminal rendering |
| `references/scenes.md` | Scene protocol, `Renderer` class, `SCENES` table, `render_clip()`, beat-synced cutting, parallel rendering, design patterns (layer hierarchy, directional arcs, visual metaphors, compositional techniques), scene examples at every complexity level, scene design checklist |
| `references/inputs.md` | Audio analysis (FFT, bands, beats), video sampling, image conversion, text/lyrics, TTS integration (ElevenLabs, voice assignment, audio mixing) |
| `references/optimization.md` | Hardware detection, quality profiles, vectorized patterns, parallel rendering, memory management, performance budgets |
| `references/troubleshooting.md` | NumPy broadcasting traps, blend mode pitfalls, multiprocessing/pickling, brightness diagnostics, ffmpeg issues, font problems, common mistakes |

---

## Creative Divergence (use only when user requests experimental/creative/unique output)

If user asks for creative, experimental, surprising, or unconventional output, pick best-fit strategy and reason through its steps BEFORE generating code.

- **Forced Connections** — when user wants cross-domain inspiration ("make it look organic," "industrial aesthetic")
- **Conceptual Blending** — when user names two things to combine ("ocean meets music," "space + calligraphy")
- **Oblique Strategies** — when user is maximally open ("surprise me," "something I've never seen")

### Forced Connections
1. Pick domain unrelated to visual goal (weather systems, microbiology, architecture, fluid dynamics, textile weaving)
2. List its core visual/structural elements (erosion → gradual reveal; mitosis → splitting duplication; weaving → interlocking patterns)
3. Map them onto ASCII characters and animation patterns
4. Synthesize: what does "erosion" or "crystallization" look like in a character grid?

### Conceptual Blending
1. Name two distinct visual/conceptual spaces (e.g., ocean waves + sheet music)
2. Map correspondences (crests = high notes, troughs = rests, foam = staccato)
3. Blend selectively: keep most interesting mappings, drop forced ones
4. Develop emergent properties existing only in blend

### Oblique Strategies
1. Draw one: "Honor thy error as a hidden intention" / "Use an old idea" / "What would your closest friend do?" / "Emphasize the flaws" / "Turn it upside down" / "Only a part, not the whole" / "Reverse"
2. Interpret directive against current ASCII animation challenge
3. Apply lateral insight to visual design before writing code
