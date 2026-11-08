---
name: crystal-build-and-test
description: Build, test, format or diagnose Crystal shards and small benchmark programs, and distinguish Crystal source projects from TypeScript Crystal-editor integrations and workstation toolchain scripts.
license: MIT
---

Start from actual shard manifest, entrypoint, specs, CI and selected compiler. Diagnosing environment: record `crystal --version`, `shards --version`, executable paths and target architecture. Historical metadata, workstation snap and CI are separate evidence; do not silently upgrade one to match another.

Read [references/project-scopes.md](references/project-scopes.md) for portfolio's playground, editor extension and bootstrap boundaries. Read [references/commands-and-specs.md](references/commands-and-specs.md) for dependency/build/test selection. Keep existing application or library layout; do not recreate it with `crystal init`.

Before requiring source file from spec or running it, trace its top-level behavior. Importing benchmark entrypoint alone can execute lengthy measurements. Make reusable behavior independently requireable when needed; keep benchmark drivers and test initialization separate.

Pick check proving requested behavior: formatting proves source style, specs prove assertions, compilation proves selected target compatibility, benchmark measures its configured workload. Placeholder spec or commented CI command does not prove meaningful coverage. Report layer actually tested and missing tools separately.

For native or deployment work, preserve supported system libraries, ABI and target platform. Local build success does not prove portable static linking or another platform's runtime behavior. Change Crystal setup through existing workstation installer workflow. Language-source edit needs no host bootstrap run or second global compiler install.
