---
name: rust-systems-contracts
description: Maintain Cargo workspace, ownership, error, UTF-8 and conditional unsafe-memory contracts in Rust libraries, CLI tools and the mixed-edition Rust learning playground.
license: MIT
---

# Rust systems contracts

Read the workspace and affected member manifests, lockfile, toolchain/configuration, applicable instructions and tests before choosing commands or changing APIs. Distinguish a learning exercise, reusable library, service and platform application. Preserve each package's edition, minimum Rust version, resolver and feature/target contract; one 2024 member does not authorize migrating every member or the workspace resolver.

Read [workspace-and-learning.md](references/workspace-and-learning.md) for package selection, the observed mixed-edition playground, parsing/UTF-8/numeric exercises and meaningful targeted checks. Read [ownership-and-memory.md](references/ownership-and-memory.md) for borrowed versus owned interfaces, error propagation, allocation/performance claims and unsafe allocator changes. Allocator guidance applies when such code is actually present or requested; the inspected playground contains ordinary standard-library learning code.

State the changed invariant: who owns a value, how long a borrow remains valid, which inputs are accepted, how failures reach the caller, and what observable behavior must remain. Resolve ownership structurally before adding clones, shared mutexes or unsafe pointers. Preserve deliberately constrained kata inputs; do not convert an educational example into a service architecture or add dependencies solely to demonstrate a pattern.

Choose the affected package and target first, then its tests and reverse dependents when the public contract changed. Match existing warning/lint policy and feature combinations; universal all-features or warnings-as-errors gates can exclude supported builds or obstruct learning exercises. For unsafe or performance work, add the relevant correctness/tooling/measurement check when available and report what was actually verified. A check build is not evidence of executed tests, native portability, race freedom or an allocator's safety.
