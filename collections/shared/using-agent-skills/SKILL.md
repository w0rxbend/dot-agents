---
name: using-agent-skills
description: "Pick which installed skill (if any) to load for the current engineering task, and avoid loading whole skill families or running lifecycle ceremony for simple edits. Use when unsure which installed skill applies or when the user asks how skills fit together; to search for skills that are not installed use find-skills."
---

# Choosing Engineering Skills

Use skill descriptions to select guidance that changes a decision in the requested task. Repository instructions and the user's current choices determine the workflow; a skill never overrides them.

For a clear implementation request, start from the existing code, build configuration, and acceptance criteria. If the goal is unclear in a way that affects the result, ask the smallest useful question while progressing on independent work. Reuse preferences and authorization already given in the session.

## Match the task

| Situation | Load |
|---|---|
| Unclear goal or requirements | `interview-me`, `idea-refine`, or `spec-driven-development`, only when that phase is needed |
| Large or multi-step implementation | `planning-and-task-breakdown`, then `incremental-implementation` |
| New behavior that needs a safety net | `test-driven-development`, or the language's testing skill (e.g. `pytest-fixtures`, `golang-testing`, `mill-testing`) |
| Something broke, cause unknown | `debugging-and-error-recovery` plus the relevant language/tool skill |
| Judging or reviewing a change | `code-review` (run a PR/diff review), `code-review-and-quality` (rubric) |
| Cleanup without behavior change | `code-simplification` (readability), `refactoring-guru` (structural, smell-driven) |
| Public API or module boundary | `api-and-interface-design` |
| UI work | `frontend-ui-engineering`; `frontend-design` for visual direction; `frontend-dev-guidelines` in React + MUI + TanStack repos |
| Slow code or endpoint | `performance-optimization`; load tests and SLOs: `performance-engineering` |
| Security-sensitive feature | `security-and-hardening` |
| Logs, metrics, traces in code | `observability-and-instrumentation` |
| Analytics events and tracking plans | `analytics` |
| Decision records, READMEs, changelogs | `documentation-and-adrs` |
| Git, CI, release, deployment | `git-workflow-and-versioning`, `ci-cd-and-automation`, `shipping-and-launch` - only when that work is part of the request |
| Agent context, memory, delegation | `context-engineering`, `agent-memory-systems`, `agent-orchestration-improve-agent` |
| Writing or fixing a skill | `skill-writer` |
| Language or build question | The language skill and the detected build tool. For a new JVM build here, prefer the Mill skills; preserve an existing build unless migration is requested |

If no installed skill fits, do the task directly. Use `find-skills` only when the user asks to find or install a new skill.

## Rules

- Do not load an entire skill family because the repository uses that language. Start with the primary task and read supporting guidance when a concrete question needs it.
- One primary skill per task phase; add a second only when it answers a question the first does not.
- A tool-specific skill requires a callable tool or a documented fallback.
- A simple, well-specified edit needs no spec, plan or ceremony: make it and verify it.

## Completion

Verify the intended behavior using checks proportional to the change and any required repository checks. Report the result and material limits. A read-only review produces findings; it does not imply publishing comments, creating issues, committing, or deploying.
