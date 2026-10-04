---
name: workstation-installers
description: Maintain declarative workstation bootstrap, dotfile, font, and binary installers with faithful plans, artifact verification, resumable state, filesystem contracts, and native CLI parity.
license: MIT
---

# Declarative workstation installers

Use this for Fluxion, binstaller, Dotbot ports, Nerd Fonts installers, and comparable profile-driven tools. Identify the actual frontend schema, parser ordering, planner, executor, state store, and CLI/TUI adapters before changing behavior. Similar projects and ports intentionally have different supported formats and features.

Read [planning-state.md](references/planning-state.md) for execution order, truthful dry runs, idempotence, persistence, and port contracts. Read [artifact-filesystem.md](references/artifact-filesystem.md) for checksum trust, archive bounds, symlink ownership, staging, privilege, and release validation.

The plan should describe the same operations the executor will perform, without itself applying them. A change to the installer does not authorize running its real apply workflow on the developer's machine. Verify with isolated temporary roots, fake downloads/commands, parser/golden tests, and native help/validate/dry-run smokes as applicable.

Preserve selected implementation stacks and builds: reviewed variants include Go, Scala/Ox, Scala/ZIO, Java with declarative Mill, and Crystal. Prefer Mill for a new JVM build when left open, while retaining each existing repository's wrapper and schema.

Make success and resume evidence explicit. Return failure when verification or a required operation fails; never turn partial installation into an unconditional success line. Run the current repository's relevant quality and behavior checks, and report any real package-manager, sudo, network, or hardware operation separately.
