# Lesson template

Used by `full` and `deep`; `quick` has its own headings in [levels.md](levels.md). Fill sections in the order levels.md gives for the level. Use the headings as written; replace `<...>`. Skip a section the level leaves out. Skip a section that would be empty; never pad one.

Each section is either explanation (why, context) or doing (steps, results). Keep the two apart: put explanation in Big picture and Why, and keep the walkthrough steps lean.

## Callouts

Use four plain-text callouts. No icons, no emoji.

- `> **Tip:**` a shortcut or insight that saves time.
- `> **Remember:**` a fact the user will need again.
- `> **Warning:**` something that breaks, loses data or costs hours.
- `> **Technical stuff:**` detail the user can skip and still finish.

At most one callout per step.

## Writing rules

- Plain words first: "idempotent (safe to run twice; the second run changes nothing)".
- One new term per sentence.
- Headings are tasks or real novice questions: "Sending your first request", "Why does this run twice?".
- Literal language. Cut "simply", "just", "easy", "obviously" and idioms.
- Code comes from the repo or from a cited doc. Mark untested snippets `unverified`.

---

## About this lesson

One line: what the user can do at the end. Start with "In this lesson we will...".

**In this lesson:** 3-5 bullets, one per core idea.

## Assumptions

- Who you assume the reader is: "You write <language> daily and have never used <topic>."
- What they have: tools, versions, access. Name the installed version you read.
- Out of scope: what this lesson leaves out, and where it is covered.

End with: "Wrong assumption? Say which, and I will adjust."

## Big picture

1. The problem this thing solves, in one or two sentences, with a concrete failure it prevents.
2. Its common name, its family, and 2-3 search terms. A made-up name is worse than none.
3. The one principle it rests on, in one line.
4. One analogy. Map its parts to the real parts. Then: "Where this breaks: <the difference>."
5. A map: the pieces and how they connect, as an ASCII diagram (or mermaid when the user's viewer renders it). Under 120 words of text.

When the user named a stack they know, add this table. At most 5 rows. Cite each difference.

| If you know <X> | Here it is | Key difference |
|-----------------|------------|----------------|
| `<X term>` | `<term here>` | <one line, with source> |

## Words you will meet

| Term | Plain meaning | Where you will see it |
|------|---------------|-----------------------|
| `<term>` | <one sentence> | `<path:line>` or doc link |

At most 5 rows. Define further terms inline at first use. Use one name per concept for the rest of the lesson.

## Step by step

Numbered steps, one idea each. Each step follows this shape:

```
### Step <n>: <task verb phrase>

<What to look at or do, 1-3 sentences.>

<code block, with path:line or doc link>

What you will see: <the visible result or output>.
Why: <one or two sentences>.

> **<Callout>:** <optional, one>
```

3-5 steps. Run the walkthrough on the running example from SKILL.md step 3. Trace one real value or request through the code, file by file.

## Why it is built this way (deep only)

Design reasons, with sources: docs, ADRs, commits, issues. Two or three rejected alternatives and why they lost. Constraints that shaped it.

## Common mistakes

Up to 5 rows.

| What beginners believe | What is true | How to tell in practice |
|------------------------|--------------|-------------------------|
| <wrong belief> | <correct fact, with source> | <a check, an error message, a test> |

## Failure modes (deep only)

Where it breaks first under load, bad input or misconfiguration. For each: symptom, cause, fix, source.

## Check yourself

2-3 process questions: predict an output, trace a value, explain why a choice was made, spot the planted bug in a snippet.

- Ask before you explain the answer. Wait for the reply in `full` and `deep`.
- In `full` this is the last section of pass 2. In `deep` it ends every chunk but the last. The reply after the user answers is a short feedback turn, not a new pass.
- Multiple choice: give every option the same length and shape. Vary where the right one sits.
- After the reply, say what was right, fix what was wrong, and ask one "what if" follow-up.

## Faded example (deep only)

The worked example again with 1-3 lines blanked as `____`. The user fills them in. Then one task with no blanks.

## Practice ladder (deep only)

| Rung | Task | Done when | Where people get stuck |
|------|------|-----------|------------------------|
| 15 minutes | <task> | <check> | <trap> |
| 1 hour | <task> | <check> | <trap> |
| One evening | <task> | <check> | <trap> |

When the user practices in their repo, name one spot for them to write and the marker that goes there: `TODO(human): <what to write>`. Give context, the task and a hint. Add the marker only when the user asks; the code is theirs to write.

## Cheat sheet

One screen at most. A table of commands, APIs, config keys or file paths the user will reach for, each with its source. Only items the lesson taught.

## Where to go next

1. One primary source to read next, with a one-line reason.
2. The next question worth asking.

Then close the reply as SKILL.md step 6 says.
