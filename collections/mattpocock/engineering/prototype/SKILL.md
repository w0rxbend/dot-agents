---
name: prototype
description: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
---

# Prototype

Prototype is **throwaway code that answers a question**. Question decides shape.

## Pick a branch

Find the question from user's prompt or surrounding code, or ask if user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). One shareable HTML file (free-play buttons, tabbed guided walkthroughs) pushing state machine through cases hard to reason about on paper. Non-developer can drive it.
- **"What should this look like?"** → [UI.md](UI.md). Several radically different UI variations on one route, switched via URL search param and floating bottom bar.

If question is genuinely ambiguous and user unreachable, pick branch matching surrounding code (a backend module → logic; a page or component → UI). State assumption at top of prototype.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Put code next to module or page it prototypes for, so context is obvious. Name it so casual reader sees it's prototype, not production. Throwaway UI routes follow project's existing routing convention; no new top-level structure.
2. **Trivial to run.** UI prototype: one command in project's task runner (`pnpm <name>`, `python <path>`, `bun <path>`, etc.). Logic demo: one HTML file user double-clicks.
3. **No persistence by default.** State lives in memory. Persistence is what prototype is _checking_, not a dependency. If question explicitly involves a database, hit scratch DB or local file with clear "PROTOTYPE, wipe me" name.
4. **Skip the polish.** No tests, no error handling beyond what makes it _runnable_, no abstractions.
5. **Surface the state.** After every action (logic) or variant switch (UI), print or render full relevant state so user sees what changed.
6. **Capture it when done.** Fold validated decision into real code. Capture prototype itself as **primary source**: commit to throwaway branch, out of main; leave context pointer to that branch on implementation issue. Record answer too (verdict and question it settled) in issue or commit. Main keeps only validated decision.
