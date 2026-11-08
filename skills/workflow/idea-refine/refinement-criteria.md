# Refinement & Evaluation Criteria

Use this rubric in Phase 2 (Evaluate & Converge) to stress-test idea directions. Not every criterion applies to every idea. Judge which dimensions matter most for specific context.

## Core Evaluation Dimensions

### 1. User Value

Most important dimension. If value isn't clear, nothing else matters.

**Painkiller vs. Vitamin:**
- **Painkiller:** Solves acute, frequent problem. Users actively seek it out and switch from current solution. Signs: people describe problem with emotion, have built workarounds, will pay for solution.
- **Vitamin:** Nice to have. Makes something marginally better. Users won't go out of their way. Signs: people nod politely, say "that's cool," then don't change behavior.

**Questions to ask:**
- Can you name 3 specific people who have this problem right now?
- What do they do today instead? (Real competitor is always current workaround.)
- Would they switch from current approach? What would make them switch?
- How often do they hit this problem? (Daily problems > monthly problems)
- Is this "pull" problem (users ask for it) or "push" problem (you think they should want it)?

**Red flags:**
- "Everyone could use this" — if you can't name specific user, value isn't clear
- "It's like X but better" — marginal improvements rarely drive adoption
- Problem is real but rare — high intensity but low frequency rarely justifies product

### 2. Feasibility

Can you build this? Practically, not just technically.

**Technical feasibility:**
- Does core technology exist and work reliably?
- What's hardest technical problem? Known-hard or novel?
- Any dependencies on third parties, APIs, or data sources you don't control?
- Minimum technical stack needed? (If answer is "a lot," that's a signal.)

**Resource feasibility:**
- Minimum team/effort to build MVP?
- Needs specialized expertise you don't have?
- Any regulatory, legal, or compliance requirements?

**Time-to-value:**
- How fast can you get something in front of users?
- Is there version that delivers value in days/weeks, not months?
- What's critical path? What must happen first?

**Red flags:**
- "We just need to solve [very hard research problem] first"
- Multiple dependencies that all need to work simultaneously
- MVP still needs months of work — likely not minimal enough

### 3. Differentiation

What makes this genuinely different? Not better — *different*.

**Questions to ask:**
- If user described this to friend, what would they say? Is that description compelling?
- What's one thing this does that nothing else does? (If you can't name one, that's a problem.)
- Is differentiation durable? Can competitor copy it in a week?
- Do users care about the difference, or do only builders find it interesting?

**Types of differentiation (strongest to weakest):**
1. **New capability:** Does something previously impossible
2. **10x improvement:** So much better on key dimension that it changes behavior
3. **New audience:** Brings existing capability to people who were excluded
4. **New context:** Works where existing solutions fail
5. **Better UX:** Same capability, dramatically simpler experience
6. **Cheaper:** Same thing, lower cost (weakest — easily competed away)

**Red flags:**
- Differentiation is entirely about technology, not user experience
- "We're faster/cheaper/prettier" without structural reason why
- Differentiating feature is not feature users care most about

## Assumption Audit

For every idea direction, list assumptions explicitly in three categories:

### Must Be True (Dealbreakers)
If wrong, idea dies entirely. Validate before building.

Example: "Users will share their data with us" — if they won't, whole product doesn't work.

### Should Be True (Important)
Strongly affect success but don't kill idea. If wrong, adjust approach.

Example: "Users prefer self-serve over talking to a person" — if wrong, you need different go-to-market, but core product can still work.

### Might Be True (Nice to Have)
Assumptions about secondary features or optimizations. Don't validate until core is proven.

Example: "Users will want to share their results with teammates" — growth feature, not core value proposition.

## Decision Framework

When choosing between directions, rank on this matrix:

|                    | High Feasibility | Low Feasibility |
|--------------------|-------------------|-----------------|
| **High Value**     | Do this first     | Worth the risk   |
| **Low Value**      | Only if trivial   | Don't do this    |

Then use differentiation as tiebreaker between options in same quadrant.

## MVP Scoping Principles

When defining MVP scope for chosen direction:

1. **One job, done well.** MVP should nail exactly one user job. Not three jobs done partially.
2. **The riskiest assumption first.** MVP's main purpose: test assumption most likely to be wrong.
3. **Time-box, not feature-list.** "What can we build and test in [timeframe]?" beats "What features do we need?"
4. **The 'Not Doing' list is mandatory.** Name explicitly what you're cutting and why. Prevents scope creep and forces honest prioritization.
5. **If it's not embarrassing, you waited too long.** First version should feel incomplete to builder. If it doesn't, you over-built.
