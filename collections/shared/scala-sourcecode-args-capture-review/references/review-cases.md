# Historical boundaries and review cases

Read this when a finding needs compiler-era context or a concrete regression specification. This is not an additional generic macro, compatibility or build skill.

## Evidence chain

| Record | Observation | What it does not establish |
|---|---|---|
| `e-api-2020` | Shared `Args` stores nested sequences of strict `Text` values. | A by-name macro entrypoint does not make the stored field lazy. |
| `e-args-broken-2022`, `e-args-oracle-2022` | Scala 3 reads optional initializer trees, substitutes `None`, and tests names only. | A successful test process would not validate values. |
| `e-args-fixed-2023`, `e-args-oracle-2023` | PR 126 references the parameter symbol and restores full equality. | Approval supplies no additional design reasoning; the mixed-clause case is unresolved. |
| `e103-erasure`, `e103-counterexample`, `e-casts-2024` | RC1 discussion names erased clause distinctions and a generic extension case; casts persist in a later snapshot. | Do not assert the same exact runtime error across all compiler representations, or claim a verified classifier patch. |
| `e-args-scala2-owner`, `e-args-scala2-emission` | Scala 2 chooses method/constructor symbols and emits nested values. | Do not copy Scala 3 tree operations into this branch. |
| `e154-runner`, `e-main-2024`, `e-tests-dispatch-2024`, `e-ci-2024` | Main-driven assertions are wired into `test.run`. | Wiring is not recorded execution. |

Full source citations, dates and attribution: [evidence.json](evidence.json).

## Consumer regression specification

Keep the parameter reference in the enclosing callable's scope. Invoke a debug/capture helper whose implicit `Args` materializes at the call site; materializing it inside a separately extracted helper can change the owner being inspected.

The 2023 `ArgsTests` source supplies these cases:

- A curried method has two ordered term groups.
- A local value block still captures the surrounding method arguments.
- A primary constructor captures both of its groups; a secondary constructor's later capture records that constructor's own parameters.
- A parameterless method records an empty outer sequence.
- An implicit parameter records the actual explicit or implicitly supplied value, not merely its name.

Extend that corpus with original probes, labelled unexecuted until run:

1. Invoke the same method with different values to distinguish runtime references from cached/default values. Do not use only literal `None` arguments: they would mask the historical fallback bug.
2. Compare `def f` and `def f()` under the chosen compiler. Establish whether its representation preserves an empty term clause; do not erase it as a side effect of filtering type clauses.
3. Define an extension block with a type parameter and an extension method with another type parameter. Materialize Args inside the method. Inspect that compiler's clause shape, identify expected receiver/term groups, and assert names/values only for actual term parameters. Decide the intended receiver exposure explicitly; the historical review supplies a counterexample, not a full expected payload.
4. Repeat the classifier check in constructor extraction. Fixing only the method branch leaves the sibling cast assumption intact.

The correction must distinguish type clauses without erased generic-list tests. On compiler releases with a dedicated term-clause API, verify its signature and empty-clause behavior before using it. On an older list-of-trees representation, inspect tree kinds and homogeneous-clause invariants; do not infer a kind from a nonexistent first element or silently flatten/filter away meaningful structure.

## Review attribution

Alexarchambault explains the erasure concern as PR 103's author. His historical commit/merge access is independently established by Li Haoyi's access grant in PR 56; that does not make this an independent design review. Smarter supplies the extension-method counterexample; historical repository-maintainer status is unverified. Li Haoyi explains his own submitted main-runner design in PR 154. PR 126's value-source repair is a source-derived lesson, not an inferred reviewer preference.

## Version and execution boundaries

Use `e-build-2023` for the repair's declared matrix and `e-build-2024`, `e-platforms-2024`, `e-mill-pin-2024` for the late snapshot. Calendar year alone does not select a compiler API. Shared runtime wrappers are distinct from compile-time reflection code; default-public implementation helpers are not automatically private API.

Inspect current checkout build/CI before running anything. For the exact late snapshot the test selector is `__.test.run`, and the observed assertion chain is Main → Tests.run → ArgsTests. A conventional framework selector can miss that chain. Publication success and binary-compatibility checks cannot replace a value-sensitive consumer. This candidate was authored without executing upstream Scala code; no supplied example is labelled compiled.
