# The Coverage-Adaptive Safety Net

Caution before a refactor is not fixed policy. Gate it on how well-tested the _blast radius_ is, not on project-wide coverage. 90% overall can hide your target function at 0%; 30% overall can have it fully pinned by table-driven tests. Measure code you'll change, then pick tier.

## The Three Tiers

- **HIGH coverage on the blast radius (roughly ≥80% function coverage via `go tool cover -func`)** — refactor aggressively with tools; trust green bar.
  - Prefer gopls Rename/Inline/Extract, `eg`/`gofmt -r` for bulk mechanical changes, and generated `go/analysis` fixers over hand-edits.
  - Run fast net (build/vet/test) after each step. Escalate to `-race`/`-bench` only when step touches concurrency or hot path.
  - Larger steps OK: net catches regression within one test run, so mistakes are cheap and immediate.
- **MEDIUM coverage (~40-80%)** — harden blast radius before refactoring, not after.
  - First measure exactly what change touches: gopls references and call hierarchy give real call graph, not remembered one (see planning gate in [workflow.md](workflow.md)).
  - Add targeted table-driven or golden tests for exactly those paths, confirm they pass on current code, only then refactor.
  - Easy to skip; don't: re-run with `-coverprofile` and confirm new tests hit lines you'll change. Test importing right package but never reaching edited branch looks like a net, catches nothing. Once confirmed, same transforms as High tier allowed.
- **LOW/ZERO coverage (<40%, or specific touched lines uncovered even if package average looks fine) — Feathers mode** — write characterization (a.k.a. golden or pinning) tests _first_, recording what code does today, warts and all, before changing a single line.
  - Deliberately not correctness tests: they record current behavior rather than assert it is right, so refactor can be checked against it.
  - Find a seam (below); introduce minimum needed for testability.
  - Only safest tool-verified refactorings: gopls Rename and Inline, behavior-preserving by construction. Avoid Extract or any cross-package move until a real net exists.
  - Prefer Sprout/Wrap (see [catalog.md](catalog.md)): new behavior in new tested function, not edits to untested code in place.
  - Run `deadcode -test` first; worth two minutes. Some "untested code that needs a net" is exported API nothing calls; honest fix there is deletion, not testing.

**Diagnose:** 1- `go test -covermode=atomic -coverpkg=./... -coverprofile=cover.out ./...` — runs suite, writes coverage profile scoped to blast radius's packages 2- `go tool cover -func=cover.out` — ranks every function by coverage; check functions you'll touch, not package average 3- `go tool cover -html=cover.out` — red/green view of exact touched lines, for when `-func` percentage doesn't show which branches are green

Two caveats before trusting any number this produces:

- **Go's coverage is statement coverage, not branch coverage** — line in `if` block that ran once counts as fully covered even if `else` never ran, or `switch` only ever hit one `case`. Function at 100% can still hide untested branch. Percentage is floor on what's exercised, not proof logic is correct; read actual branches in code you'll touch.
- **`go test ./...` silently drops any package that has no `_test.go` file from the aggregate** — not counted as 0%, absent from report entirely, so untested package is invisible, not visibly red. `-coverpkg=./...` (as in Diagnose command above) forces every module package into profile, so silently-untested dependency can't slip past tier decision.

## Seams — What to Introduce When There's No Net Yet

- Seam, in Michael Feathers's sense: place where you can alter behavior without editing that exact spot.
- Seams let Feathers mode get a fake into a test without first doing the larger refactor the test protects against.
- Two seam types matter in Go:
  - **Object seam**: interface, or function-typed field or parameter, injected at construction; test passes fake implementation through it instead of real dependency. Most important in Go: interfaces are satisfied implicitly, so adding one at point of use touches only consumer, never producer package. Legacy code gains a seam without invasive edits to its dependencies.
  - **Link/build-tag seam**: swaps whole implementation at build time via `//go:build` constraints. Far rarer; mostly platform- or environment-specific substitutions where interface would be overkill.
- Enabling move for untested code with no seam yet: extract smallest possible interface (often one method) at exact call site where code depends on something external (database client, filesystem, clock). Inject concrete implementation via constructor parameter instead of constructing it inline.
  - One move, two wins: breaks potential import cycle between consumer and concrete type it depended on, and opens door for fake in characterization test. No producer-side change at all.

```go
// Before — no seam: NewReport constructs its own client, so a test
// exercising Generate has no way to substitute a fake and is stuck
// hitting a real database.
func NewReport(dsn string) *Report {
    db, _ := sql.Open("postgres", dsn)
    return &Report{db: db}
}

func (r *Report) Generate(ctx context.Context, id int) (Summary, error) {
    row := r.db.QueryRowContext(ctx, "SELECT ... WHERE id = $1", id)
    // ...
}

// After — a one-method interface extracted at the point of use;
// the concrete *sql.DB already satisfies it implicitly, so the
// producer package needs no change at all.
type rowQuerier interface {
    QueryRowContext(ctx context.Context, query string, args ...any) *sql.Row
}

func NewReport(db rowQuerier) *Report {
    return &Report{db: db}
}

func (r *Report) Generate(ctx context.Context, id int) (Summary, error) {
    row := r.db.QueryRowContext(ctx, "SELECT ... WHERE id = $1", id)
    // ... unchanged — a characterization test can now inject a fake rowQuerier
}
```

→ See `samber/cc-skills-golang@golang-design-patterns` skill for constructor and dependency-injection patterns this move builds on, and [catalog.md](catalog.md) in this skill for Sprout/Wrap mechanics that usually pair with a new seam.

## Verification Command Reference

Fast net from Core Loop in [SKILL.md](../SKILL.md), escalated only as far as change requires:

```bash
go build ./...                              # fastest gate — compile errors
go vet ./...                                 # correctness checks the compiler doesn't do
go test ./...                                # full test suite
go test -run TestName ./pkg/...              # target one test while iterating
go test -race ./...                          # concurrency changes — see samber/cc-skills-golang@golang-testing for race-detector and testing/synctest mechanics
go test -covermode=atomic -coverpkg=./... -coverprofile=cover.out ./...
go tool cover -func=cover.out                 # per-function and total coverage, ranked
go tool cover -html=cover.out                 # visual red/green source view
go test -bench=. -benchmem -count=10 > new.txt   # capture before AND after with the same command, then:
benchstat old.txt new.txt                     # `~` means no statistically significant difference — the desired result for a behavior-preserving refactor; anything else is a signal to stop and investigate, not noise to shrug off
```

## Cross-References

- → See `samber/cc-skills-golang@golang-testing` skill for test-writing craft, race-detector mechanics, and `testing/synctest`. Assumed baseline here; this file covers only when refactor's safety net needs them.
- → See `samber/cc-skills-golang@golang-benchmark` skill for interpreting `benchstat` delta and full profiling methodology.
- [workflow.md](workflow.md) — planning gate measuring blast radius these tiers are gated on, and human-checkpoint rule for touching untested code.
