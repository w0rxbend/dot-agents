# Phase boundaries

A **phase** is a chunk of work in a session: grilling, implementation, QA. Deliberately fuzzy: a phase ends when you think *"ok, we're done with that"*.

The **phase boundary** is the gap between two phases, the only place for this decision. Mid-phase, no decision: continue, or split remaining work into subagents. Compacting mid-phase makes the agent lose the thread.

## The five options

| Option         | What it does                                                     |
| -------------- | ---------------------------------------------------------------- |
| **Continue**   | Stay in session. No context switch.                              |
| **`/clear`**   | Empty the context window; start from nothing.                    |
| **`/handoff`** | Write a portable markdown file; seed a session anywhere with it. |
| **Subagent**   | Send the task to its own context window; get a report back.      |
| **`/compact`** | Compress this context; seed a fresh session with the summary.    |

## The tree

Work top to bottom at the boundary. First **yes** wins.

**1. Can you continue in this session?** Yes if the next phase needs this one as a **primary source**, or enough [smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone) remains (~150k tokens) to fit the next phase. Grilling → implementation is the standard yes: implementation wants the reasoning verbatim, not a summary. Continue costs nothing and loses nothing; rule it out first.

**2. Is the context irrelevant to what comes next?** Everything here (exploration, decisions, dead ends) disposable? Then **`/clear`**. Cheapest move: instant, returns the whole window. `/clear` isn't terminal either: the old session stays resumable.

A wrong call is one-way. Clear a *relevant* context and the **why** behind what you built is gone; rereading the diff won't bring it back.

**3. Do you need to hand off?** `/handoff` is narrow. Use it only when:

- swapping to a **new harness** (Claude → Codex),
- moving to a **new directory** or repo,
- sending the work to a **colleague**,
- or forking a side task you found **mid-phase** without derailing what you're doing.

That list is the whole clause. `/handoff` buys **portability**: a file that travels. If nothing travels, you don't need it.

**4. Can the task be done AFK?** Scoped tightly enough to run with you away from the keyboard, no steering? Send it to a **subagent**; leave this session untouched. Standard case: automated review. The agent reads the diff and reports without you.

**5. Otherwise, `/compact`.** Relevant context, same harness, same directory, and you must stay in the loop: the tree lands here, often. Pass an instruction (`/compact we're going to QA this area`) so the summary keeps what the next phase needs.

`/compact` is the **default, not the first reach**. It's last because the four questions above are cheaper or more precise. Failure mode when starting here: a fresh session confidently wrong about a decision the summary flattened.

## Primary and secondary sources

Every move except **Continue** turns a **primary source** (the session as it happened) into a **secondary source** (its summary). Same trade every time:

| Source                             | Information | Noise | Room to move |
| ---------------------------------- | ----------- | ----- | ------------ |
| Primary (Continue)                 | Full        | Lots  | Little       |
| Secondary (`/compact`, `/handoff`) | Lossy       | Less  | Lots         |

Hence question 1 first: pay the lossiness only when staying costs more than it saves.

## These are judgement calls

The questions aren't objective: each carries taste, and the same boundary can go two ways on two days. The value is in asking them **in order**, at the boundary, not mid-work.
