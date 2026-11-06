---
name: cpp-obs-plugin-development
description: Modify C++/Qt OBS plugins and the obs-aitum-multistream fork while preserving libobs reference lifetimes, frontend callback/thread ownership, CMake dependency contracts and plugin packaging.
license: MIT
---

# C++ OBS plugin development

Identify plugin fork, target OBS build, Qt family and supported platforms before changing C++ or CMake. In-process libobs/frontend plugin: WebSocket client rules do not define its ownership or callback API. Keep upstream structure and local changes unless asked to migrate.

Read [build-contracts.md](references/build-contracts.md) for in-tree/out-of-tree linkage, dependency bundles and artifacts. Read [output-lifecycle.md](references/output-lifecycle.md) for OBS references, Qt thread handoff, asynchronous stop/unload and settings.

Trace each output operation: configuration, creation, start/stop callback, teardown. Pick checks proving the changed contract, including plugin load in supported OBS runtime when available. Report configure/build/package success apart from runtime smoke. Do not start public streams or modify user's real OBS profile for validation.
