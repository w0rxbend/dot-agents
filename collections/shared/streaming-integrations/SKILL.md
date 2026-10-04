---
name: streaming-integrations
description: Implement or debug OBS WebSocket v5 clients, Twitch OAuth/EventSub delivery, and event-driven OBS browser-source overlays, preserving session correlation and render-resource lifetimes.
license: MIT
---

Work from the checked-out protocol implementation, dependency lockfiles, and tests. In this portfolio OBS control clients, Twitch ingestion, the backend-to-overlay WebSocket, and browser rendering are separate boundaries. Identify which boundary fails before changing another one. Preserve the repository's language, effect system, UI stack, and public contract.

## Select the boundary

- OBS connection, authentication, requests, batching, or reconnect: read [references/obs-session.md](references/obs-session.md).
- Twitch first-run authorization, token refresh, permissions, or EventSub delivery: read [references/twitch-events.md](references/twitch-events.md).
- Pixi overlays, media assets, browser-source visibility, or rendering leaks: read [references/browser-sources.md](references/browser-sources.md).

Trace one input through the relevant path: transport message → validated domain event → queue/session state → user-visible output. Keep parsing and compatibility normalization at the boundary; scene code should receive the normalized event rather than repeatedly interpreting wire aliases. Adding a new event means checking backend serialization and every consuming scene, including unknown-event fallback.

Use recorded fixtures and fake transports for protocol work. Reconnect, timeout, slow-consumer, and teardown failures need deterministic tests that observe completion, cancellation, bounded resource use, and duplicate handling. Actual OBS, Twitch accounts, and a live broadcast are separate integration checks: a request to edit code does not authorize sending chat, changing scenes, starting output, or opening a new authorization flow. Use an already authorized live check when it is in scope; otherwise report the untested boundary.

For performance work measure frame time, allocation/resource growth, queue depth, event age, and network gaps independently. A smooth renderer cannot repair lost ingress events; faster transport cannot repair an unbounded texture cache. Prefer a scoped repair with before/after evidence over changing multiple stacks together.
