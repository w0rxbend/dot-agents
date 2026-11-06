# TUI Widgets — Live Panels for the Ink TUI Dock

Widget apps for Hermes TUI (`hermes --tui`): glanceable ambient panels docked
above status bar, or modal overlays owning keyboard. Plain ESM files loaded
at TUI startup. No build step, no repo changes. Not for desktop-app or
web-dashboard widgets.

## When to Use

- Live TUI panel (ticker, clock, countdown, status card, API-backed readout).
- Custom modal tool (picker, calculator, viewer) bound to slash command.

## Prerequisites

- TUI must be in use (`hermes --tui`). Widgets do not render in classic CLI
  or messaging platforms.
- Network-backed widgets need their API's credentials. Fetch failures must
  land as error phase, never crash.

## How to Run

1. `write_file` to `~/.hermes/tui-widgets/<name>.mjs` (working example:
   `templates/clock.mjs`).
2. Running TUI hot-loads file within ~a second (directory watched);
   `/widgets-reload` forces rescan.
3. Widget id becomes slash command (`/<id>`); its `help` shows in `/`
   completion popover. No other registration exists.
4. Auto-open (no command): end `register(sdk)` with
   `sdk.openWidget(app, app.init(''))`; widget docks on file load. Only when
   user asked; re-docks on every `/widgets-reload`.

## Quick Reference

Widget file default-exports `register(sdk)`:

```js
export default function register(sdk) {
  const { Box, Text, defineWidgetApp, h } = sdk

  defineWidgetApp({
    id: 'clock',                    // slash command name
    help: 'live clock in the dock', // `/` completion metadata
    mode: 'ambient',                // 'ambient' docks; 'modal' takes input
    init: arg => ({ label: arg.trim() || 'UTC' }),   // null = print usage
    reduce: (state, { ch, key }) => (key.escape || ch === 'q' ? null : state),
    render: ({ state, t }) => h(sdk.Dialog, { width: 24 }, h(Text, { color: t.color.label }, state.label))
  })
}
```

`sdk` contents: `defineWidgetApp`, `openWidget`, `updateWidget`, `isCtrl`,
`React`, `h` (createElement — no JSX in .mjs), components `Box`, `Text`,
`Dialog`, `Overlay`, `WidgetGrid`, `GridAreas`, loaders `Shimmer`,
`ShimmerRows`, `useShimmerPhase`. Loading phases: `ShimmerRows`, not bare
"loading…" line.

Expand/collapse: `sdk.Accordion`, same primitive as session panel's
tool/skill sections. `h(Accordion, { t, title: 'details', count: 3,
defaultOpen: false }, body)` toggles on CLICK (works in ambient widgets,
which get no keys). Modal apps may pass `open` + `onToggle` to drive it from
reducer state.

Stable sizing (cards must NEVER resize while ticking):

- Give `Dialog` explicit `width`. Charts return exactly requested `width`
  (short series pad-left while history warms up).
- Pad dynamic numbers: `String(v).padStart(6)`. `51 ms` → `112 ms` must not
  change line length.
- Constant row count per phase; swap content, not structure.

Charts (pure string builders; color with theme tones):

- `sdk.sparkline(series, width?)` → `▂▃▅▇█▆` one-row trend
- `sdk.sparkRows(series, width, rows)` → multi-row column chart (top line
  first), mission-control panel look; taller cells gain resolution
- `sdk.gauge(ratio, width)` → `█████░░░` fill bar for a 0..1 value
- `sdk.hbars(values, width)` → horizontal bar chart, one bar per value,
  eighth-block tips, scaled to max

Rolling series in component state (push per tick, cap ~120 samples).
`sparkRows` for dashboard panels, `sparkline` for one-liners.

Contract essentials:

- `mode: 'ambient'` — no input captured; command toggles it. `render`
  returns a CARD (usually `Dialog`), never `Overlay`. Placement via `zone`;
  every zone RESERVES real space (nothing paints over transcript):
  - Docks (chrome rows): `dock-top` (under top status bar),
    `dock-bottom` (default — above bottom one).
  - Rails (side columns beside transcript; text reflows around them):
    `top-left`, `top-right`, `bottom-left`, `bottom-right`. Corner name picks
    rail side and top/bottom anchor. Set app `width` to card width (match
    Dialog width; default 44); rail reserves exactly that many columns.
  Map user's words to nearest zone: "top right" → `top-right`,
  "above/next to the status bar" → a dock. Rails suit narrow cards
  (~30-46 cols); full-width or short-and-wide content belongs in a dock.
- `mode: 'modal'` (default) — owns every keypress. `reduce` returns next
  state, same reference to swallow key, or `null` to close. `render` wraps
  content in `Overlay` for placement.
- Async data: fetch from `init`, land results with
  `sdk.updateWidget(app, fn)`. No-op if widget closed, so late reply never
  resurrects it.
- Animation: timer inside component via `React.useState` +
  `React.useEffect` (see template); intervals ≥ 250ms.
- Colors: ALWAYS theme tones (`t.color.primary/label/muted/ok/error/…`),
  never hardcoded hexes. Must survive `/skin` and light/dark.

## Procedure

1. Pick `id`, `mode`, state shape; keep state serializable.
2. Write file from template; wire data via `init` + `updateWidget`.
3. `/<id>` launches (hot-loaded on write); `/<id>` again dismisses ambient
   widget.
4. Iterate: edits hot-reload on save (last-writer-wins, fresh definition
   shadows old). Relaunch `/<id>` to remount.

## Pitfalls

- No JSX, no bare imports in `.mjs`. Everything comes from `sdk` parameter;
  `h(...)` builds elements.
- Never ship modal without close path (`Esc`/`q` returning `null`).
- Ambient widgets must stay small (≤ ~6 rows): dock sits between transcript and
  status bar.
- Thrown `register()` gets logged and skipped. Widget missing: check
  `~/.hermes/logs/tui_gateway_crash.log`.

## Verification

`/widgets-reload`: transcript line lists file under `loaded:`. Then `/<id>`:
ambient widget docks right, above status bar; composer still accepts input.
`/<id>` again removes it.
