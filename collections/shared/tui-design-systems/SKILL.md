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

Rules for new or overhauled Ratatui TUI visuals without breaking interaction model. For this user's Rust terminal dashboards; pair with repo-local app instructions.

## When to Use

- New Ratatui dashboard visual layer (themes, panels, badges, meters, tabs).
- Redesigning/restyling existing Ratatui TUI, especially with multiple themes, live theme picker, mouse hit-testing or deterministic screenshot gate in CI.

## Token architecture

- Keep palettes flat, const, few: one semantic-role struct per theme, swapped by pointer. Derive every *layered or blended* colour as token from those roles with one RGB `blend()`: `surface` and `surface_hi` (panel, overlay fills), `track` (empty bar end), `fade` (colour dimmed toward background), `gradient` (accent run), `on_color` (readable badge text, picked by luminance). New palette then restyles every component at once, as live theme picker needs.
- Widgets never name literal `Color`, only theme tokens.
- Guard `blend()` against non-RGB endpoints: ANSI colours have no channels, so snap to nearer endpoint, do not invent one.

## Background-less themes

- Theme with `Color::Reset` background (mono/TTY palette) must degrade every fill: surfaces fall to `Reset`, badges become bracketed coloured text, empty bar ends use border colour, not derived track (that is `Reset`, renders as terminal default foreground). Test it paints only `Reset` and selection highlight.

## Background integrity

- Sweep every view × overlay with cell-buffer test: each cell background must be in theme-provided whitelist (`is_background` token list), not hardcoded colour list. Hardcoded list needs edit per new token and gets forgotten.
- `Clear` resets cells without repainting; whatever draws after it must restyle background. Fill overlays with raised surface so they float above panels.
- ratatui's `Chart` paints plot area via `Canvas` whose background defaults to `Color::Reset`. In tinted panel, set chart background to *panel's* fill, not page's: page colour inside surface-coloured card is same hole, one level up.

## Layout-coupled hit testing

- If mouse hit-testing mirrors drawn layout (tab strips, segmented bars, status fields), change drawing and mirror math in same edit. Prefer render-driven tests locating each label by drawn column; hand-written rect assertions pass while real layout puts widget elsewhere.
- Adding or widening list highlight symbol shifts every row's text. Clickable row regions must be full-width or recomputed to match.

## Glyphs

- Sub-cell meter precision uses eighth blocks (U+258F..U+2589), Block Elements: Unicode path only; ASCII fallback fills whole cells. Braille charts and sparklines too: supply ASCII substitute, do not leak box-drawing into `--ascii` mode.
- Aligned-column icons must be single-width BMP symbols. Emoji are double-width, silently shifting every later column in row.

## Verification

- Redesign: change styles first, text second. Rendering tests assert text content, so untouched strings keep suite green while look changes.
- Visual gate: project's deterministic screenshot generator (fixed frame counter, no wall-clock, no RNG). Text-dump mode is fastest layout review. Commit regenerated images with source change so CI's no-drift check passes.
- Check backgrounds on cell buffer, not rendered image: image writer resolving `Color::Reset` to theme background hides exactly the holes buffer sweep catches.
- Keep frame-counter-driven animation (pulses, blinks) deterministic for reproducible screenshots.
