---
name: zig-build-and-memory
description: Maintain version-sensitive Zig build graphs, allocator ownership, buffered I/O, tests and fuzz targets, especially zig-playground's Zig 0.15.2 minimum API contract.
license: MIT
---

# Zig build and memory contracts

Read build.zig.zon and build.zig before selecting snippets or commands. Confirm the actual compiler version and supported floor; a minimum of 0.15.2 is not an exact compiler pin or proof that every future standard library is compatible. Preserve module names, package fingerprint and dependency hashes unless deliberately changing package identity or dependencies.

Read [build-memory-io.md](references/build-memory-io.md) for the repository's module/test graph, unmanaged containers, allocation failure, writer flush and fuzz semantics. Match official documentation and std source to the compiler being used.

For a change, state who owns allocated bytes and when slices become invalid. Run the relevant module and executable tests through the existing build graph, then format/build checks appropriate to the change. Keep deterministic regression results, fuzz duration/corpus findings and cross-target compile results distinct.
