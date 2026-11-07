---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview user relentlessly until shared understanding. Map it as **design tree**: each decision branches into decisions that hang off it.

Work tree in **rounds**. **Frontier**: every decision with settled prerequisites, askable _now_ without guessing unheard answers. Ask whole frontier in one round. Number each question, give recommended answer. Wait for user's answers before next round.

Round format:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Word each question so "yes" accepts recommended answer.

Answers reshape tree: settled decisions push frontier outward, unblocking dependent questions. Recompute frontier, ask next round. Question depending on another question still open this round belongs to _later_ round, not this one.

Finding _facts_ is your job, never user's. If frontier question needs environment fact (filesystem, tools, etc.), dispatch sub-agent to find it. Never ask user for anything you could look up yourself. Do not block on it: running exploration is unsettled prerequisite, so only questions downstream of it wait for sub-agent report. Ask rest of frontier now. _Decisions_ are user's: put each to them, wait.

Session done when frontier empty: every design-tree branch visited, nothing silently assumed. Do not act on it until user confirms shared understanding.
