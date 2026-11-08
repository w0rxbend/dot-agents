---
name: ask-matt
description: Ask which skill or flow fits your situation. A router over the skills in this repo.
disable-model-invocation: true
---

# Ask Matt

Before describing a skill or advising to skip a step, read that skill's SKILL.md. Summaries here only orient.

A **flow** is a path through the skills. Most follow one **main flow**; two **on-ramps** merge onto it. Rest: standalone, or a vocabulary layer underneath.

## The main flow: idea → ship

Route for most work: an idea you want built.

1. **`/grill-with-docs`** sharpens the idea by interview. Start here whenever **working in a working directory**: it's stateful, saving learnings to `GLOSSARY.md` and ADRs. (No working directory? Use `/grill-me`, under Standalone.)
2. **Branch: can you settle every question in conversation?** Question needs a runnable answer (state, business logic, a UI you must see)? Detour through a prototype, bridged by **`/handoff`** both ways, since a prototype lives in its own directory (see Phase boundaries):
   - **`/handoff`** out, then open a fresh session against that file,
   - **`/prototype`** answers the question with throwaway code,
   - **`/handoff`** back what you learned; reference it from the original idea thread.
3. **Branch: is this a multi-session build?**
   - **Yes** → **`/to-spec`** (thread into spec), then **`/to-tickets`** (split into tracer-bullet tickets, each declaring its **blocking edges**). Work tickets one of two ways:
     - **`/implement`** per ticket, **`/clear`ing context between each one**. Local tracker: one file per ticket under `.scratch/<feature>/issues/`, worked blockers-first by hand. Real tracker: edges become native blocking links; grab any ticket whose blockers are done.
     - **`/implement-spec`**: whole spec in one run. Reads tickets as a **task graph**, runs implementer subagents across the ready **frontier** in parallel, lands everything on one **integration branch**. Use to orchestrate the build rather than drive each ticket.
   - **No** → **`/implement`** right here, same context window.

   Either way, the build drives **`/tdd`** (one red-green slice at a time) and ends with **`/code-review`**, a two-axis review (Standards + Spec) of the diff. `/implement` runs both per ticket. Under `/implement-spec`, each implementer drives `/tdd`; one `/code-review` covers the integration branch. Use **`/tdd`** alone to build a concrete behaviour test-first without a full spec, and **`/code-review`** alone to review a branch or PR against a fixed point.

   For a pull request, **`/pr`** shapes the body: smallest visual showing the change, before/after evidence it works, one-way or two-way door call. Model-invoked: agent uses it whenever writing a PR.

4. **`/retro`** closes the loop. After a build, especially a sideways one, it reviews the session and suggests changes to the agent's **environment**, not the code: navigation pointers, automated checks, coding standards `/code-review` enforces, steering files, tooling. Mechanical mistakes become deterministic checks; judgement calls become coding standards.

### Context hygiene

Keep steps 1–3 in **one unbroken context window** (no compact or clear until after `/to-tickets`) so grilling, spec and tickets build on the same thinking. Each `/implement` starts fresh from its ticket. Run `/retro` in the session it reviews, before clearing; after clearing, point it at that session's log.

Limit: the **[smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone)**, the window (~150k tokens on state-of-the-art models) where the model still reasons sharply. Nearing it before `/to-tickets`? Don't push on degraded; `/compact` at the nearest phase boundary and continue (see Phase boundaries).

## On-ramps

Starting situations that generate work, then merge onto the main flow.

- **Bugs and requests piling up** → **`/triage`**. Moves issues through triage roles into agent-ready issues for **`/implement`** to pick up.

  Triage only issues **you didn't create**: bug reports, incoming feature requests, anything raw. Tickets from `/to-tickets` are already agent-ready, so **don't triage them**.

- **Something's broken** → **`/diagnosing-bugs`**. For hard ones: bugs resisting a first glance, intermittent flakes, regressions that crept in between two known-good states. No theorising until it has a **tight feedback loop** (one command already red on *this* bug); then it fixes with a regression test. After the fix, run **`/retro`** in the same session to ask what would have prevented the bug. If the real finding is that there's no good seam to lock it down, that's a job for **`/improve-codebase-architecture`**.

- **A huge, foggy effort: a greenfield project or a huge feature build, too big for one session** → **`/wayfinder`**, the most cognitively demanding flow here. When the way to the destination isn't visible yet, it charts a **shared map** of **decision tickets** on the issue tracker and resolves them one by one. Output: **decisions, not deliverables**, until the way is clear. **`/grill-with-docs`** sharpens an idea that fits one session; wayfinder is for one that doesn't. Slower and denser: save it for exactly that, never a well-scoped feature.

  When the map clears, **it hands off, it doesn't build**. Merge onto the main flow at **`/to-spec`** (collapses the map's linked decisions into a buildable plan), then `/to-tickets` and `/implement` as usual. Looping the map straight into `/implement` skips that collapse and loses linked detail. Go straight to `/implement` only if the effort proved genuinely small.

## Codebase health

Upkeep, not feature work.

- **`/improve-codebase-architecture`**: run in any spare moment to keep the codebase good for agents to work in. Surfaces **deepening opportunities**; picking one _generates an idea_ for the main flow at `/grill-with-docs`. It's the survey finding candidates; **`/codebase-design`** (below) is the bench for designing the chosen one.

## Vocabulary underneath

Two model-invoked references running *beneath* other skills, each the single source of truth for its vocabulary. Use directly when the **words**, not the process, are the problem; otherwise skills above pull them in.

- **`/domain-modeling`**: sharpen the project's *domain* language: challenge a fuzzy term, resolve an overloaded word ("account" doing three jobs), record a hard-to-reverse decision as an ADR. `/grill-with-docs` drives it to keep `GLOSSARY.md` a clean glossary.
- **`/codebase-design`**: deep-module vocabulary (module, interface, depth, seam, adapter, leverage, locality) for designing a module's *shape*: much behaviour behind a small interface at a clean seam. `/tdd` and `/improve-codebase-architecture` both speak it.

## Phase boundaries

A **phase** is a chunk of work in a session: grilling, implementation, QA. At the **boundary** between two phases, pick one of five options: **Continue**, **`/clear`**, **`/handoff`**, **Subagent** or **`/compact`**. It's the fuzziest decision in this map.

Read [PHASE-BOUNDARIES.md](PHASE-BOUNDARIES.md) for the ordered tree: five questions, reasoning per branch, and why primary-source cost makes **Continue** the first to rule out. Decide **at** a boundary; mid-phase, continue or split the rest into subagents.

## Standalone

Off the main flow entirely.

- **`/grill-me`**: the relentless interview of `/grill-with-docs`, but **stateless**: saves nothing locally, builds no `GLOSSARY.md`. Use when **not working in a working directory** (a plan, design, piece of writing, anything with no repo under it). In a working directory, `/grill-with-docs` is strictly better: same interview plus a paper trail.
- **`/grilling`**: the interview primitive itself: rounds, the frontier, facts are the agent's job, decisions are yours. `/grill-me` and `/grill-with-docs` are the two named ways in; `/triage`, `/wayfinder` and `/improve-codebase-architecture` run it internally. Use directly only for the interview with no wrapper.
- **`/prototype`**: small throwaway program answering one design question: does this state model feel right, or what should this UI look like. Throwaway constrains how code is written; it's not a promise to destroy it. The answer folds into real code; the prototype stays as a **primary source** on a `prototype/<name>` branch out of main, pointed at from the implementation issue. It's the step 2 detour, but use it whenever a design question is hard to settle on paper.
- **`/research`**: hand reading legwork to a **background agent**. It investigates a question against **primary sources** and leaves a cited Markdown file in the repo. Keep working meanwhile. Take the file *into* the main flow at `/grill-with-docs`: research feeds thinking, doesn't replace it.
- **`/to-questionnaire`**: when the blocker is in **someone else's** head, not yours or the codebase, it writes them a questionnaire. Inverse of `/grill-me`: it interviews you about the **send** (who it's going to, what you need back), not the subject, and aims questions at the gap. Answers feed `/grill-with-docs` or `/to-spec`.
- **`/wizard`**: steps only a **human** can take: provisioning infrastructure, setting up credentials or CI secrets, clicking through an unfamiliar third-party dashboard, running a one-off migration or cutover. Generates an interactive bash script that opens each URL, captures each value, and writes it into `.env` and GitHub secrets. Model-invoked: agent uses it on hitting a wall only you can pass. If the agent can do it itself, it should; this is only for a human genuinely in the loop.
- **`/wait-what`**: corrective for a message that didn't land. Use mid-conversation, inside any other skill: agent re-pitches what it just said with the context you lacked, in plain English, using `GLOSSARY.md` vocabulary. Works after the fact; `/grill-with-docs` is the upfront cure.
- **`/teach`**: learn a concept over multiple sessions, with the current directory as a stateful workspace.
- **`/writing-for-agents`**: reference for writing documents agents consume: skills, AGENTS.md, pointed-at docs.

## Precondition

**`/setup-matt-pocock-skills`**: run before your first engineering flow. Configures the issue tracker, triage labels and doc layout other skills assume. Custom issue trackers work too.
