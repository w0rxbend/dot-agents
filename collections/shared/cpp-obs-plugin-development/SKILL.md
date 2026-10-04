---
name: cpp-obs-plugin-development
description: Modify C++/Qt OBS plugins and the obs-aitum-multistream fork while preserving libobs reference lifetimes, frontend callback/thread ownership, CMake dependency contracts and plugin packaging.
license: MIT
---

# C++ OBS plugin development

Identify the plugin fork, targeted OBS build, Qt family and supported platforms before changing C++ or CMake. This is an in-process libobs/frontend plugin; WebSocket client rules do not define its ownership or callback API. Preserve upstream structure and local changes unless a migration is requested.

Read [build-contracts.md](references/build-contracts.md) for in-tree/out-of-tree linkage, dependency bundles and artifacts. Read [output-lifecycle.md](references/output-lifecycle.md) for OBS references, Qt thread handoff, asynchronous stop/unload and settings.

Trace each output operation from configuration through creation, start/stop callback and teardown. Choose checks that establish the changed contract, including plugin loading in the supported OBS runtime when available. Separate configure/build/package success from runtime smoke; do not start public streams or modify the user's real OBS profile to validate development changes.
