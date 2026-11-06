---
name: writing-for-agents
description: Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.
---

Reference for writing any document an agent consumes: skill, `AGENTS.md` / `CLAUDE.md`, doc reached by pointer. Packaging differs, writing does not: same levers make each predictable, meaning agent takes same _process_ every run, not same output.

Writing a skill: read [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md) for frontmatter, invocation choice, router skills.

## Context pointers

**Context pointer**: in-context reference naming out-of-context material and encoding condition for reaching it. Skill description is one; `AGENTS.md` line naming a doc is same object. Pointer's _wording_, not target, decides when and how reliably agent reaches material. Must-have target behind weakly worded pointer is a variance bug: sharpen wording first; inline material only if sharpening fails.

Pointer does two jobs: say what material is; list **branches** that should trigger reaching it (branch: distinct case document handles, so different runs take different paths through the document). Always-loaded pointer costs every word every turn, so prune it even harder than body:

- **Front-load the leading word**: pointer is where it does triggering work.
- **One trigger per branch.** Synonyms renaming one branch are one branch written twice; collapse them, keep only distinct branches.
- **Cut identity the body already carries.**

## The two loads

Every added document and pointer spends one of two budgets:

- **Context load**: cost of always-loaded material on agent's window (`AGENTS.md` line, skill description, anything in context every turn). Spends tokens and attention whether or not it fires.
- **Cognitive load**: cost on human, knowing which documents exist and when to reach for each. Human is the index. Not a cost to minimise: price of human agency. Spend it where human judgement matters; remove it where it does not.

Pointer-only material escapes context load, paying only pointer's own line. Material with no pointer rides entirely on cognitive load.

## Information hierarchy

Documents hold two content types: **steps** (ordered agent actions) and **reference** (definitions, rules, facts consulted on demand). Any mix works: all steps (recipe), all reference (review rules, this skill), or both. Core decision: where each piece sits on **information hierarchy**, a ladder ranked by how immediately agent needs it:

1. **In-file step**: primary tier. What agent does, in order.
2. **In-file reference**: consulted on demand. Often a legitimately flat peer-set (every review rule on one rung): fine, not a smell.
3. **Disclosed reference**: moved to separate file behind context pointer, loaded only when pointer fires. Ranges from sibling file in same folder to fully external reference that lives anywhere and any document can point at.

Push too little down: top bloats. Push too much: you hide material agent actually needs. That tension is the whole decision.

**Progressive disclosure**: moving down the ladder (out of main file, behind a pointer) so top stays legible. Mainly protects hierarchy, not tokens. Cleanest disclosure test is branching: inline what every branch needs; push behind a pointer what only some branches reach. In a document with steps, in-file reference that should be disclosed buries them, making attention to them a coin-flip: a variance lever, not just legibility.

**Co-location**: within-file companion. Ladder decides _how far down_ a piece sits; co-location decides _what sits beside it_ once there. Keep a concept's definition, rules, and caveats under one heading, not scattered, so reading one part brings its neighbours. Test: document should read like documentation written for the agent. Grouped material does; scattered material does not. (Not duplication, which repeats one meaning in two places; scattering fragments one meaning across many.)

**Sprawl**: failure mode here. Document too long, even with every line live and unique. Attention thins across excess; every extra line is one more to keep relevant. Cure is the ladder: disclose reference behind pointers; split by branch or sequence so each path carries only what it needs.

## Steps and completion criteria

Every step ends on a **completion criterion**: condition telling agent work is done. Two properties make it a lever:

- **Clarity**: can agent tell done from not-done? Vague bound ("understanding reached") invites **premature completion**: ending step before it is done, attention slipping to _being done_. Visible steps ahead (**post-completion steps**) pull; criterion's clarity resists. Defend in order: **sharpen the bound first** (local, cheap). Only if bound is irreducibly fuzzy _and_ you observe the rush, hide later steps by splitting the sequence. Hiding works only across a real context boundary (hand-off or subagent dispatch). Inline call leaves later steps in context, clearing nothing.
- **Demand**: how much it requires. "Every modified model accounted for" forces thorough work; "produce a change list" does not. Demand drives **legwork**: digging agent does within the work, latent in wording, not written as its own step. Demand is not step-bound: "every rule applied" binds flat reference just as "every step done" binds a sequence. So all-reference documents still carry an exhaustiveness bar.

Strongest criteria are both checkable and exhaustive.

## When to split

Every split spends one of the two loads. Split only when the cut earns it:

- **By sequence**: split steps where post-completion steps tempt agent to rush the current one. Keeping them out of view drives more legwork on current task. Beware reverse: merging sequences exposes each step's later steps to what follows, inviting premature completion.
- **By invocation**, skill-specific: see [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md).

## Leading words

**Leading word**: compact concept already in model's pretraining that agent thinks with while running the document (_lesson_, _fog of war_, _tracer bullets_). Repeated as token, never as sentence, it accumulates a distributed definition. Recruiting priors model already holds, it anchors a whole region of behaviour in fewest tokens. Coined words work if defined clearly, but recruit no priors: you pay definition tokens for what a pretrained word gives free. Reach for existing words first.

Anchors twice. In body, _execution_: agent reaches for same behaviour wherever the word appears; inside flat reference it focuses attention on a class of thing to look for. In a pointer, _invocation_: when same word lives in your prompts, docs, and codebase, agent links that shared language to the material and reaches it more reliably.

Hunt leading-word refactors: a triad spelled out at three sites, a pointer spending a sentence gesturing at one idea. Each begs to collapse into one token:

- "fast, deterministic, low-overhead" → _tight_ (a _tight_ loop).
- "a loop you believe in" → _red_, turning a fuzzy gate into a binary observable state (the loop goes _red_ on the bug, or it doesn't).

Assume every document carries restatements leading words can retire. Find them.

**Negation**: failure mode beside this lever. Prohibition drags forbidden behaviour into context, making it _more_ available, not less. _Don't think of an elephant_, and elephant is all there is. Negation is a weak modifier the strongly-activated concept overruns, so the ban half-reads as instruction to do the thing. Prompt the **positive**: state target behaviour ("write one-line comments") so banned one is never spoken. Prohibition earns its place only as a hard guardrail you cannot phrase positively. Even then, pair it with positive target so attention lands on what to do.

## Pruning

- Keep each meaning in a **single source of truth**: one authoritative place, so changing behaviour is a one-place edit. **Duplication** (same meaning in more than one place) costs maintenance and tokens, and inflates meaning's prominence on the ladder past its real rank. (Accidental inverse of a leading word, which repeats a token on purpose, never the meaning.)
- **Environment** is a source of truth too (`package.json` scripts, config files, directory layout, `--help` output). Document restating it is a **cache**: copy of a lookup, earning its load only when lookup is expensive. Cache what agent cannot find by looking: unwritten convention, reason behind a choice, gotcha no config confesses. Leave one-file, one-command lookups to environment, where they cannot go stale.
- Check every line for **relevance**: does it still bear on what document does? Lines lose relevance by never bearing on the task (mere exposition, or a branch that should be disclosed), or by going stale as described behaviour or world changes. Without pruning discipline, default fate is **sediment**: stale layers settle because adding feels safe and removing feels risky, until you must core down through them to find what is still live.
- Hunt **no-ops** sentence by sentence: instruction model already obeys by default pays load to say nothing. Test (does it change behaviour versus default?) is model-relative, not reader-relative. People disagreeing about a no-op disagree about the default; settle it by running the document, not by debate. Failing sentence: delete it whole; do not trim words from it. Test also grades leading words: word too weak to beat default (_be thorough_ when agent is already thorough-ish) is a no-op. Fix is a stronger word (_relentless_), not a different technique.
