# Desktop App Plugins — UI Panes, Commands, Widgets

Plugins for Hermes desktop app: statusbar items, layout panes,
command-palette commands, keybinds, routes, themes. Each plugin is one
plain-JavaScript ESM file loaded at runtime. No build step, no repo
changes. Plugin can talk to own Python backend namespace
(`ctx.rest`/`ctx.socket` → `/api/plugins/<id>`). General Python plugin
system (`~/.hermes/plugins/`) documented separately.

TWO on-disk doors, same contract and hot reload:

- `$HERMES_HOME/desktop-plugins/<id>/plugin.js` — standalone desktop plugin.
  Loads enabled by default.
- `$HERMES_HOME/plugins/<id>/desktop/plugin.js` — desktop HALF of unified
  agent-plugin package. Folder holding Python plugin (`plugin.yaml`) and
  its `dashboard/plugin_api.py` backend also ships desktop UI, so one
  feature installs/uninstalls as one folder. Electron shell copies that half
  into `desktop-plugins/<id>/` (with `.hermes-package.json` marker), the
  ONLY root renderer loads from. Pane is therefore app-level, not tied to
  selected profile.
  This half is OPT-IN: listed in Capabilities → Plugins but off until user
  toggles it (matches Python half's `plugins.enabled` gate). Tell user to
  flip it on after install. Check that toggle before debugging any "plugin
  not appearing" report.

Full human reference (every export, area payloads, backend, security):
`website/docs/developer-guide/desktop-plugin-sdk.md`.

## When to Use

- User asks for new desktop UI element (pane, statusbar widget, dashboard,
  command) without modifying app itself.
- Surface data you compute (via gateway RPC) inside app.

## Prerequisites

- Hermes desktop app (loads plugins; CLI/gateway alone does not).
- Write access to `$HERMES_HOME/desktop-plugins/` (usually
  `~/.hermes/desktop-plugins/`).

## How to Run

1. Create `$HERMES_HOME/desktop-plugins/<name>/plugin.js` from
   `templates/plugin.js` (in this skill directory). Default
   `~/.hermes/...`; under named profile `~/.hermes/profiles/<profile>/...`.
2. App watches that directory: plugin loads within a few seconds of file
   landing; every later save hot-reloads in place. No reload step.
   (Fallback if missing: ⌘K → **Reload desktop plugins**.)
3. Load failure shows toast naming error. Fix file, save again.

## Quick Reference

ONLY import surface: `@hermes/plugin-sdk` (plus `react` /
`react/jsx-runtime`, resolving to app's own React).

- `host.state.*` — readonly reactive atoms: `activeSessionId`, `busy`,
  `awaitingResponse`, `busyBySession`, `cwd`, `gateway` (socket state, not
  turn-busy), `model`, `profile`, `viewport`, plus tile-aware focused
  session atoms: `focusedSessionId` (runtime id; key for `session.*` RPC),
  `focusedStoredSessionId` (durable id; navigation / list matching),
  `focusedSessionProfile` (owner profile of focused chat; prefer over
  `profile` for per-bot/profile readouts, since `profile` is gateway
  socket's home and does not move with tab focus), and
  `focusedUsage` (live streamed `UsageStats` of focused session, no RPC
  needed). `busy`: true while focused chat works after a send (thinking
  and streaming). `awaitingResponse`: true until first assistant payload.
  `busyBySession`: runtime session id → mid-turn, for rosters watching
  every session. Readouts that should follow user between tiles: use
  focused atoms. Read with `.get()` in handlers,
  `useValue(atom)` in components.
- `host.request(method, params)` — gateway JSON-RPC (sessions, config,
  skills, cron: everything app uses).
- `host.onEvent(type, fn)` — live gateway events (`'*'` for all). Returns
  disposer.
- `host.notify({ kind, message })`, `host.navigate(path)`, `host.logs(...)`,
  `host.status()`, `haptic('tap')`.
- `ctx.register({ id, area, order?, render?, data? })` — contribute UI.
  Key areas: `'statusBar.right'`/`'statusBar.left'` (chips),
  `'panes'` (layout zones; set `title` and
  `data: { placement, dock?, width?, height? }`, pane auto-joins matching
  zone), `PALETTE_AREA` (⌘K commands), `KEYBINDS_AREA` (rebindable
  actions), `THEMES_AREA` (`data` is full `DesktopTheme`).
- THEMES: registering one only lists it in picker. Select with
  `useTheme().setTheme(name)` from component, or `requestTheme(name)` from
  callback with no component (gateway event, socket handler).
  `requestTheme` returns `false` for unresolved name and leaves appearance
  alone; use it as availability check instead of forcing user back to
  default skin.
- Pane placement: `placement: 'left'|'right'|'bottom'|'main'` is semantic
  role; pane stacks (tabs) with existing panes of that role. For specific
  EDGE, add `dock: { pane, pos }` (same as dragging onto pane's drop chip).
  `pane`: any pane id (`workspace` is main thread; also `sessions`,
  `terminal`, `files`, `review`, `logs`). `pos`:
  `'top'|'bottom'|'left'|'right'|'center'`.
  E.g. "below the conversation" = `dock: { pane: 'workspace', pos: 'bottom' }`.
  Declare `height` (e.g. `'200px'`) so it doesn't take half the zone.
- Full PAGES: register `area: ROUTES_AREA` with `data: { path: '/my-page' }`
  and `render`. Page mounts in workspace (main) pane like built-in views.
  Reach it via sidebar nav row:
  `ctx.register({ id: 'nav', area: SIDEBAR_NAV_AREA, data: { path: '/my-page', label: 'My Page', codicon: 'project' } })`
  (renders below Artifacts, lights up at route), and/or
  `PALETTE_AREA` command calling `host.navigate('/my-page')`.
- TRANSCRIPT directives: register `area: TRANSCRIPT_DIRECTIVE_AREA` with
  `data: { name: 'task', render: ({ attrs, streaming }) => jsx(...) }`.
  Assistant then renders your component inline in chat message when it
  emits `::task{id="BB-12"}` alone on its own line. Attrs are untrusted
  `key="value"` strings; validate. Unclaimed/malformed directives fall back
  to plain text. Reference: core's own `::preview{file="…"}`.
  After registering, TELL model it exists (bundled skill or user's
  instructions); it won't discover the name itself.
- `ctx.storage.get/set/remove` — persistence namespaced to your plugin.
- `ctx.os` — curated OS door, attributed to your plugin:
  `ctx.os.notify({ title, body?, silent?, icon?, activate?, onActivate?, actions? })`
  posts native OS notification. Fires only while user is away from Hermes
  (in-app toast: `host.notify`). Gated by Settings ▸ Notifications ▸
  "Plugin notifications", throttled per plugin; reserve for genuinely
  notable events. `activate` accepts plugin deep link
  (`hermes://index-network/intent/1`), hash path (`/index-network/intent/1`),
  or `{ path, params }` (same resolver as OS deep links). Action buttons may
  set own `activate` or `onAction`
  callback (renderer-only; only action id crosses IPC).
  `ctx.os.openExternal(url)`, `ctx.os.revealPath(path)`, and
  `ctx.os.writeClipboard(text)` resolve `false` (never throw) when
  capability unavailable.
- `ctx.i18n.register({ en, ja, ... })` — ship OWN locale bundles, scoped
  to your plugin (never edit core `en.ts`). Values: literal strings or
  interpolator functions; nested trees addressed by dot-path. Read
  reactively in components via `usePluginI18n(id)` returning `t('key', ...args)`
  (re-renders on locale switch), or `ctx.i18n.t` in handlers/stores.
  Resolution: app's active locale, then your `en`, then raw key.
- Data: `useQuery`/`useMutation`/`useQueryClient`/`queryClient` (app's ONE
  React Query client: cache, dedupe, `refetchInterval`, invalidate like core;
  never hand-roll poll loop), plus `atom`/`computed` for plugin-local state.
- Backend: if plugin ships Python `plugin_api.py` (under
  `~/.hermes/plugins/<id>/dashboard/`, manifest `"api": "plugin_api.py"`), call
  it with `ctx.rest('/path', { method?, body?, timeoutMs? })` and live twin
  `ctx.socket('/events', onMessage)`. Both scoped to `/api/plugins/<id>` by
  construction (traversal rejected). `ctx.socket` is **no-op on OAuth
  remotes**; always keep polling fallback. Python backend imported
  only when plugin is in `plugins.enabled` in `config.yaml` (separate from
  in-app enable toggle). Gateway-wide data: use `host.request` /
  `host.onEvent` instead.
- `Contribute` (mount-scoped): render `jsx(Contribute, { area, id, children })`
  inside component so page-owned chrome (e.g. titlebar control in
  `TITLEBAR_AREAS.center`) leaves on page unmount. `ctx.register` is for
  permanent contributions.
- `defaultEnabled: false` on default export ships opt-in plugin: listed in
  Settings → Plugins, off until user flips it on.
- Users manage plugins in Settings → Plugins (enable/disable live, reveal
  folder). Disabled plugin stays disabled across restarts. Don't fight it;
  user turned you off.
- UI: app's design language, importable directly: `Button`, `Input`,
  `Textarea`, `Select*`, `Switch`, `Checkbox`, `SegmentedControl`, `Tabs*`,
  `Dialog*`, `ConfirmDialog`, `DropdownMenu*`, `ContextMenu*`, `Popover*`,
  `Tip`/`Tooltip*`, `Badge`, `Kbd`/`KbdGroup`, `SearchField`, `ScrollArea`,
  `Separator`, `Skeleton`, `GlyphSpinner`, `EmptyState`, `ErrorState`,
  `CopyButton`, `StatusDot`, `LogView`, `Codicon`, `DecodeText`, plus `cn`
  and `icons.*`. Prefer these over hand-rolled elements so plugin looks
  native.

## Procedure

1. Pick short kebab-case `id`; folder name must match.
2. Keep `templates/plugin.js` default export shape
   (`{ id, name, register(ctx) }`).
3. For pane, register `area: 'panes'` with `placement` hint and `render`
   returning your component. App places it in sensible zone automatically;
   user can drag it anywhere afterwards.
4. Fetch data with `host.request` and/or subscribe with `host.onEvent`;
   never poll faster than a few seconds.
5. Write file with your file tools, then ask user to run
   **Reload desktop plugins** from ⌘K.

## Pitfalls

- NEVER hardcode colors or backgrounds (`#000`, `black`, `rgb(...)`). Panes
  already sit on app's editor background: leave it alone. Use theme
  variables for everything else: `var(--ui-text-secondary)`,
  `var(--ui-text-quaternary)`, `var(--ui-stroke-secondary)`,
  `var(--ui-accent)`. For canvas drawing, resolve once with
  `getComputedStyle(canvas).getPropertyValue('--ui-accent')`.
- Reference only what you imported. Missing import (e.g. `StatusDot`) is
  ReferenceError at render. Check every identifier in `jsx()` calls
  appears in import line.
- Canvas panes MUST track container with `ResizeObserver` and re-size
  canvas (width/height attributes, not just CSS). Panes resize constantly
  (sash drags, layout switches); mount-time-only size leaves blank space or
  blurry scaling.
- JSX syntax will not parse; file loads uncompiled. Use
  `jsx('div', { children: ... })` from `react/jsx-runtime`.
- Do not import anything except `@hermes/plugin-sdk`, `react`, and
  `react/jsx-runtime`; other specifiers fail to resolve.
- Handlers must read state imperatively (`$atom.get()`), never from render
  closures. Otherwise rapid events see stale values.
- Keep components small; subscribe (`useValue`) only in leaf rendering
  the value.

## Verification

- Plugin UI appears after **Reload desktop plugins**.
- No error toast ("Plugin <name> failed to load"). If one appears, message
  names failure; fix and reload.
- Panes: new zone visible and draggable like any core pane.
