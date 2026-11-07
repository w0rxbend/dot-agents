---
name: simplify-code
description: "Parallel 4-agent cleanup of recent code changes (reuse, quality, efficiency, altitude). Use when the user asks to simplify or clean up their changes; not a bug hunt or general code review."
version: 1.1.0
author: Hermes Agent (inspired by Claude Code /simplify)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, cleanup, refactor, delegation, subagent, parallel, simplify]
    related_skills: [requesting-code-review, test-driven-development]
---

# Simplify Code — Parallel Review & Cleanup

**Cleanup pass, not bug hunt.** Improve working code: remove duplication, flatten needless complexity, cut waste, deepen band-aid fixes.

## When to Use

Trigger when user says any of:

- "simplify" / "simplify my changes" / "simplify these changes"
- "clean up my changes" / "tidy up my recent changes"
- "/simplify" (Claude Code habit carried over)

For "review my code" or correctness review, use `requesting-code-review` instead.

Honor optional user modifiers:

- **Focus:** "simplify focus on efficiency": run only efficiency reviewer (or weight aggregation toward it). Recognized focuses: `reuse`, `quality` (also accepts `simplification`), `efficiency`, `altitude`.
- **Dry run:** "simplify but don't change anything" / "just report": run four reviewers, present findings, apply NOTHING. Ask before applying.
- **Scope:** "simplify the last commit" / "simplify staged" / "simplify src/foo.py": narrow diff source to match (see Phase 1).

Do NOT auto-run after every edit or tack onto unrelated tasks. Costs four subagents' worth of tokens; invoke only when user explicitly asks.

## The Process

### Phase 1 — Identify the changes

Pick diff source by user request, in this default order:

```bash
# 1. Default: uncommitted working-tree changes (tracked files)
git diff

# 2. If that's empty, include staged changes
git diff HEAD

# 3. Scoped variants the user may request:
git diff --staged                 # "staged changes"
git diff HEAD~1                    # "the last commit"
git diff main...HEAD              # "this branch" / "my PR"
git diff -- src/foo.py            # specific file(s)
```

If `git diff` and `git diff HEAD` are both empty and there's no git repo or no changes, fall back to files user explicitly named or files created/edited this session. If no changed code found, say so and stop.

Capture full diff text. If very large (say >2000 changed lines), warn that four subagents each carrying full diff is token-heavy. Offer to scope down (per-directory, per-commit) first.

### Phase 2 — Launch four reviewers in parallel

Use `delegate_task` **batch mode**: all four tasks in one `tasks` array, run concurrently. Four fits `delegation.max_concurrent_children` budget on any default install.

**No delegation available?** If `delegate_task` can't be called here (leaf subagent, delegation disabled, or budget exhausted), do NOT skip review or drop angles. Run all four angles yourself, sequentially, with same search standards and finding format. Final summary must state: single-pass inline review, not parallel fan-out.

Give **every** reviewer the **complete diff** (not fragments — cross-file issues hide in gaps) plus absolute repo path for wider search. Each gets `terminal`, `file`, and `search` toolsets (for `git`, `read_file`, and `search_files`/grep).

Tell each reviewer to:
- Search codebase for evidence; don't reason from diff alone.
- **Apply Chesterton's Fence:** before flagging anything for removal, run `git blame` on the line to learn why it exists. If original purpose is unknown, mark it `confidence: low`; don't guess.
- Report findings as structured output with concrete cost, confidence, and risk:
  ```
  file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
  ```
  **cost** forces each finding to justify itself. Finding that can't state its cost is probably a nit.
  - **SAFE** = proven not to affect behavior (unused imports, commented-out code, pass-through wrappers). Auto-apply.
  - **CAREFUL** = improves without changing semantics (rename local variable, flatten nested ternary, extract helper). Apply with test verification.
  - **RISKY** = may change behavior or breaks public contracts (N+1 restructuring, public API rename, memory lifecycle change). Flag for human review; do NOT auto-apply.
- Skip nits and style-only churn. Flag only material improvements.

Pass these four goals (drop any the user's focus excludes):

**Reviewer 1 — Code Reuse**
> Review this diff for code that duplicates functionality already in the
> codebase. Search utility modules, shared helpers, and adjacent files
> (use search_files / grep) for existing functions, constants, or patterns
> the new code could call instead of reimplementing. Flag: new functions
> that duplicate existing ones; hand-rolled logic that an existing utility
> already does (manual string/path manipulation, custom env checks, ad-hoc
> type guards, re-implemented parsing). For each, name the existing thing to
> use and where it lives.

**Reviewer 2 — Code Quality**
> Review this diff for quality problems. Look for: redundant state (values
> that duplicate or could be derived from existing state; caches that don't
> need to exist); parameter sprawl (new params bolted on where the function
> should have been restructured); copy-paste-with-variation (near-duplicate
> blocks that should share an abstraction); leaky abstractions (exposing
> internals, breaking an existing encapsulation boundary); stringly-typed
> code (raw strings where a constant/enum/registry already exists — check the
> canonical registries before flagging); deeply nested conditionals (ternary
> chains, 3+-level if/else pyramids — flatten with guard clauses, early
> returns, or a lookup table); AI-generated slop patterns (extra
> comments restating obvious code like `// increment counter` above `count++`;
> unnecessary defensive null-checks on already-validated inputs; `as any`
> casts that bypass the type system; patterns inconsistent with the rest of
> the file). For each, give the concrete refactor.

**Reviewer 3 — Efficiency**
> Review this diff for efficiency problems. Look for: unnecessary work
> (redundant computation, repeated file reads, duplicate API calls, N+1
> access patterns); missed concurrency (independent ops run sequentially);
> hot-path bloat (heavy/blocking work on startup or per-request paths);
> TOCTOU anti-patterns (existence pre-checks before an op instead of doing
> the op and handling the error); memory issues (unbounded growth, missing
> cleanup, listener/handle leaks; long-lived callbacks or objects built as
> closures that capture the whole enclosing scope — everything captured
> stays alive as long as the object does, so prefer a small class or
> explicit-fields struct that copies only what it needs); overly broad reads
> (loading whole files when a slice would do); silent failures (empty catch
> blocks, ignored error returns, `except: pass`, `.catch(() => {})` with no
> handling, error propagation gaps — these hide bugs and should at minimum
> log before swallowing). For each, give the concrete fix and why it's
> faster or safer.

**Reviewer 4 — Altitude**
> Review this diff for changes implemented at the wrong depth — band-aids
> layered on top of shared infrastructure instead of fixes to the
> infrastructure itself. Signs of a too-shallow fix: a special case added to
> a generic code path to handle one caller (an `if (caller == X)` branch, a
> type check, a magic-value escape hatch); a symptom patched at the call
> site while sibling call sites keep the same flaw; a workaround stacked on
> an earlier workaround; a wrapper added to avoid touching the thing that
> actually needs changing; configuration or flags introduced to route around
> a broken default instead of fixing the default. For each, identify the
> underlying mechanism the change is dodging and describe the deeper fix —
> generalize the shared path, fix the root default, or fix the whole bug
> class — and honestly note when the deeper fix is large enough that it
> should be its own task rather than part of this cleanup. Read the
> surrounding code and `git blame` first: what looks like a band-aid is
> sometimes a deliberate boundary (compat shims, staged migrations,
> vendored-code isolation). Don't flag those.

### Phase 3 — Aggregate and apply

Wait for all four to return (batch mode returns them together).

1. **Merge** findings into one list. Collapse findings that target same line or same underlying mechanism.
2. **Discard false positives.** Silently drop weak or wrong suggestions; no arguing with reviewers.
3. **Resolve conflicts.** Reviewers can disagree (Reviewer 1: "use existing util X"; Reviewer 3: "X is slow, inline it"). Default resolution order: **correctness > the user's stated focus > readability/reuse > micro-perf.** Don't apply perf "fix" that hurts clarity unless path is genuinely hot. If two suggestions are mutually exclusive and both defensible, pick one touching less code and note the alternative.
4. **Apply in risk-tier order:**
   - **SAFE first** (auto-apply): unused imports, commented-out code, pass-through wrappers, redundant type assertions. Run tests after.
   - **CAREFUL next** (apply with verification, one file at a time): rename locals, flatten ternaries, extract helpers, consolidate dupes. Run tests after each file. If one breaks, undo only your own edit (reverse that patch); never `git checkout`/`restore`/`reset`/`stash` files, since default diff is user's uncommitted work.
   - **RISKY last** (flag for review — do NOT auto-apply): N+1 restructuring, public API changes, concurrency fixes, error-handling changes. Present each with risk description and test coverage status. Altitude findings usually land here: deeper fix touches shared infrastructure. Present it; user decides whether to do it now or as follow-up.
   On dry run, present all three tiers and apply nothing.
5. **Verify** nothing broke: run targeted tests for touched files (not full suite). Re-run repo's linter/type check, if any. If a fix breaks a test, undo only that edit (same rule, no git revert commands) and report it.
6. **Summarize** applied fixes, grouped by reviewer category and risk tier, plus deliberately skipped findings and why.

## Pitfalls

- **Don't fan out wider than 4.** More reviewers add cost and conflicting suggestions, not coverage.
- **Reviewers search, they don't guess.** Reuse finding with no pointer to existing utility ("there's probably a helper for this") is noise. Require `file:line` evidence; drop findings without it.
- **Apply ≠ rewrite.** Clean up user's recent changes; don't refactor whole module. Limit edits to what diff touched plus minimal surrounding change a fix requires. Altitude findings are the exception: if right fix is deeper than diff, FLAG it. Don't unilaterally rebuild shared mechanism in cleanup pass.
- **Don't drift into bug-hunting.** Report genuine correctness bug prominently, but as separate "found a bug" note, not folded into cleanup fixes.
- **Respect project conventions.** If repo has AGENTS.md / CLAUDE.md / HERMES.md or linter config, fold those rules into reviewer prompts so suggestions match house style.
- **Large diffs blow context.** Scope huge diffs down before delegating. Four subagents each carrying 5000-line diff is expensive and may truncate.
- **Over-trusting dead code tools.** `knip`, `ts-prune`, and `depcheck` flag exports that ARE used dynamically (string-based imports, reflection). Always grep for symbol name before removing; clean tool report is not proof.
- **Renaming without checking public contracts.** Export names, API route paths, DB column names, and config keys are contracts. Renaming breaks consumers, even if name is bad. Tag public-contract changes RISKY; never auto-rename them.
- **Removing "unnecessary" error handling.** Empty catch block or ignored error might be intentional (expected and benign in that context). Flag it, don't remove it; human decides.
- **Not every special case is a band-aid.** Compat shims, staged migrations, and isolation layers around vendored code are deliberate design, not altitude violations. Check `git blame` and surrounding comments before flagging; if intent unclear, mark `confidence: low`.

## Related

If installed, optional `subagent-driven-development` skill covers complementary case: parallel review *during* implementation, per task. This skill is standalone *after-the-fact* cleanup pass. Use `requesting-code-review` for pre-commit security/quality gate.
