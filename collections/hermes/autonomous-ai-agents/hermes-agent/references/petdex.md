# Petdex — Animated Pet Mascots

Browse, install, select animated "pet" mascots from public
[petdex](https://github.com/crafter-station/petdex) gallery. Installed pet
reacts to agent activity (idle, running a tool, reviewing, error, done) in
Hermes CLI, TUI, desktop app. Skill drives `hermes pets` CLI and
`display.pet` config; does not generate sprites.

## When to Use

- User wants desktop/terminal mascot or asks about "pets" / petdex.
- User wants to change, preview, or disable active pet.
- Diagnosing why pet isn't showing (terminal graphics support, config).

## Prerequisites

- Network access to `petdex.dev` for gallery/manifest (read-only, no auth).
- Pillow (core Hermes dependency) for sprite decoding; already installed.
- Full-fidelity terminal rendering needs graphics-capable terminal (kitty,
  Ghostty, WezTerm, iTerm2, or sixel). Otherwise falls back automatically
  to truecolor Unicode half-block.

## How to Run

Run `hermes pets <subcommand>` via `terminal` tool.

## Quick Reference

| Goal | Command |
| --- | --- |
| Browse gallery | `hermes pets list` (substring filters: `hermes pets list cat`) |
| List installed pets | `hermes pets list --installed` |
| Install pet | `hermes pets install <slug>` (`--select` makes it active) |
| Set active pet | `hermes pets select <slug>` (no slug opens picker) |
| Resize pet everywhere | `hermes pets scale <factor>` (e.g. `0.5`, clamped 0.1–3.0) |
| Preview/animate in terminal | `hermes pets show [slug] [--cycle] [--state run]` |
| Disable pet | `hermes pets off` |
| Remove pet | `hermes pets remove <slug>` |
| Diagnose setup | `hermes pets doctor` |

## Procedure

1. Find pet: `hermes pets list <query>`, note its `slug`.
2. Install + activate: `hermes pets install <slug> --select`.
3. Preview: `hermes pets show` (Ctrl+C to stop).
4. Confirm setup: `hermes pets doctor`. Shows resolved pet, configured
   render mode, detected terminal graphics protocol, effective mode.

Pets install into `<HERMES_HOME>/pets/<slug>/` (profile-aware). Selecting
pet writes `display.pet.slug` + `display.pet.enabled` to `config.yaml`.

## Configuration

Under `display.pet` in `config.yaml`:

- `enabled` (bool) — master on/off.
- `slug` (str) — active pet; empty = first installed.
- `render_mode` — `auto` (detect) | `kitty` | `iterm` | `sixel` | `unicode` | `off`.
- `scale` (float) — on-screen size of native 192×208 frames (default 0.33,
  clamped 0.1–3.0). One knob resizes every surface. Set via
  `hermes pets scale <factor>`, `/pet scale` slash command, or desktop
  Appearance slider.
- `unicode_cols` (int) — column width of Unicode fallback.

## Pitfalls

- Pet shows only once one is installed AND selected (`enabled: true`).
- Inside pipe/redirect (no TTY), terminal rendering disabled by design.
- petdex npm CLI installs to `~/.codex/pets`. Hermes uses own
  profile-scoped `<HERMES_HOME>/pets/` instead; install through `hermes pets`.

## Verification

- `hermes pets doctor` reports `✓ ready` when pet is installed, selected,
  enabled, and Pillow importable.
