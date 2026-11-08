# Refactoring Workflow — Plan, Stage, Land

Optional multi-PR strategy for large refactor with explicit human checkpoints. Focused local refactor can keep same safety-net/order invariants without integration branches, published PRs, or new approval per step. Use requested repository workflow and existing authorization.

## Table of Contents

- [1. The Planning Gate (mandatory, before any edit)](#1-the-planning-gate-mandatory-before-any-edit)
- [2. Three Interacting Orderings](#2-three-interacting-orderings)
  - [Parallel vs. sequential — decision checklist](#parallel-vs-sequential--decision-checklist)
- [3. The Git Model](#3-the-git-model)
- [4. Parallel vs. Sequential Execution](#4-parallel-vs-sequential-execution)
- [5. The `// REFACTOR(step N): ...` Marker Convention](#5-the--refactorstep-n--marker-convention)
- [6. Workflows (`ultracode`) vs. Human-in-the-Loop](#6-workflows-ultracode-vs-human-in-the-loop)
- [7. Human Checkpoints](#7-human-checkpoints)
- [Cross-References](#cross-references)

## 1. The Planning Gate (mandatory, before any edit)

**Thinking mode:** reason as thoroughly as possible; on Claude Code, use `ultrathink` for explicit extended thinking. Bad ordering does not look wrong in plan. It surfaces later as broken build or conflict-riddled merge, with several PRs in flight.

- Before touching any code, map blast radius with gopls:
  - find every reference to symbols you intend to change
  - walk call hierarchy both directions
  - check package's exported API surface for anything external module might depend on
- Workspace symbol search and `gopls codeaction` show mechanical options per site. `samber/cc-skills-golang@golang-gopls` skill owns day-to-day mechanics (rename, browsing references, call hierarchy).

Turn blast radius into **refactoring inventory**, one row per atomic change, so whole refactor is one artifact before any PR exists:

| Transform | Files / callers touched | Risk | S/B |
| --- | --- | --- | --- |
| Extract `validateOrder` from `ProcessOrder` | `internal/orders/process.go` (1 file, no external callers) | Low | S |
| Rename `Client.Send` → `Client.Publish` | `pkg/client/*.go`, 14 call sites across 3 packages | Low | S |
| Break import cycle `billing` ↔ `orders` via consumer-side interface | `internal/billing/service.go`, `internal/orders/service.go` | High | S |
| Move `Invoice` type to `pkg/billing`, alias from old location | `internal/orders/invoice.go` → `pkg/billing/invoice.go`, ~9 call sites | High | S |
| Replace `Invoice.Total`'s O(n²) discount-lookup loop with a map lookup | `pkg/billing/invoice.go` | Medium | S |
| Switch `Invoice.Total` computation to Decimal instead of float64 | `pkg/billing/invoice.go` and its tests | Medium | B |

- Risk tiers match Risk Stratification table in `SKILL.md` (Low/Medium/High).
- **S/B** marks each row Structural (changes code shape, not observable behavior) or Behavioral (changes what code does), in Kent Beck's sense.
- **Never let one PR carry both letters.** Rename and bug fix in same function: two rows, two PRs, two review postures.
- One concern per row holds within one letter too:
  - move and loop-optimization rows above are both S, yet still two rows and two sequential PRs
  - move needs gopls plus green build/test. Optimization needs benchmarks (→ See `samber/cc-skills-golang@golang-benchmark` skill) and closer read for subtle correctness changes
  - both touch same file, so Ordering (b) sequences them anyway. Never split move-then-optimize pair across parallel worktrees
- Inventory is the object every later ordering decision is computed from, and what you show human for sign-off.

For large staged refactor, make inventory reviewable before dependent edits. Reuse plan or direction user already authorized. Ask when direction adds unresolved product/API decision or expands requested scope; ordinary reversible work inside chosen plan continues.

## 2. Three Interacting Orderings

After inventory approval, three independent orderings combine into final sequence. Plan that gets one right but ignores others still fails.

| Ordering | Question it answers | Why it matters |
| --- | --- | --- |
| **(a) Beck ordering** | Within dependency chain, structure or behavior? | Structural first, behavioral last. `git blame` stays meaningful: last change on a line is what future reader needs, not passing rename. Reviewers wear one hat: structural PR gets fast, low-scrutiny pass (is this reversible? did tests stay green?); behavioral PR gets full scrutiny (does this do the right thing?). Mixing forces both postures on every PR. |
| **(b) Conflict-avoidance ordering** | Do two rows share files or symbols/callers? | Such PRs must land sequentially (one merges to refactoring branch before next starts), else second PR rebases against moving target for whole review cycle. File-disjoint PRs can run in parallel worktrees at no coordination cost. |
| **(c) Dependency ordering** | Does row need structural groundwork from another row first? | Breaking import cycle, extracting shared package, or adding type alias for cross-package move are prerequisites, not peers: cannot move function into package still forming cycle. Land them before anything assuming groundwork. |

- **Workspace-wide gopls rename is a barrier.**
  - It rewrites every reference tree-wide, so it may touch any in-flight change's files. File-disjointness cannot be known in advance.
  - Schedule it alone: land every other ready PR first, or hold every other PR until it lands.
  - Never run tree-wide rename concurrently with anything else, even change that looks unrelated.

### Parallel vs. sequential — decision checklist

Run for every row pair considered for concurrent execution:

| Question | If yes |
| --- | --- |
| Do two changes touch same file? | Sequential |
| Do they touch same symbol, or do one's callers overlap other's? | Sequential |
| Does one depend on structural groundwork the other lands (cycle break, extracted package, alias)? | Sequential — groundwork first |
| Is either change a workspace-wide rename? | Sequential — rename runs alone |
| None of the above | Safe to parallelize in separate worktrees |

Any yes: sequential. Concurrent only when every answer is no.

## 3. The Git Model

- Deliberate, explicit choice for staged refactors; not the only way to refactor, nor how every Go team works day to day.
- Many teams land small, independent PRs straight on fast-moving trunk, each shippable alone; works when changes are truly independent.
- _Staged_ refactor is one coherent transformation split into reviewable steps, not independent changes. It needs place to accumulate before reaching `main`.
- Tradeoff: reviewability and human checkpoint on every step, at cost of extra integration branch and final merge step.

The shape:

1. Create long-lived `refactor/<topic>` branch off `main`. Seed it with `// REFACTOR(step N): ...` markers for plan itself (see Step 5).
2. For each inventory change, in Step 2 order, execute inline or, if authorized and available, dispatch to agent with isolated edit ownership. Sub-agent, scoped to fresh worktree, does the work:
   - Enter fresh, isolated worktree.
   - Branch for that one change off current tip of `refactor/<topic>`.
   - Apply that change, nothing else. Row growing past **~100–500 lines** signals it is actually two rows: split it before diff outgrows one review sitting.
   - Verify: `go build ./... && go vet ./... && go test ./...` (add `-race` or `benchstat`-backed `-bench` per Risk Stratification table in `SKILL.md`).
     - Many sequential PRs: weigh actual CI duration against refactor pace. Few minutes rarely worth front-loading; much longer pipelines across many PRs add up fast. If CI waits would meaningfully stall sequence, run same checks locally first, with CI as final confirmation, not primary feedback loop.
     - If CI is already fast, no need to duplicate it locally.
   - Open **PR targeting refactoring branch**, not `main`. Ready for review, not draft: staging exists for prompt human review and merge:

     ```bash
     GH_TELEMETRY=false gh pr create --base refactor/<topic> --title "..." --body "..."
     ```

   - Have sub-agent report short result (pass/fail, verification output, PR link). Keep that in orchestrating context, not sub-agent's full transcript.
3. Human reviews and merges each small PR into `refactor/<topic>` at own pace.
   - For PR changing code logic, not just shape, load `samber/cc-skills-golang@golang-security` (and `golang-safety` for internal-correctness risk) with this skill before approving.
4. Only once every row has landed on `refactor/<topic>` and Step 5 TODO-marker sweep is clean, open **final PR** merging `refactor/<topic>` into `main`, **as a draft**. Unlike intermediate PRs, it is whole transformation and deserves slower final look before marked ready.

**Never merge an intermediate PR directly to `main`.** Refactoring branch is integration point for whole refactor; `main` only sees completed transformation, in one final merge. Intermediate PR on `main` exposes deliberately incomplete state (aliases still in place, shims not yet removed) to every branch built off `main` meanwhile.

## 4. Parallel vs. Sequential Execution

- Launch ready rows (dependency prerequisites landed, Step 2 checklist "no" on every question) concurrently: one sub-agent per row, each with own worktree, branch off current tip of `refactor/<topic>`, and PR.
- Run overlapping rows (same file, same symbol, or dependency) one at a time: land first on `refactor/<topic>`, then branch second off new tip.
- Step 2 rename-barrier rule applies here without exception: never schedule tree-wide rename alongside any other in-flight worktree, however unrelated files look.

## 5. The `// REFACTOR(step N): ...` Marker Convention

Marker has two jobs; first matters more than it looks.

- **Job 1 — surviving context loss.** Multi-step refactor eats context fast:
  - it can span many sessions; each new session or agent starts with fresh, limited context and no memory of planning conversation
  - conversation is bad place to keep plan safe; codebase, committed to refactoring branch, is not
  - so when creating `refactor/<topic>` (Step 3), before any change lands, seed markers liberally wherever inventory shows future work, idea worth not losing, or decision not obvious from later diff. Not only at deliberate imperfection
  - **Skip this for a small refactoring.** Single-PR change or Section 6 mechanical sweep has no plan worth losing; markers there are noise, not insurance. Reserve liberal seeding for staged, multi-PR refactors whose plan is too large for one session's memory.
- **Job 2 — flagging deliberate imperfection.** Staged refactor by design passes through intentionally imperfect states: type alias kept so callers migrate one PR at a time, shim left until later step removes it, old code path reachable until last caller is gone.
  - **This is fine and expected.** Risk is not imperfection but forgetting it after its PR merges.

Mark every such spot (plan note or deliberate imperfection) with comment naming step and reason:

```go
// REFACTOR(step 3): remove this alias once all callers in pkg/foo migrate to bar.New (see refactor/<topic>)
```

**Final sweep**, right before opening PR that merges `refactor/<topic>` into `main`, must find zero markers:

```bash
grep -rn "REFACTOR(" .
```

**Diagnose:** `grep -rn "REFACTOR(" .` must return no results before final merge to `main`. Any hit means planned step never landed; refactor is not done, even if every PR merged cleanly.

## 6. Workflows (`ultracode`) vs. Human-in-the-Loop

- Claude Code's Workflow feature (`ultracode`) orchestrates sub-agents across stages automatically, with no human checkpoint between them.
- Wrong shape for staged refactor, whose whole value is human reviewing and merging each PR _before_ next step builds on it.
- Use Workflows/`ultracode` only for truly **single mechanical sweep in one pass**: one `gofmt -r` rule, one `eg` template, or one `modernize`-style fixer applied tree-wide, green on build/vet/test, nothing else in inventory depending on it.
- For progressive review across multiple merges (usual real refactor), use worktree + PR + human-review flow from Steps 3 and 4, not Workflows.

## 7. Human Checkpoints

Preserve explicitly requested human checkpoints for this staged strategy. Cross-package moves, public API changes, deletion, and toolchain changes need review proportional to impact; reuse authorization for items already in plan. Ask again only when new evidence materially changes scope or compatibility. For untested code, establish and inspect [characterization-test baseline](safety-net.md) before relying on it.

Structural-only PRs are reversible and low-risk by construction (thanks to Beck's separation) and can be fast-reviewed. Behavioral PRs (anything changing what code does, not just its shape) get full scrutiny every time, however small diff looks.

## Cross-References

- [catalog.md](catalog.md) — Fowler refactoring catalog mapped to Go: code-smell trigger, mechanics, tool, risk per entry.
- [go-tooling.md](go-tooling.md) — gopls code actions, CLI invocation, `gofmt -r`, `eg`, `gopatch`, `go/analysis` fixers used in inventory examples.
- [safety-net.md](safety-net.md) — coverage-adaptive strategy and characterization-testing recipes cited in Human Checkpoints.
- [structural.md](structural.md) — import-cycle breaking, package-boundary design, type-alias gradual-repair mechanism from inventory example.
- → See `samber/cc-skills-golang@golang-security` skill (and `golang-safety`) for reviewing PRs that change code logic, per Step 3.
