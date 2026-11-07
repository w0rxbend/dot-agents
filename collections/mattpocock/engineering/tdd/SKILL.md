---
name: tdd
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
---

# Test-Driven Development

TDD is the red → green loop. Every section applies every cycle. Consult before and during loop, not after.

Exploring codebase: read `GLOSSARY.md` (if it exists) so test names and interface vocabulary match project domain language. Respect ADRs in area you touch.

## What a good test is

Test behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. Good test reads like spec: "user can checkout with valid cart" names exact capability.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

**Seam**: public boundary you test at. Observe behavior there without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before any test, list seams under test and confirm with user. No test at unconfirmed seam. Can't test everything; agreed seams focus effort on critical paths and complex logic, not every edge case.

Ask: "What's the public interface, and which seams should we test?" Give each proposed seam one-line note: what it catches, what it misses.

Interface shape itself in question (module depth, where seam belongs, what interface exposes)? Call Skill tool with "codebase-design" for vocabulary. It is shared source of module, interface, depth, seam, adapter, leverage and locality terms. Reference to consult, not session to run.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through side channel (querying database instead of using interface). Tell: test breaks on refactor while behavior unchanged.
- **Tautological**: assertion recomputes expected value same way code does (`expect(add(a, b)).toBe(a + b)`, hand-derived snapshot done same way, constant asserted equal to itself). Passes by construction; never disagrees with code. Expected values must come from independent source of truth: known-good literal, worked example, spec.
- **Horizontal slicing**: all tests first, then all implementation. Bulk tests verify _imagined_ behavior: _shape_ of things, not user-facing behavior. They go insensitive to real changes and lock test structure before you understand implementation. Use **vertical slices** instead: one test → one implementation → repeat. Each test is a **tracer bullet**, shaped by what last cycle taught.

## Rules of the loop

- **Red before green.** Failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** Belongs to review stage (`mattpocock--code-review` skill), not red → green implementation cycle.
