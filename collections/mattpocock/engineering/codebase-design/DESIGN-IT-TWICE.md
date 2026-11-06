# Design It Twice

When user wants alternative interfaces for chosen deepening candidate, use this parallel sub-agent pattern. Based on "Design It Twice" (Ousterhout): first idea unlikely to be best.

Uses vocabulary from [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write user-facing problem-space explanation for chosen candidate:

- Constraints any new interface must satisfy
- Dependencies it relies on, and their category (see [DEEPENING.md](DEEPENING.md))
- Rough illustrative code sketch grounding constraints: not a proposal, only makes constraints concrete

Show this to user, then immediately proceed to Step 2; user reads while sub-agents work in parallel.

### 2. Spawn sub-agents

Spawn 3+ sub-agents in parallel. Each must produce **radically different** interface for deepened module.

Give each sub-agent separate technical brief (file paths, coupling details, dependency category from [DEEPENING.md](DEEPENING.md), what sits behind seam). Brief is independent of Step 1's user-facing explanation. Give each agent different design constraint:

- Agent 1: "Minimize the interface: aim for 1–3 entry points max. Maximise leverage per entry point."
- Agent 2: "Maximise flexibility: support many use cases and extension."
- Agent 3: "Optimise for the most common caller: make the default case trivial."
- Agent 4 (if applicable): "Design around ports & adapters for cross-seam dependencies."

Put both [SKILL.md](SKILL.md) vocabulary and GLOSSARY.md vocabulary in brief, so each sub-agent names things consistently with architecture language and project's domain language.

Each sub-agent outputs:

1. Interface (types, methods, params, plus invariants, ordering, error modes)
2. Usage example for callers
3. What implementation hides behind seam
4. Dependency strategy and adapters (see [DEEPENING.md](DEEPENING.md))
5. Trade-offs: where leverage is high, where thin

### 3. Present and compare

Present designs one at a time so user absorbs each, then compare in prose. Contrast by **depth** (leverage at interface), **locality** (where change concentrates), **seam placement**.

Then recommend: strongest design and why. If elements from different designs combine well, propose hybrid. Be opinionated: user wants strong read, not menu.
