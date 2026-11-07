---
name: rust-systems-contracts
description: Maintain Cargo workspace, ownership, error, UTF-8 and conditional unsafe-memory contracts in Rust libraries, CLI tools and the mixed-edition Rust learning playground.
license: MIT
---

# Rust systems contracts

Before picking commands or changing APIs, read workspace and affected member manifests, lockfile, toolchain/configuration, applicable instructions and tests. Classify code: learning exercise, reusable library, service or platform application. Keep each package's edition, minimum Rust version, resolver and feature/target contract. One 2024 member does not justify migrating every member or the workspace resolver.

Read [workspace-and-learning.md](references/workspace-and-learning.md) for package selection, mixed-edition playground, parsing/UTF-8/numeric exercises and meaningful targeted checks. Read [ownership-and-memory.md](references/ownership-and-memory.md) for borrowed versus owned interfaces, error propagation, allocation/performance claims and unsafe allocator changes. Allocator guidance applies when such code exists or is requested; inspected playground is ordinary standard-library learning code.

State changed invariant: who owns a value, how long a borrow stays valid, accepted inputs, how failures reach caller, observable behavior that must stay. Fix ownership structurally before adding clones, shared mutexes or unsafe pointers. Keep deliberately constrained kata inputs. Do not turn an educational example into service architecture or add dependencies solely to demonstrate a pattern.

Pick affected package and target first, then its tests, plus reverse dependents if public contract changed. Match existing warning/lint policy and feature combinations; blanket all-features or warnings-as-errors gates can exclude supported builds or block learning exercises. For unsafe or performance work, add relevant correctness/tooling/measurement check when available. Report what was actually verified. Check build does not prove executed tests, native portability, race freedom or allocator safety.
