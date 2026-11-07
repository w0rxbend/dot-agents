---
name: interview-me
description: "Clarify an underspecified goal when the missing decision materially affects the result, or conduct an explicitly requested interview. Reuse established preferences and authorization; continue independent work instead of restarting intake."
---

# Interview Me

## When to Use

Apply only when a missing decision would materially change what you build, and you cannot recover it from conversation, established preferences or repository:

- Ask lacks **who** user is, **why** they want it, what **success** looks like, or binding **constraint**, and a wrong guess means building wrong thing
- Request is conventional, not specific ("build me X", "make it faster"), and unpacking it needs guessing
- Two reasonable values conflict (simplicity vs. flexibility, cost vs. speed), user hasn't picked one, and choice changes result
- User explicitly invokes: "interview me", "before we start, are we sure?"

Gap small or reversible? State your assumption and keep working instead of interviewing. To stress-test a plan user already has ("grill me", "stress-test my thinking"), use `mattpocock--grilling` instead.

**When NOT to use:**

- Ask is unambiguous and self-contained ("rename this variable", "fix this typo")
- User explicitly asked for speed over verification
- Pure information requests ("how does X work?", "what does this code do?")
- Mechanical operations (renames, formats, file moves)
- You already have ≥95% confidence; re-read stop condition below before assuming you don't

## Loading Constraints

Needs a live, responsive user. **Do not invoke in non-interactive contexts** like CI pipelines, scheduled runs, `/loop`, or autonomous-loop. There, flag an underspecified ask to user as a blocker instead of guessing.

## The Process

### Step 1: Hypothesize, with a confidence number

Before asking anything, write your best read of what user wants in **one sentence**, plus an honest confidence number (0–100%):

```
HYPOTHESIS: You want a way to answer "how are we doing?" in standup, and "dashboard" was the convention that came to mind.
CONFIDENCE: ~30% — missing: who it's for, what "metrics" means in context, and what success looks like
```

High number, but can't predict user's reactions to your next three questions? Number is wrong. Start at a level you can defend.

Below ~70%, append a brief reason on same line: what's unresolved or missing. Shows user what interview must surface.

### Step 2: Ask one question at a time, each with a guess attached

Format:

```
Q: <one focused question>
GUESS: <your hypothesis for the answer, with the reasoning that produced it>
```

Wait for user's reaction before next question.

Risk: polite user agrees with your guess to be agreeable. Mitigate: be visibly willing to be wrong. Sometimes guess in a direction you expect pushback on.

### Step 3: Listen for "want vs. should want"

Most dangerous answers: user says what a thoughtful answer *sounds like*, not what they want. Watch for:

- Best-practice talk ("I want it to be scalable", "clean architecture") without specifics
- Deferring to convention ("the way most apps do it", "the standard approach")
- Phrases like "I should probably…", "I think I'm supposed to…", "good engineering practice says…"
- Buzzwords as goals: "modern", "scalable", "robust" instead of a specific outcome

When you hear these, ask:

> *"If you didn't have to justify this to anyone, what would you actually want?"*

### Step 4: Restate intent in the user's own words

At high confidence, write back what you now think user wants. Tight (5–8 lines), in their language where possible, confirmable or correctable line by line:

```
Here's what I now think you want:

- Outcome:      <one line>
- User:         <one line — who benefits>
- Why now:      <one line — what changed>
- Success:      <one line — how we know it worked>
- Constraint:   <one line — the binding limit>
- Out of scope: <one line — what we're explicitly not doing>

Yes / no / refine?
```

"Out of scope" is non-negotiable. Half of misalignment is silent disagreement about what is *not* being built.

### Step 5: Confirm — explicit yes, not "whatever you think"

After a full interview, gate is an explicit "yes." If user already authorized you to proceed, or you asked only one clarifying question, take their answer and continue; do not restart intake. In a full interview, these are **not** yes:

- "Whatever you think is best." → Delegation: user lacks 95% confidence too. Re-ask with two concrete options framed as a choice.
- "Sounds good." → Ambiguous. Ask: "Anything you'd refine?" Silence isn't confirmation.
- "Sure, let's go." → Often a polite exit, not an endorsement. Same follow-up.
- Silence followed by "okay let's start." → User gave up on interview, not converged. Stop and ask whether you missed something.

On correction, fold it in and restate. Loop until explicit yes.

### Step 6: Terminal Turn & Stop Rule (CRITICAL)

When user confirms statement of intent with explicit "yes":

1. **Deliver confirmed Statement of Intent.**
2. **Offer downstream paths** (save it to `docs/intent/[topic].md`, draft a spec with `spec-driven-development`, or task planning after spec).
3. **STOP YOUR TURN IMMEDIATELY.** Do NOT invoke tools or start downstream work this turn. Hand control back; user picks next step.

### The 95% Confidence Stop

Done when you can answer yes to:

> *Can I predict the user's reaction to the next three questions I would ask?*

Yes: understanding is shared. Stop interviewing; produce restate. No: not done; ask next question.

Checkable test, not a vibe. Floor: several rounds in and still can't predict? That's information about the ask, not a reason to keep grinding. Stop and tell user: "I've asked X questions and I still can't predict your reactions. Something foundational is missing. Want to step back?"

## Output

Deliverable: a **confirmed statement of intent**, meaning Step 4 restate plus explicit yes from Step 5. Specs, plans, and task lists are downstream; they consume this intent.

If intent must persist (multi-session project, handoff to another collaborator), offer to save it to `docs/intent/[topic].md`. Save only if user confirms.

## Example

**Without `interview-me`:**

```
User:  build me a dashboard for our metrics
Agent: <starts proposing chart libraries and layouts>
```

**With `interview-me`:**

```
User: build me a dashboard for our metrics

Agent:
HYPOTHESIS: You want a way to answer "how are we doing?" in standup, and "dashboard" came to mind because that's the conventional answer.
CONFIDENCE: ~30% — missing: who it's for, what "metrics" are, and what success looks like

Q:     When you say "how are we doing?", who's asking — you alone, the engineering team in standup, or up the chain (e.g., your manager, an exec, a board)?
GUESS: engineering team in standup, because "we" usually scopes that way and standups are where this question gets asked. If it's for execs the metrics and the framing change a lot.

User: It's actually for me. I keep losing track of which experiments are running and what their early signal looks like.

Agent:
Updated read: not a team dashboard at all. It's a personal experiment tracker. Confidence: ~60% — still missing: what "early signal" means and what done looks like.

Q:     Is the gap that you don't know which experiments exist, or that you can't see their results in one place?
GUESS: the second one. You have a list of experiments somewhere, but their results live in five different tools, and reconciling them by hand is what you're tired of.

User: First one actually. I literally don't have a list. They're spread across different docs.

Agent: <continues>
```

## Interaction with Other Skills

- **`idea-refine`**: downstream. If confirmed intent is "I want X but I don't know how to scope it," hand off to `idea-refine` for variations against now-explicit intent.
- **`spec-driven-development`**: downstream. If confirmed intent is concrete ("I want X for Y users with Z success criteria"), hand off to `spec-driven-development` to write it down.
- **`planning-and-task-breakdown`**: two hops downstream (after spec).
- **`doubt-driven-development`**: opposite end of timeline. Interview-me extracts intent before decision; doubt-driven reviews artifacts after. Both catch divergence, at different moments.
- **`source-driven-development`**: orthogonal. Interview-me clarifies what user wants; SDD verifies framework facts. No overlap.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The ask is clear enough" | Can't state user's desired outcome in one sentence now? Ask isn't clear. Run Step 1 before deciding. |
| "Asking too many questions wastes their time" | 4–6 targeted questions cost little. Building wrong thing costs enormous time, and user pays. |
| "I'll figure it out as I build" | Switching costs after code exists are 10x today's. Discovery during implementation is rework. |
| "I should give them several options to pick from" | Options work when user knows what they want and weighs trade-offs. They don't know yet. Options widen search; asking narrows it. |
| "If I attach my guess, I'm leading them" | Leading is the point. Reacting beats generating from scratch. |
| "The user said yes, we're done" | Yes after a vague restate or open-ended "sounds good" is hollow. Restate concretely; re-confirm. |

## Red Flags

- Questions framed as "what would be best practice?" instead of "what do you actually want?"
- Three or more rounds without confidence visibly rising: wrong questions; step back and reframe

## Verification

After applying interview-me:

- [ ] First turn stated explicit hypothesis with confidence number
- [ ] Every confidence number below ~70% had a one-line reason (what's unresolved or missing)
- [ ] Questions asked one at a time, each with agent's guess
- [ ] At least one "what would you actually want if you didn't have to justify it?" probe ran after a sophistication-signaling or convention-signaling answer
- [ ] Concrete restate (Outcome / User / Why now / Success / Constraint / Out of scope) written back to user
- [ ] User confirmed restate with explicit yes (not "whatever you think," not "sounds good," not silence)
- [ ] At stop point, agent could predict reactions to its next three questions
- [ ] On explicit confirmation, turn stopped immediately, no tools invoked, no downstream work started
- [ ] Any handoff to downstream skill (`idea-refine`, `spec-driven-development`) framed by confirmed intent, not original underspecified ask
