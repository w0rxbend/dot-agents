---
name: using-agent-skills
description: "Select an appropriate installed engineering skill when the user asks about workflows or skill choice. Use existing task context and load only relevant guidance; ordinary well-specified edits do not need a lifecycle ceremony."
---

# Choosing Engineering Skills

Use skill descriptions to select guidance that changes a decision in the requested task. Repository instructions and the user's current choices determine the workflow.

For a clear implementation request, start from the existing code, build configuration, and acceptance criteria. If the goal is unclear in a way that affects the result, ask the smallest useful question while progressing on independent work. Reuse preferences and authorization already given in the session.

## Match the task

- Requirements or an unclear goal: `interview-me`, `idea-refine`, or `spec-driven-development`, only when that phase is needed.
- A large implementation: `planning-and-task-breakdown` and `incremental-implementation`.
- A concrete language/build question: the language skill and the detected build tool. For a new JVM build here, prefer the Mill skills; preserve an existing build unless migration is requested.
- Behavior that needs a safety net: `test-driven-development` or the repository's language-specific testing guidance.
- A failure: `debugging-and-error-recovery` plus a relevant language/tool skill.
- Review or refactoring: `code-review-and-quality`, `safe-refactor`, or the relevant focused language skill.
- Git, CI, release, or deployment work: apply that workflow only when it belongs to the user's request.

Do not load an entire skill family simply because the repository uses that language. Start with the primary task and read supporting guidance when a concrete question needs it. A tool-specific skill requires a callable tool or documented fallback.

## Completion

Verify the intended behavior using checks proportional to the change and any required repository checks. Report the result and material limits. A read-only review produces findings; it does not imply publishing comments, creating issues, committing, or deploying.
