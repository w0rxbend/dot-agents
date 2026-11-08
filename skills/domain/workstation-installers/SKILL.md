---
name: workstation-installers
description: Maintain declarative workstation bootstrap, dotfile, font, and binary installers with faithful plans, artifact verification, resumable state, filesystem contracts, and native CLI parity. Use when changing Fluxion, binstaller, Dotbot ports, Nerd Fonts installers or a similar profile-driven installer.
license: MIT
---

# Declarative workstation installers

Before changing behavior, find actual frontend schema, parser ordering, planner, executor, state store and CLI/TUI adapters. Similar projects and ports deliberately differ in supported formats and features.

Read [planning-state.md](references/planning-state.md) for execution order, truthful dry runs, idempotence, persistence and port contracts. Read [artifact-filesystem.md](references/artifact-filesystem.md) for checksum trust, archive bounds, symlink ownership, staging, privilege and release validation.

Plan should list same operations executor will perform, without applying them. Installer change does not authorize running real apply workflow on developer's machine. Verify with isolated temporary roots, fake downloads/commands, parser/golden tests and native help/validate/dry-run smokes as applicable.

Preserve selected stacks and builds (reviewed: Go, Scala/Ox, Scala/ZIO, Java with declarative Mill, Crystal). Prefer Mill for new JVM build when left open; keep each existing repository's wrapper and schema.

Make success and resume evidence explicit. Return failure when verification or required operation fails. Never report partial install as unconditional success. Run current repository's relevant quality and behavior checks. Report real package-manager, sudo, network or hardware operations separately.
