---
name: constraint-driven-development
description: Establishes a project's quality bar as a written contract and stops agents quietly lowering it. Interviews the user on which dimensions matter, supplies sane default thresholds when they have no number in mind, records everything in CONSTRAINTS.md, and watches the diff for a weakened bar — new @ts-ignore or eslint-disable suppressions, skipped or deleted tests, assertions stripped out, unimplemented stubs, thresholds edited down. Use when no quality bar is written down, when the user says "set up constraints" or "define our standards", when the user wants dimensions they care about — accessibility, web performance, coverage — set up as enforced constraints, when an agent keeps silencing checks or skipping tests to get to green, when you need a coverage or performance threshold and don't know what number to pick, or when an agent writes more code than anyone will read.
---

# Constraint-Driven Development

## Overview

Output: written record of **this project's** bar, with numbers, that outlives the conversation and can be checked mechanically. Checks must fire close enough to the work that the agent fixes its own output. Spec-driven development says what to build, test-driven proves it works; constraint-driven defines "good enough to ship" before anyone argues it in a pull request.

## When to Use

Apply when:

- New project or significant feature, no written quality bar
- User asks to "set up constraints", "add quality gates", "define our standards", or "stop the agent shipping junk"
- Agent produces volume nobody reads line by line
- CI has checks, but nobody knows which block merge and which are decoration
- Coverage, performance, or accessibility numbers argued per-PR instead of decided once
- Starting autonomous agent loop guarded from main only by a test suite the agent also wrote

**When NOT to use:**

- `CONSTRAINTS.md` exists and user isn't changing it — read and follow it
- One-off scripts, spikes, throwaway prototypes
- User wants code review now (`code-review-and-quality`) or CI pipeline built (`ci-cd-and-automation`)
- Pre-product-market-fit code expected to live two weeks — floor still worth it, rest isn't

## Loading Constraints

Interview needs live user. **Don't run it in non-interactive contexts** (CI, scheduled or looping agent runs, other autonomous runs). There, if constraints are missing: apply Floor below, note it, flag rest for a human.

## The Process

### Step 1: Detect before you ask

Never ask what you can read. Before first question, gather:

| What | Where to look |
|------|---------------|
| Language and stack | `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml` |
| Test runner | dev dependencies, `test` script, existing test files |
| Existing linters | `eslint.config.*`, `biome.json`, `.ruff.toml` |
| Coverage today | `coverage/` output, or run suite once |
| CI | `.github/workflows/`, `.gitlab-ci.yml` |
| Agent harness | `.claude/`, `.codex/`, `AGENTS.md` |

Report findings in two lines, then ask only what's left.

### Step 2: Four questions, each with a default

Use `interview-me` one-question-at-a-time discipline, with one change: every question has a default. "I don't know" is a complete answer that still yields working config.

```
Q1: Beyond the floor, which of these do you want enforced?
    (a) Test coverage on new code
    (b) Security scanning
    (c) Performance budgets
    (d) Accessibility
    (e) Architecture boundaries
GUESS: (a) and (b) — you have a test runner already and you're handling user input.
DEFAULT if unsure: (a) and (b).
Say what each pick costs: (c) and (d) need a running URL, (e) needs a rules file written.
```

```
Q2: When a check fails while the agent is mid-task, should it block or warn?
GUESS: Block. You're running agents unattended and a warning nobody reads is a warning.
DEFAULT if unsure: Block on the floor, warn on everything else for the first two weeks.
```

```
Q3: Do you have target numbers in mind, or should I measure where you are today and hold that line?
GUESS: Measure. Most teams don't have a number, and an invented one gets ignored.
DEFAULT if unsure: Measure and hold. See "Ratchets" below.
```

```
Q4: What's the slowest check you'll tolerate before the agent hands work back?
GUESS: About 90 seconds. Longer and you'll stop running it.
DEFAULT if unsure: 90 seconds at task end, unlimited in CI.
```

Stop at four.

### Step 3: Write CONSTRAINTS.md

One file at repo root.

```markdown
# Constraints

Last reviewed: 2026-08-08 by @addy

## Floor (always enforced, no setup required)

- No new suppression comments: `@ts-ignore`, `eslint-disable`, `# noqa`, `# type: ignore`
- No unimplemented stubs: `throw new Error("Not implemented")`, empty `catch {}`
- No skipped or deleted tests without a reason in the commit message
- No secrets in source
- This file does not get weakened to make a change pass

## Enforced with numbers

| Dimension | Rule | Checked by | Runs at |
|-----------|------|-----------|---------|
| Types | Zero type errors | `tsc --noEmit` | every edit |
| Lint | Zero errors from our config | `biome check` | every edit |
| Secrets | No secrets in source | `gitleaks dir --redact .` (gitleaks ≥ 8.19; older: `gitleaks detect --redact`) | every edit |
| Coverage | Changed lines ≥ 80% covered | `vitest run --coverage` + git diff | task end, CI |
| Security: code | No high findings | `semgrep scan --metrics=off --config p/default` | CI |
| Security: deps | Nothing at high or above | `osv-scanner scan source -r .` | CI |
| Accessibility | Zero critical or serious | `axe $PREVIEW_URL --tags wcag2a,wcag2aa,wcag21aa` | preview deploy |
| Performance | LCP ≤ 2500ms, CLS ≤ 0.1 | `lighthouse $PREVIEW_URL --output=json` | preview deploy |

Every row names the command that produces the verdict. A dimension with a
number and no command in this column is an aspiration, not a constraint.

## Measured, not yet enforced

| Metric | Today | Direction |
|--------|-------|-----------|
| Project coverage | 62.4% | must not fall |
| Bundle size (main) | 184 kB | must not grow |

## Exceptions

| ID | Rule | Path | Reason | Owner | Expires |
|----|------|------|--------|-------|---------|
| W1 | `no-explicit-any` | `src/legacy/**` | Rewrite tracked in ENG-441 | @addy | 2026-11-01 |
```

Then add one line to `AGENTS.md` and `CLAUDE.md`: `Read CONSTRAINTS.md before writing code. Do not weaken it to make a change pass.`

### Step 4: Install what each dimension needs

Each picked dimension needs an install. Don't write your own checker when a de facto one exists. Ecosystem targets these tools' rule formats and thresholds, so team's existing config keeps working.

| Dimension | Tool | Install | Run | Gate on |
|-----------|------|---------|-----|---------|
| Types (TS) | tsc | already there | `tsc --noEmit` | any error |
| Types (Python) | mypy | `pip install mypy` | `mypy .` | any error |
| Lint | your existing config | already there | `eslint .` / `biome check` / `ruff check` | any error |
| Coverage (JS) | your test runner | already there | `vitest run --coverage` (or `jest --coverage`) | changed-line coverage |
| Coverage (Python) | pytest-cov | `pip install pytest-cov` | `pytest --cov --cov-report=lcov` | same |
| Security: code | Semgrep | `pipx install semgrep` | `semgrep scan --metrics=off --config p/default --config p/owasp-top-ten` | any high finding |
| Security: secrets | gitleaks | `brew install gitleaks` | `gitleaks dir --redact --no-banner .` (≥ 8.19; `gitleaks git` scans history) | any finding |
| Security: dependencies | osv-scanner | `brew install osv-scanner` | `osv-scanner scan source -r .` | high or above |
| Performance: page | Lighthouse | `npm i -D lighthouse` | `lighthouse $URL --output=json --quiet` | LCP, CLS, performance score |
| Performance: bundle | size-limit | `npm i -D size-limit` | `size-limit --json` | per-entry byte budget |
| Accessibility | axe-core | `npm i -D @axe-core/cli` | `axe $URL --tags wcag2a,wcag2aa,wcag21aa` | zero critical or serious |
| Architecture | dependency-cruiser | `npm i -D dependency-cruiser` | `depcruise --validate src` | any violation |
| Assertion quality | Stryker | `npm i -D @stryker-mutator/core` | `stryker run --mutate <changed files>` | mutation score |

Five things that bite if skipped:

1. **`--redact` on gitleaks is not optional.** Without it, matched secret lands in agent transcript, then a log, summary, or commit message. Report rule and location, never value.
2. **Lighthouse and axe need a URL.** They work only against a running app, so they belong in runtime stage, against preview deploy or local server started first. No URL (CLI, library, desktop app)? Say so, drop the dimension. Don't invent a check that can't run.
3. **Scope the expensive ones to the diff.** `stryker run --mutate` on whole repo takes hours and gets turned off; on touched files, under a minute. Same for Semgrep, which takes a path list.
4. **Coverage needs no second test run.** Intersect lcov the suite already writes with `git diff`.
5. **Semgrep's registry rules are free to run; check the licence before redistributing them.** `opengrep` is a drop-in fork, same rule format and JSON output, if legal team cares. Keep `--metrics=off`: registry configs otherwise send usage metrics to Semgrep. Never `--config auto` (requires metrics).

Add each to project's own script, reproducible without an agent:

```json
{
  "scripts": {
    "check:fast": "tsc --noEmit && eslint . && gitleaks dir --redact --no-banner .",
    "check:task": "npm run check:fast && vitest run --coverage",
    "check:full": "npm run check:task && semgrep scan --metrics=off --config p/default && osv-scanner scan source -r ."
  }
}
```

`check:fast` runs after an edit, `check:task` when agent thinks it's done, `check:full` in CI.

Commands live in two places: `Checked by` column in `CONSTRAINTS.md`, and these scripts. `CONSTRAINTS.md` is canonical. Scripts are wrappers that must mirror it, not a second source of truth. On drift, file wins.

### Step 5: Wire it to the lifecycle

Biggest mistake: running everything everywhere. Check that stalls agent gets switched off.

| Phase | Where it runs | What runs | Budget |
|-------|---------------|-----------|--------|
| BUILD | After each edit (editor/agent hook or build script) | Types, lint, secrets, floor | under 5s, changed file only |
| VERIFY | Project's test command | Related tests, changed-line coverage | under 90s |
| REVIEW | Before opening or merging a PR | Everything, plus guards below | minutes |
| SHIP | CI on merge target | Direction checks, no regressions | CI |

Two rules keep this tolerable:

1. **Scope to the diff.** Check lines this change touched, not whole repo. Agent can move changed-line coverage; project coverage is inherited.
2. **Cost decides placement.** Anything over a few seconds leaves the edit loop.

### Step 6: Guard the bar itself

Agents don't craft clever loopholes. They hit red check, take cheapest road to green. At review, watch diff for five moves:

1. **The threshold moved.** Budget lowered, severity dropped, check removed from fast stage. Compare `CONSTRAINTS.md` with its branch-point state.
2. **A test got easier.** `.skip` added, test file deleted, assertions pulled from tests that stayed.
3. **A checker got silenced.** New `@ts-ignore` or `eslint-disable`. Four suppressions need special attention, since each switches off a check you rely on: `istanbul ignore` drops code from coverage instead of testing it, `Stryker disable` hides a surviving mutant, `nosemgrep` and `gitleaks:allow` hide security findings.
4. **Work is unfinished.** Stub that throws, empty `catch` turning failure into silence, `TODO` in place of implementation.
5. **An exception appeared.** New Exceptions row nobody discussed.

Needs no tooling beyond `git diff`. Tightening the bar should be silent; loosening, loud.

Unlike numbered dimensions, floor has no de facto tool. Reference implementation of these five checks ships in [references/floor-guard.md](references/floor-guard.md) (diff-scoped, exit `0`/`1`/`2`, patterns adaptable per ecosystem). Adapt it, don't reinvent.

**Not all checks are equally circular.** Rank by one question: can agent make it pass with code that doesn't work?

- **External** — axe-core encodes WCAG, `osv-scanner` reads a vulnerability database, Lighthouse measures a real browser. Agent can't argue with these.
- **Project** — your lint rules, layer boundaries. Human owns the file.
- **Suite** — your own tests. Most useful, only genuinely circular one.

Ensure at least one external constraint.

### Step 7: Ratchets, when you don't have a number

Record where you are, refuse to get worse. Put today's number and a direction in "Measured, not yet enforced" table. Checks compare against recorded value, not an aspiration. Number improves: update it. Number drops: that's the finding.

## Sane Defaults

No user opinion? Use these. Most codebases meet them day one.

| Constraint | Default | Why this number |
|------------|---------|-----------------|
| Coverage of changed lines | ≥ 80% | Forces a test, still allows a config line |
| Project coverage | today's value, must not fall | Adopts with no argument |
| Mutation score (if used) | ≥ 60% to start | Typical for never-mutated suite; 80% is mature |
| Dependency vulnerabilities | nothing at high or above | Below that mostly noise |
| LCP | ≤ 2500 ms | Core Web Vitals "good" threshold |
| CLS | ≤ 0.1 | Same |
| Accessibility | zero critical or serious axe violations | Moderate and minor often debatable |
| Exception lifetime | 90 days | Long enough to plan fix, short enough to remember |
| Ratchet tolerance | 0.5% | Absorbs drift when unrelated file moves the number |

State number and reason together. Threshold without rationale gets deleted by next person who hits it.

## Escalation Path

Three levels of teeth. Start at first.

1. **Written only.** `CONSTRAINTS.md` exists, agents read it. Free, catches honest mistakes, relies on agent compliance.
2. **Scripted.** `npm run check` (or `make check`) runs fast checks, wired into agent post-edit hook and CI. Deterministic, no new dependency.
3. **Tool-backed.** Dedicated runner for diff scoping, budgets, ratchets, guard checks. Use when config outgrows a shell script. Floor-guard reference in [references/floor-guard.md](references/floor-guard.md) is the starting point for the guard-checks half.

Most projects should stop at 2. Move to 3 past about thirty lines of check-running shell.

**A first run can be floor-only.** Floor guard is diff-only, needs no installs. Enforce floor day one; add numbered dimensions as each tool gets installed. Machine-wide security tools (gitleaks, osv-scanner) can run CI-only to keep laptops clean. Declare where each dimension runs in `Runs at` column.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "We'll add constraints once the code settles" | Code settles around whatever was allowed while it moved |
| "The tests are the constraints" | Your own tests prove you agree with yourself; they say nothing about new-code coverage, dependency risk, or bundle growth |
| "We can't hit 80% coverage" | Then don't set 80%. Set today's number and hold it |
| "This will slow the agent down" | Only if slow checks sit in fast loop. Placement error, not argument against constraints |
| "I'll remember what our standards are" | Agent won't, and it writes most of the code |
| "Constraints will block us shipping" | Exception with owner and date unblocks you. Deleting the constraint unblocks everyone forever |

## Red Flags

Stop and reconsider if:

- Interview passed four questions, or produced config user can't explain
- Budget set that codebase fails today, with no plan to reach it
- Dimension in CONSTRAINTS.md with a number but no tool behind it
- Hand-rolled checker where de facto one exists, ignoring team's existing config
- Every constraint checked by project's own test suite, no external opinion
- `CONSTRAINTS.md` changed in same commit as the failing feature
- Exception with no owner, or expiry over a year out
- Agent proposed relaxing a threshold instead of fixing code
- Slow checks in edit loop, and someone started passing `--no-verify`
- Nobody opened `CONSTRAINTS.md` since it was written

## Verification

Skill applied correctly when:

- [ ] `CONSTRAINTS.md` exists; every number has stated reason
- [ ] Floor enforced, passes on current codebase without changes
- [ ] Each picked dimension has installed tool and command that runs today
- [ ] Each constraint says where it runs; fast stage stays under a few seconds
- [ ] At least one constraint external (not judged by project's own tests)
- [ ] Measured-only metrics record today's value and direction
- [ ] Exceptions have owner and expiry date
- [ ] `AGENTS.md` or `CLAUDE.md` points at the file
- [ ] Trial run on current branch: no failures user disagrees with

## See Also

- `interview-me` — one-question-at-a-time discipline the intake borrows
- `code-review-and-quality` — how to review; this skill decides what review enforces
- `ci-cd-and-automation` — builds pipeline these constraints run in
- `test-driven-development` — suite that coverage and mutation constraints measure
- `security-and-hardening` — what security dimension should contain
- `performance-optimization` — source of performance numbers
