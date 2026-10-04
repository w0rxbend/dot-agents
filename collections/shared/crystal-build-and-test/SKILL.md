---
name: crystal-build-and-test
description: Build, test, format or diagnose Crystal shards and small benchmark programs, and distinguish Crystal source projects from TypeScript Crystal-editor integrations and workstation toolchain scripts.
license: MIT
---

Start from the actual shard manifest, entrypoint, specs, CI and selected compiler. Record `crystal --version`, `shards --version`, executable paths and target architecture when diagnosing the environment. Historical metadata, a workstation snap, and CI are separate evidence; do not silently upgrade one to match another.

Read [references/project-scopes.md](references/project-scopes.md) for the portfolio's playground, editor extension and bootstrap boundaries. Read [references/commands-and-specs.md](references/commands-and-specs.md) for dependency/build/test selection. Preserve an existing application or library layout rather than recreating it with `crystal init`.

Trace what a source file does at top level before requiring it from a spec or running it. A benchmark entrypoint can execute lengthy measurements merely by being imported. Make reusable behavior independently requireable when that is needed; keep benchmark drivers and test initialization separate.

Choose a check that establishes the requested behavior: formatting checks source style, specs establish assertions, compilation establishes selected target compatibility, and a benchmark measures its configured workload. A placeholder spec or commented CI command is not evidence of meaningful coverage. Report the layer actually tested and missing tools separately.

For native or deployment work preserve supported system libraries, ABI and target platform. A successful local build does not establish portable static linking or another platform's runtime behavior. Changes to Crystal setup should follow the existing workstation installer workflow; a language-source edit does not require running a host bootstrap or installing a second global compiler.
