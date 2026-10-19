---
name: tui-design-systems
description: Design system for Ratatui terminal UIs - theme tokens, background integrity, layout and hit-testing, glyph fallbacks and deterministic screenshot gates. Use when building a new Ratatui dashboard or redesigning an existing TUI's visuals.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ratatui, tui, theming, design-system, terminal-ui]
    related_skills: [rust-linux-apps]
---

# TUI design systems (Ratatui)

Rules for building or overhauling the visual layer of a Ratatui TUI (themes, panels, badges, meters, tabs) without breaking the interaction model. Applies to this user's Rust terminal dashboards; pair with repo-local instructions for the specific app.

## When to Use

- Building a new Ratatui dashboard's visual layer (themes, panels, badges, meters, tabs).
- A redesign/restyle request for an existing Ratatui TUI, especially one with multiple themes, a live theme picker, mouse hit-testing, or a deterministic screenshot gate in CI.

## Token architecture

- Keep palettes flat, const, and few: one struct of semantic roles per theme, switchable by pointer swap. Compute every *layered or blended* colour as a derived token from those roles with a single RGB `blend()`: `surface` and `surface_hi` (panel and overlay fills), `track` (the empty end of a bar), `fade` (a colour dimmed toward the background), `gradient` (the accent run), `on_color` (readable text on a badge, picked by luminance). A new palette then restyles every component at once, which is what a live theme picker needs.
- Widgets never name a literal `Color`; they ask the theme for a token. That is what keeps dozens of palettes consistent.
- Guard `blend()` against non-RGB endpoints: ANSI colours have no channels to interpolate, so snap to the nearer endpoint instead of inventing one.

## Background-less themes

- A theme with `Color::Reset` as its background (a mono/TTY palette) must degrade every fill: surfaces fall through to `Reset`, badges become bracketed coloured text, and the empty end of bars uses the border colour rather than a derived track (which is `Reset` and would render as the terminal's default foreground). Test that such a theme paints only `Reset` and its selection highlight.

## Background integrity

- Sweep every view × overlay with a cell-buffer test asserting each cell's background against a theme-provided whitelist (an `is_background` token list), not a hardcoded colour list — a hardcoded list must be edited for every new token and will be forgotten.
- `Clear` resets cells without repainting; whatever draws after it must restyle the background, and overlays should fill with the raised surface so they read as floating above the panels.
- ratatui's `Chart` paints its plot area through a `Canvas` whose background defaults to `Color::Reset`. Inside a tinted panel, set the chart's background to the *panel's* fill, not the page's — a page-coloured rectangle inside a surface-coloured card is the same hole, one level up.

## Layout-coupled hit testing

- When mouse hit-testing mirrors a drawn layout (tab strips, segmented bars, status fields), change the drawing and the mirror math in the same edit, and prefer render-driven tests that locate each label by its drawn column — hand-written rect assertions pass while the real layout puts the widget elsewhere.
- Adding or widening a list's highlight symbol shifts every row's text; clickable row regions must be full-width or recomputed to match.

## Glyphs

- Sub-cell meter precision uses the eighth blocks (U+258F..U+2589), which are Block Elements: Unicode path only, with the ASCII fallback filling whole cells. The same rule covers braille charts and sparklines — supply an ASCII substitute rather than letting box-drawing leak into `--ascii` mode.
- Icons in aligned columns must be single-width BMP symbols; emoji are double-width and silently shift every column after them on that row.

## Verification

- Redesign by changing styles first and text second: rendering tests assert on text content, so untouched strings keep the suite green while the look changes underneath it.
- Use the project's deterministic screenshot generator (fixed frame counter, no wall-clock, no RNG) as the visual gate: the text-dump mode is the fastest layout review, and regenerated images are committed with the source change so CI's no-drift check passes.
- Verify background correctness on the cell buffer, not the rendered image — an image writer that resolves `Color::Reset` to the theme background hides exactly the holes the buffer sweep catches.
- Keep frame-counter-driven animation (pulses, blinks) deterministic so screenshots stay reproducible.
