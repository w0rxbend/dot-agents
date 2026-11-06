---
name: idea-refine
description: "Refine a raw idea into a one-page brief (problem statement, recommended direction, assumptions to validate, MVP scope, not-doing list) through divergent then convergent thinking. Use when an idea is still vague or you want options and a stress test before committing; use interview-me when the goal itself is unclear and spec-driven-development once the direction is chosen."
risk: safe
source: https://github.com/addyosmani/agent-skills/tree/main/skills/idea-refine
source_repo: addyosmani/agent-skills
source_type: community
date_added: 2026-07-01
license: MIT
license_source: https://github.com/addyosmani/agent-skills/blob/main/LICENSE
---

# Idea Refine

## When to Use

- Idea still vague; need options before committing to one.
- Want to stress-test assumptions behind direction before planning it.

Do not use when user already knows what they want (use `spec-driven-development`), or when goal itself is unclear (use `interview-me` first).

## Usage

```bash
# Optional: Initialize the ideas directory
bash "<skill-directory>/scripts/idea-refine.sh"   # run from the project root; creates docs/ideas/
```

**Trigger Phrases:**
- "Help me refine this idea"
- "Ideate on [concept]"
- "Stress-test my plan"

## Detailed Instructions

### Philosophy

- Simplicity is the ultimate sophistication. Push toward simplest version that still solves real problem.
- Start with user experience, work backwards to technology.
- Say no to 1,000 things. Focus beats breadth.
- Challenge every assumption. "How it's usually done" is not a reason.

### Process

When user invokes skill with idea (`$ARGUMENTS`), guide them through three phases. Adapt to what they say. This is conversation, not template.

#### Phase 1: Understand & Expand (Divergent)

1. **Restate the idea** as crisp "How Might We" problem statement.

2. **Ask 3-5 sharpening questions** — no more. Focus on:
   - Who is this for, specifically?
   - What does success look like?
   - What are the real constraints (time, tech, resources)?
   - What's been tried before?
   - Why now?

   Use `AskUserQuestion` tool to gather input. Do NOT proceed until you understand who this is for and what success looks like.

3. **Generate 5-8 idea variations** using these lenses:
   - **Inversion:** "What if we did the opposite?"
   - **Constraint removal:** "What if budget/time/tech weren't factors?"
   - **Audience shift:** "What if this were for [different user]?"
   - **Combination:** "What if we merged this with [adjacent idea]?"
   - **Simplification:** "What's the version that's 10x simpler?"
   - **10x version:** "What would this look like at massive scale?"
   - **Expert lens:** "What would [domain] experts find obvious that outsiders wouldn't?"

   Push beyond what user first asked for. Create products people don't know they need yet.

**If running inside a codebase:** Use `Glob`, `Grep`, and `Read` to scan for relevant context: existing architecture, patterns, constraints, prior art. Ground variations in what exists. Reference specific files and patterns when relevant.

Read `frameworks.md` in this skill directory for more ideation frameworks. Use selectively: pick lens that fits idea; don't run every framework mechanically.

#### Phase 2: Evaluate & Converge

After user reacts to Phase 1 (says which ideas resonate, pushes back, adds context), switch to convergent mode:

1. **Cluster** resonating ideas into 2-3 distinct directions. Each direction should feel meaningfully different, not just variations on theme.

2. **Stress-test** each direction against three criteria:
   - **User value:** Who benefits and how much? Painkiller or vitamin?
   - **Feasibility:** What's technical and resource cost? What's hardest part?
   - **Differentiation:** What makes this genuinely different? Would someone switch from their current solution?

   Read `refinement-criteria.md` in this skill directory for full evaluation rubric.

3. **Surface hidden assumptions.** For each direction, name explicitly:
   - What you're betting is true (but haven't validated)
   - What could kill this idea
   - What you're choosing to ignore (and why that's okay for now)

   Most ideation fails here. Don't skip it.

**Be honest, not supportive.** If idea is weak, say so with kindness. Good ideation partner is not yes-machine. Push back on complexity, question real value, point out when emperor has no clothes.

#### Phase 3: Sharpen & Ship

Produce concrete artifact: markdown one-pager that moves work forward:

```markdown
# [Idea Name]

## Problem Statement
[One-sentence "How Might We" framing]

## Recommended Direction
[The chosen direction and why — 2-3 paragraphs max]

## Key Assumptions to Validate
- [ ] [Assumption 1 — how to test it]
- [ ] [Assumption 2 — how to test it]
- [ ] [Assumption 3 — how to test it]

## MVP Scope
[The minimum version that tests the core assumption. What's in, what's out.]

## Not Doing (and Why)
- [Thing 1] — [reason]
- [Thing 2] — [reason]
- [Thing 3] — [reason]

## Open Questions
- [Question that needs answering before building]
```

**"Not Doing" list is arguably most valuable part.** Focus means saying no to good ideas. Make trade-offs explicit.

Ask user whether to save this to `docs/ideas/[idea-name].md` (or location of their choosing). Save only if they confirm.

### Anti-patterns to Avoid

- **Don't over-engineer the process.** Three phases, each doing one thing well. Resist adding steps.
- **Don't just list ideas — tell a story.** Each variation needs reason it exists, not just bullet point.

### Tone

Direct, thoughtful, slightly provocative. Sharp thinking partner, not facilitator reading from script. Channel energy of "that's interesting, but what if..." -- always push one step further without being exhausting.

Read `examples.md` in this skill directory for examples of great ideation sessions.

## Red Flags

- 20+ shallow variations instead of 5-8 considered ones
- Skipping "who is this for" question
- No assumptions surfaced before committing to direction
- Yes-machining weak ideas instead of pushing back with specificity
- Plan without "Not Doing" list
- Ignoring existing codebase constraints when ideating inside project
- Jumping straight to Phase 3 output without running Phases 1 and 2

## Verification

After ideation session:

- [ ] Clear "How Might We" problem statement exists
- [ ] Target user and success criteria defined
- [ ] Multiple directions explored, not just first idea
- [ ] Hidden assumptions listed explicitly with validation strategies
- [ ] "Not Doing" list makes trade-offs explicit
- [ ] Output is concrete artifact (markdown one-pager), not just conversation
- [ ] User confirmed final direction before any implementation work
