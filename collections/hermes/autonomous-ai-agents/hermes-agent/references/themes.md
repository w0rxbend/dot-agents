# Themes / Skins — Author a Hermes Color Theme

Hermes **skin**: one YAML file theming CLI, TUI, and desktop GUI at once.
Skin engine (`hermes_cli/skin_engine.py`) resolves active skin; gateway pushes
it to every surface. Covers writing and activating skins, not GUI theme
editors or built-in presets.

## When to Use

- User wants custom Hermes look ("make me a synthwave theme", "dark forest
  vibes", "match my brand colors").
- User wants one palette across CLI/TUI/desktop.
- User iterates live ("that coral is too loud, make it teal"). Edit active
  skin's YAML; every surface repaints as your tool finishes.

## Prerequisites

- Write access to Hermes home: `~/.hermes` default, or `$HERMES_HOME` /
  active profile's dir. Skins live in `<hermes-home>/skins/`.
- Native tools: `write_file` (create YAML), `read_file` / `search_files`
  (inspect skins), `terminal` (activate via `hermes config set`).

## How to Run

1. Pick lowercase, hyphen-safe `name` (e.g. `synthwave`).
2. Copy `templates/skin.yaml`, fill palette. Keep every key; missing keys
   inherit `default` skin.
3. Write, activate, confirm: see Procedure.

## Quick Reference — element → key

Hex (`#rrggbb`). Theming is **semantic**: one key colors every element in
that role. Recolor one element: set key in its row (element-specific keys
fall back to shared key when unset).

| Visible element | Key to set | Falls back to |
|---|---|---|
| App background (whole TUI + GUI) | `background` | terminal default |
| **Tool-call marker** (`●`, tool spinner) | `ui_tool` | `ui_accent` |
| **Thinking / reasoning text** | `ui_thinking` | `banner_dim` |
| Accent — headings, links, chevrons, `Σ` | `ui_accent` / `banner_accent` | — |
| Heading / primary text | `banner_title` / `ui_primary` | — |
| Body / label text, user messages | `ui_text` / `banner_text`, `ui_label` | — |
| Muted / secondary, tree connectors | `banner_dim` | — |
| Borders, rules, gutters | `ui_border` / `banner_border` | — |
| Prompt symbol color | `prompt` | `banner_text` |
| Success / warn / error | `ui_ok` / `ui_warn` / `ui_error` | — |
| Status bar text + usage | `status_bar_text`, `status_bar_good/warn/bad/critical` | — |
| Diff add/remove (line + word) | `diff_added` / `diff_removed` / `diff_added_word` / `diff_removed_word` | built-in |
| Code syntax (string/number/keyword/comment) | `syntax_string` / `syntax_number` / `syntax_keyword` / `syntax_comment` | accent/text/border/muted |
| Completion menu | `completion_menu_bg` / `completion_menu_current_bg` / `…_meta_bg` | — |

`ui_accent` colors tool markers **and** headings/links/chevrons. Recolor
*only* tool calls (classic "change the gold `●`"): set `ui_tool`. `branding`
(`agent_name`, `prompt_symbol`, `welcome`, `goodbye`, `help_header`),
`spinner`, `tool_prefix`: optional flavor. Full schema in
`hermes_cli/skin_engine.py`.

## Procedure

1. **Design the palette.** `background` first, then `ui_accent` clearing WCAG
   AA against it (~4.5:1) for legible labels. GUI enforces contrast, yet
   low-contrast accent still looks washed out. Keep
   `ui_ok`/`ui_warn`/`ui_error` recognizably green/amber/red.
2. **Write the file** to `<hermes-home>/skins/<name>.yaml` with every
   top-level `colors` key from template.
3. **Apply it yourself — never hand-edit `config.yaml`.** Run safe writer via
   `terminal`:
   ```
   hermes config set display.skin <name>
   ```
   Skin watcher **repaints every surface live within ~a second** (CLI, TUI,
   desktop); skin appears in Appearance / `Cmd-K` / `/skin`. You apply it; do
   NOT tell user to run `/skin` (they can, but it's your job). Writer emits
   valid YAML; hand-edit can corrupt file and break live gateway (including
   `/`).
4. **Confirm the new look landed**, give revert:
   `hermes config set display.skin default` (or `/skin default`).

## Tweak the active look (change one thing)

User adjusts CURRENT look ("make the tool `●` cyan", "warmer background"):
one deterministic command edits ONE key of ACTIVE skin in place. Everything
else (background included) untouched:

```
hermes skin set <key> <hex>      # e.g. hermes skin set ui_tool "#00FFFF"
```

Edits active skin's file (active built-in gets forked into editable copy
keeping full palette); watcher repaints live. `hermes skin set background "#08201f"` changes
only background. `hermes skin use <name>` / `hermes skin list` switch and
enumerate.

## Pitfalls

- **Don't hardcode `~/.hermes`** under active profile. Resolve home from
  `$HERMES_HOME` first, fall back to `~/.hermes`.
- **Keep `#rrggbb` hex.** Shorthand `#rgb`, `rgb()`, named colors not
  guaranteed to parse everywhere.
- **Set `background`.** Without it GUI guesses base surface from text
  luminance. Usable, but no control of app background.
- **Name collisions**: skin named like desktop built-in (`mono`, `slate`,
  `cyberpunk`, `nous`, `midnight`, `ember`) won't override it on GUI. Pick
  fresh name.
- **To change one color, edit the ACTIVE skin — never fork `default`.** Forked
  `default` drops current palette: no `background` resets terminal to its
  own default (often black). Patch active skin's file in place so
  `background` and rest survive.

## Verification

- `read_file` `<hermes-home>/skins/<name>.yaml`: valid YAML, intended `name`
  and `colors`.
- `hermes config get display.skin` reports `<name>`.
- Repaint lands at turn end. Ask user to confirm new look.
