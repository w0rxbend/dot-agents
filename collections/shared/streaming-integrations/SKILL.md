---
name: streaming-integrations
description: Implement or debug OBS WebSocket v5 clients, Twitch OAuth/EventSub delivery, and event-driven OBS browser-source overlays, preserving session correlation and render-resource lifetimes. Use when working on OBS control, Twitch event ingestion or stream overlay code.
license: MIT
---

# Streaming integrations

Work from checked-out protocol code, lockfiles and tests. In this portfolio these are separate boundaries: OBS control clients, Twitch ingestion, backend-to-overlay WebSocket, browser rendering. Find failing boundary before changing another. Keep repository's language, effect system, UI stack and public contract.

## Select the boundary

- OBS connection, authentication, requests, batching or reconnect: read [references/obs-session.md](references/obs-session.md).
- Twitch first-run authorization, token refresh, permissions or EventSub delivery: read [references/twitch-events.md](references/twitch-events.md).
- Pixi overlays, media assets, browser-source visibility or rendering leaks: read [references/browser-sources.md](references/browser-sources.md).

Trace one input: transport message → validated domain event → queue/session state → user-visible output. Parse and normalize compatibility aliases at boundary; scenes receive normalized events, not wire aliases. New event: check backend serialization and every consuming scene, including unknown-event fallback.

Protocol work: recorded fixtures, fake transports. Reconnect, timeout, slow-consumer and teardown failures need deterministic tests of completion, cancellation, bounded resource use and duplicate handling. Real OBS, Twitch accounts and live broadcast are separate integration checks. Code-edit request does not authorize sending chat, changing scenes, starting output or opening new authorization flow. Use already authorized live check if in scope; otherwise report untested boundary.

Performance: measure frame time, allocation/resource growth, queue depth, event age and network gaps independently. Smooth renderer cannot repair lost ingress events; faster transport cannot repair unbounded texture cache. Prefer one scoped repair with before/after evidence over multi-stack changes.
