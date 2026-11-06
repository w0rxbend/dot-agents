---
name: using-agent-skills
description: "Pick which installed skill (if any) to load for the current engineering task, and avoid loading whole skill families or running lifecycle ceremony for simple edits. Use when unsure which installed skill applies or when the user asks how skills fit together."
---

# Choosing Engineering Skills

Use skill descriptions to pick guidance that changes a decision in requested task. Repository instructions and user's current choices set workflow. Skill never overrides them.

For clear implementation request, start from existing code, build configuration and acceptance criteria. If unclear goal affects result, ask smallest useful question. Meanwhile, continue independent work. Reuse preferences and authorization already given in session.

## Match the task

| Situation | Load |
|---|---|
| Unclear goal or requirements | `interview-me`, `idea-refine` or `spec-driven-development`, only when that phase is needed |
| Large or multi-step implementation | `planning-and-task-breakdown`, then `incremental-implementation` |
| New behavior needing safety net | `test-driven-development`, or language's testing skill (e.g. `pytest-fixtures`, `golang-testing`, `mill-testing`) |
| Something broke, cause unknown | `debugging-and-error-recovery` plus relevant language/tool skill |
| Judging or reviewing change | `code-review` (run PR/diff review), `code-review-and-quality` (rubric) |
| Cleanup without behavior change | `code-simplification` (readability), `refactoring-guru` (structural, smell-driven) |
| Public API or module boundary | `api-and-interface-design` |
| UI work | `frontend-ui-engineering`; `frontend-design` for visual direction; `frontend-dev-guidelines` in React + MUI + TanStack repos |
| Slow code or endpoint | `performance-optimization`; load tests and SLOs: `performance-engineering` |
| Security-sensitive feature | `security-and-hardening` |
| Logs, metrics, traces in code | `observability-and-instrumentation` |
| Analytics events and tracking plans | `analytics` |
| Decision records, READMEs, changelogs | `documentation-and-adrs` |
| Git, CI, release, deployment | `git-workflow-and-versioning`, `ci-cd-and-automation`, `shipping-and-launch`, only when request includes that work |
| Agent context, memory, delegation | `context-engineering`, `agent-memory-systems`, `agent-orchestration-improve-agent` |
| Writing or fixing skill | `skill-writer` |
| Language or build question | Language skill plus detected build tool. For new JVM build here, prefer Mill skills. Keep existing build unless migration is requested |

If no installed skill fits, do task directly.

## Rules

- Do not load whole skill family because repository uses that language. Start with primary task. Read supporting guidance when concrete question needs it.
- One primary skill per task phase. Add second skill only when it answers question first skill does not.
- Tool-specific skill requires callable tool or documented fallback.
- Simple, well-specified edit needs no spec, plan or ceremony. Make it, verify it.

## Completion

Verify intended behavior with checks proportional to change, plus any required repository checks. Report result and material limits. Read-only review produces findings. It does not imply publishing comments, creating issues, committing or deploying.
