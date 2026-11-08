# Structural Constraints: Import Cycles, Package Boundaries, Type Moves, API Evolution

## Table of Contents

- [Breaking Import Cycles](#breaking-import-cycles)
  - [1. Consumer-side interface (dependency inversion)](#1-consumer-side-interface-dependency-inversion)
  - [2. Extract shared types to a new/lower package](#2-extract-shared-types-to-a-newlower-package)
  - [3. `internal/` packages](#3-internal-packages)
  - [4. Mediator/bridge package](#4-mediatorbridge-package)
- [Package Boundary Design](#package-boundary-design)
  - [Splitting a god package](#splitting-a-god-package)
- [Moving Types Across Packages: Type Aliases for Gradual Code Repair](#moving-types-across-packages-type-aliases-for-gradual-code-repair)
- [Exported API Surface and Versioning](#exported-api-surface-and-versioning)
- [`init()`, Global State, and Package-Level Vars as a Refactoring Target](#init-global-state-and-package-level-vars-as-a-refactoring-target)
- [Generics — When a Refactor Toward Them Is Warranted](#generics--when-a-refactor-toward-them-is-warranted)
- [Common Mistakes](#common-mistakes)
- [Cross-References](#cross-references)

## Breaking Import Cycles

- Go compiles packages leaf-to-root. To type-check `X`, compiler needs compiled type information of everything `X` imports, so it must finish those first.
- Import cycle (`X` imports `Y`, `Y` imports `X`, directly or transitively) has no valid compilation order, so `go build` rejects it outright as `import cycle not allowed`. Not style; no fallback exists.

Four strategies fix a cycle, in preference order:

| # | Strategy | Call-site cost | Best when |
| --- | --- | --- | --- |
| 1 | Consumer-side interface | None: no call-site changes anywhere | Consumer only calls one or two methods on producer's type |
| 2 | Extract shared type to a leaf package | Import path changes on both sides | Both packages truly need the _same concrete type_, not only its behavior |
| 3 | `internal/` package | Import path changes for shared code only | Shared code should never become public API |
| 4 | Mediator/bridge package | New package, both sides delegate to it | 1–3 don't fit the coupling |

### 1. Consumer-side interface (dependency inversion)

- If package `x` only _uses_ behavior from package `y` (calls a method or two on `y`'s concrete type, doesn't need the type itself), define small interface in `x` naming only those methods.
- Implicit interface satisfaction: `y`'s existing type already satisfies it, without `y` importing `x` or knowing the interface exists:

```go
// package x (consumer)
type Storer interface {
    Store(ctx context.Context, key string, val []byte) error
}

func Process(s Storer) error { /* uses s.Store, no import of package y */ }
```

```go
// package y — unchanged, already satisfies x.Storer implicitly
type Store struct{ /* ... */ }
func (s *Store) Store(ctx context.Context, key string, val []byte) error { /* ... */ }
```

- `x` stops importing `y`; `y` never imported `x`.

### 2. Extract shared types to a new/lower package

- Works because Go packages are flat within a module: nested subdirectory is still a distinct, independently importable package. Move types both `x` and `y` need into small new leaf package both import. Leaf imports neither, so cycle breaks by construction.
- Honest cost: real cycle can span five or more packages once every shared type is traced.

### 3. `internal/` packages

- Share code between related packages without widening public API.
- Code under an `internal/` directory is importable only by packages rooted at that `internal/` directory's parent. Siblings share implementation detail through it without joining module's public surface, and without pulling one sibling into the other.

### 4. Mediator/bridge package

- Last resort when 1–3 don't fit: new package holding shared functionality both `x` and `y` delegate to, absorbing coupling neither side wants.
- Use only after confirming consumer-side interface can't express the relationship. It usually can.

`internal/` layout for strategy 3: both `billing` and `shipping` can import `order/internal/model`, but nothing outside `order` tree can:

```
order/
├── billing/
│   └── billing.go        // imports order/internal/model
├── shipping/
│   └── shipping.go        // imports order/internal/model
└── internal/
    └── model/
        └── order.go        // shared type, invisible outside order/
```

## Package Boundary Design

- **Accept interfaces, return structs.**
  - Narrow interface parameter accepts the widest range of callers, including test fake implementing only the one or two methods called. Function never imports caller's concrete types.
  - Concrete struct return keeps full type information at call site, so _that_ caller's consumers can later define their own narrow interface. Producer never has to anticipate which subset future callers need.
- **Define interfaces where they are consumed, not where they are implemented.** Companion rule; this one actually prevents cycles, not only describes good taste.
  - Consumer declares interface naming only methods it calls. Producer never imports or knows it; satisfies it because Go interface satisfaction is structural.
- **Caveat: this is a heuristic, not dogma.**
  - Don't mechanically split every struct into interface-plus-implementation pair for being "more testable". Concrete struct reads simpler; interface with one implementation and no test-double need is pure indirection.
  - Don't return interface from constructor only because "it might be more flexible later". That flexibility has a name (YAGNI) and a cost (caller loses type information).
  - → See `samber/cc-skills-golang@golang-project-layout` skill for directory/package layout conventions this section assumes, and `samber/cc-skills-golang@golang-design-patterns` skill for judging when an interface is right call versus premature abstraction.

### Splitting a god package

- Before full split, gopls `refactor.extract.toNewFile` code action handles lighter case: move a top-level declaration to new file in _same_ package. Often enough to make bloated package navigable without touching its import graph.
- Experimental gopls `source.splitPackage` code action assigns top-level declarations to acyclic components as starting point for real split. Treat output as draft partition to review, not final answer: it can't know your domain boundaries.

## Moving Types Across Packages: Type Aliases for Gradual Code Repair

- Needed because Go ties type identity to fully-qualified name: `pkg2.T` differs from `pkg1.T` even with byte-for-byte identical underlying definitions.
- Neither assigns to nor substitutes for the other. Moved function can be re-exported as thin wrapper, moved variable/constant re-declared pointing at new location, but moved type had no way to migrate callers gradually.
- Before Go 1.9 this blocked large-scale refactors: moving a type meant one atomic commit touching every call site in module, with no intermediate state where both names worked.

Fix is `type A = B`: a **type alias**, not a new named type.

- `A` and `B` become the _same_ type, not merely convertible. Code using either name interoperates exactly: zero runtime cost, no wrapper function anywhere.
- Added to language specifically, per its design proposal, to "enable gradual code repair during large-scale refactorings, in particular moving a type from one package to another in such a way that code referring to the old name interoperates with code referring to the new name."

Migration recipe, as fixed sequence:

```go
// Step 1 — new package: introduce the real definition in its new home.
package newpkg

type NewName struct {
    // ... real fields
}
```

```go
// Step 2 — old package: replace the original declaration with an alias,
// and mark it deprecated so tooling and IDEs surface the migration.
package oldpkg

// Deprecated: use newpkg.NewName instead.
type OldName = newpkg.NewName
```

1. Introduce type in new home package with real definition.
2. In old package, replace original declaration with alias to new one; mark it `// Deprecated: use newpkg.NewName instead`, a doc comment tooling and editors recognize.
3. Migrate callers to new import path incrementally, one PR or one package at a time. Both names stay valid and interchangeable throughout: no flag day, no big-bang commit, no window with some callers broken while others are fixed.
4. Once nothing references old name, delete alias.

Go 1.24 extended type aliases to carry type parameters, so recipe applies unchanged to generic types.

## Exported API Surface and Versioning

- **Deprecate before deleting.** Tooling and IDEs flag doc comment beginning `// Deprecated: ...` at every call site (strikethrough or warning), giving callers time to migrate before symbol disappears. Deleting exported identifier outright breaks every downstream module at next `go build`, with no prior warning.
- **Prefer additive changes.** Go's compatibility promise sets default posture: additive changes (new function, new optional field, new method) over changing existing signature, since additive changes never break existing callers. Change that must break existing callers is not a minor version bump; it's a new major version.
- **Semantic import versioning** expresses that: v2+ module carries `/vN` suffix in both module path and every importer's import path (e.g. `example.com/mod/v2`).
  - v1 and v2 of same module coexist in one build: toolchain sees different packages with different import paths.
  - Callers migrate one package at a time, not all at once. Same gradual migration a type alias gives _within_ one version, applied _across_ major versions.
  - During transition, v2 can be thin wrapper over v1 (or vice versa, whichever side holds canonical logic), avoiding two divergent copies of same behavior.
- **`retract` directives** in `go.mod` mark already-shipped defective version as unfit for use. `go get` and `go list -m -u` show retraction to dependents, without deleting broken version from module proxy:

```
module example.com/mod

go 1.24

retract (
    v1.2.0 // published with a data-loss bug, see #123
    [v1.2.1, v1.2.3] // range retraction — a whole span of bad releases
)
```

## `init()`, Global State, and Package-Level Vars as a Refactoring Target

- `init()` ordering and mutable package-level state hide coupling. Caller can't see at call site that function depends on another package's `init()` having already run, or on a global variable unrelated code mutated earlier.
- Coupling absent from signature is absent from diff: exactly what makes code unsafe to move or test in isolation.
- Refactor toward explicit construction: constructor returning a struct, dependencies passed as parameters, not reached via package-level variable or `init()`-populated singleton.
  - Dependency remains; code still needs it. It becomes explicit, visible seam in function signature, not implicit one buried in package's `init()`.
  - → See `samber/cc-skills-golang@golang-design-patterns` skill for constructor and dependency-injection patterns, and [safety-net.md](safety-net.md) in this skill for how Feathers-style characterization test exploits this same seam to get coverage before risky change.

## Generics — When a Refactor Toward Them Is Warranted

- Introduce type parameter only when _logic_ is truly identical across types, not merely similar.
- _Behavior_ differing per type, even by one branch, means interface, not generic. Generic with type switch inside is usually a disguised interface.
- Litmus test: generic fits when type parameter would eliminate an existing type assertion and constraint stays narrow: `comparable`, `cmp.Ordered`, or small one-method interface.
- Write concrete version first. Refactor to generic only once duplication is real, already committed in two or more places, not anticipated for a third caller that may never arrive.
- As of this writing, Go has no method-level type parameters, which blocks fluent generic method chaining (`Map` returning differently-typed receiver). Plan around it up front, rather than discovering it mid-refactor.
- Verify like any other refactor, no special-casing: `go build ./... && go vet ./...` plus full test suite for touched packages.

## Common Mistakes

| Mistake | Fix | Why |
| --- | --- | --- |
| Moving type via `type OldName NewName` (new named type) instead of `type OldName = NewName` | Use `=`: real type alias | Without `=` this declares a _distinct_ type; existing old-type values no longer assign to new one, the exact break alias should avoid |
| Breaking cycle by moving _producer's_ concrete type into consumer's package | Define interface in consumer instead; leave producer's type in place | Usually only relocates cycle to whatever else producer's type depends on |
| Deleting exported symbol in same PR that deprecates it | Deprecate first, land, wait a release cycle, delete later | Callers outside module never saw deprecation notice before symbol vanished, so can't react |
| Bumping module to v2 without adding `/v2` to module path | Add `/v2` suffix to both `go.mod`'s `module` line and every import path | Without suffix, module resolution can't tell new major version from old; v1 importers silently get pulled onto breaking code on next `go get -u` |
| Reaching for generic when a second similar-looking function first appears | Wait for third real occurrence with identical logic, or existing type assertion generic would remove | Two occurrences are often coincidentally similar, not logically identical; premature generic ossifies abstraction around coincidence |

## Cross-References

- → See [catalog.md](catalog.md) in this skill for Fowler catalog entries (Extract Interface, Change Function Declaration, Move Function) these structural moves build on.
- → See [workflow.md](workflow.md) in this skill for staging cross-package move or package split as ordered sequence of small PRs.
