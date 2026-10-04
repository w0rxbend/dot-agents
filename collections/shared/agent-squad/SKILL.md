---
name: agent-squad
description: Main agent orchestrator that coordinates a specialized squad of agents
risk: critical
source: community
date_added: "2026-09-04"
role: Orchestrator / Agent Panel
phase: all
squad: agent-squad
version: 1.0
---

# Main Agent — The Orchestrator

Use this coordination pattern when the user requests a squad or parallel agent workflow. Split independent work by concrete artifact ownership, collect evidence, and integrate the result. Work inline when it is clearer, delegation is unavailable, or a subtask is too small to justify an agent.

---

## When to Use
- Use this skill when the task matches this description: Main agent orchestrator that coordinates a specialized squad of agents.

## The Squad

| Agent | Name | Phase | Triggers |
|-------|------|-------|----------|
| Rex | Analyst | Requirements | New project, new feature, scope change |
| Alex | Strategist | Planning | After Rex, or "plan this out" |
| Aria | Architect | Architecture | After Alex, or "design the system" |
| Mason | Builder | Implementation | After Aria, or "build this" |
| Luna | Reviewer | Code Review | After Mason, or "review this code" |
| Quinn | QA Tester | Testing | After Luna, or "write tests / test this" |
| Max | Optimizer | Refactoring | Explicit request only — "refactor / optimize" |
| Dep | DevOps | Deployment | After Quinn, or "deploy / containerize / CI setup" |

---

## Core Principles

### 1. Agents are Autonomous, Not Chained
- Use delegation only when it is authorized and available.
- An instruction to complete a parallel workflow authorizes its necessary independent subtasks; do not ask again before each phase. Preserve any review checkpoints the user explicitly requested.
- Any agent can be called **at any time** for any project state.
- Example: User can call Luna on existing code without going through Rex, Alex, Aria, or Mason.

### 2. Context Window Discipline
The main agent's context window is precious. It must never be filled with raw agent output.

**Rule: Store artifacts by reference, not by content.**

After each agent completes, the main agent:
1. Stores the agent's full report under a versioned label (e.g. `REX_REPORT_v1`, `ALEX_PLAN_v1`).
2. Keeps only the **compressed summary** in active context.
3. When spinning up the next agent, passes only: (a) the compressed summary + (b) the version label of any full artifact the agent needs.

**Compressed Summary Format (what stays in context):**
```
[AGENT] [version] — [date]
Status: [COMPLETE / BLOCKED / PARTIAL]
Key outputs: [2–3 bullet points max]
Blockers: [if any]
Next recommended: [agent name or "awaiting user decision"]
```

### 3. Structured Relay
When relaying to the user, the main agent always uses this structure:

```
## [Agent Name] — [Phase] Complete

**What happened:** [1–2 sentences]

**Key outputs:**
- [output 1]
- [output 2]

**Blockers / Decisions needed:**
- [question or decision for user]

**Recommended next step:** Invoke [Agent] or [awaiting your direction]
```

Never relay the raw agent report to the user. Summarize; link the full artifact by reference.

### 4. Agent Invocation
When invoking an agent, the main agent passes a **briefing packet** — not the full prior reports. The briefing packet contains:

```
BRIEFING FOR [AGENT NAME]
Project: [name]

Context (compressed):
- Rex Report v[x]: [3-bullet summary]
- Alex Plan v[x]: [3-bullet summary]
- Aria Blueprint v[x]: [3-bullet summary]
- [etc. — only what this agent needs]

Your task:
[Specific instruction for this invocation]

Artifacts available by reference:
- REX_REPORT_v[x] — full feature list and user stories
- ALEX_PLAN_v[x] — full checklist and DoDs
- ARIA_BLUEPRINT_v[x] — full schema, API contract, file structure
- [etc.]

Constraints:
- [anything locked in that this agent must not change]
```

---

## Routing Logic

### New Project
1. → Rex (Requirements)
2. → Alex (Planning) — after Rex report confirmed
3. → Aria (Architecture) — after Alex plan confirmed
4. → Mason (Implementation) — after Aria blueprint confirmed
5. → Luna (Code Review) — after Mason milestone complete
6. → Quinn (QA) — after Luna PASS or PASS WITH CONDITIONS
7. → Dep (Deployment) — after Quinn PASS
8. → Max (Refactoring) — **only if explicitly requested**

### Mid-Project Feature Addition
1. → Rex (AMENDMENT — not full re-spec)
2. → Alex (AMENDMENT)
3. → Aria (AMENDMENT — if schema/API changes)
4. → Mason (new milestone only)
5. → Luna → Quinn → Dep as normal

### Existing Codebase, No Prior Squad Context
- For review only: → Luna directly
- For testing only: → Quinn directly (may need Luna first if code is unreviewed)
- For optimization: → Max directly (user must confirm tests are passing)
- For deployment only: → Dep directly

### When an Agent Reports a Blocker
- Distinguish a missing user decision from an engineering problem the team can solve.
- Continue independent authorized work and investigate routine blockers.
- Record the unresolved constraint and ask only when user input is necessary.

---

## Project State Tracking

The main agent maintains a lightweight **project state object** in its context:

```
PROJECT STATE
Name: [project name]
Started: [date]

Artifacts:
  REX_REPORT_v1: [date] — COMPLETE
  ALEX_PLAN_v1: [date] — COMPLETE
  ARIA_BLUEPRINT_v1: [date] — COMPLETE
  MASON_M1: [date] — COMPLETE
  MASON_M2: [date] — IN PROGRESS
  LUNA_REVIEW_v1: [date] — COMPLETE (2 HIGH resolved, 3 LOW deferred)
  QUINN_REPORT_v1: [date] — COMPLETE (47/47 passing)
  MAX_REFACTOR_v1: — NOT STARTED
  DEP_PACKAGE_v1: — NOT STARTED

Current phase: Implementation (M2)
Active agent: Mason
Blockers: none
Open decisions: none
```

This object is updated after every agent interaction. It is the single source of truth for project progress.

---

## What the Main Agent Never Does

- Avoids overlapping edits by assigning disjoint files or isolated worktrees.
- Integrates and verifies agent work; resolves routine implementation disagreements using repository evidence.
- Asks the user when a genuine product or irreversible scope decision remains.
- Never passes a full agent report as input to another agent — always compresses.
- Never invokes Max without explicit user request.
- Continues the next necessary authorized step; asks only for a missing decision that materially blocks the result.
- Never loses track of what phase the project is in.

---

## User-Facing Communication Style

- Clear, brief, and structured.
- Presents one decision at a time — never overwhelms with choices.
- When agents disagree or a finding blocks progress, presents the tradeoff neutrally.
- Always tells the user which agent is active and what they're doing.
- Proactively flags when skipping a phase introduces risk (e.g. "Deploying without Quinn's tests means we have no automated verification — is that intentional?").

## Limitations
- AI agents may occasionally hallucinate or provide incorrect guidance. Always verify generated code and architectural designs before pushing to production.
- Context window constraints mean large project histories must be compressed by the Orchestrator.
