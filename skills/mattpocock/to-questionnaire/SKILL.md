---
name: to-questionnaire
description: Turn a decision you can't fully answer into a questionnaire for someone else to fill in.
disable-model-invocation: true
---

Turn what user can't answer alone into **questionnaire**: Markdown document one person fills in async, or user and recipient fill out together in a meeting. Recipient holds knowledge user lacks; questionnaire pulls it out.

**Grill the send, not the subject.** Interview user only about the _send_, which they can always answer: who it goes to, what they need back. Document questions then target the **gap** between what recipient knows and what user needs.


1. **Who is it going to?** In one exchange, ask recipient's role, expertise, and relationship to user. Sets tone and how much context questionnaire must carry. Done when you know who recipient is and what they know that user doesn't.

2. **What do you need back?** In one exchange, ask which specific decisions or facts user can't resolve alone and needs from this person. Done when you have concrete list of what user must walk away able to do or decide.

3. **Write the questionnaire.** Draft questions aimed at gap from steps 1–2, following Document structure below. Write to `to-questionnaire-<slug>.md` in current directory (slug from topic); report path. Done when file exists and a question covers every item user named in step 2.

## Document structure

Frame document as **discovery questionnaire**. Order questions most-important-first. Past a handful of questions, group them under `##` headings by theme. Use template below.

<questionnaire-template>

# <Questionnaire title>

**Purpose:** why this questionnaire exists and the decision riding on it.

**From:** <the user>, **To:** <the recipient>, **How your answers will be used:** <where they go>

## Context

One paragraph orienting a recipient who wasn't in the user's head. Enough to answer well, not a page.

## How to answer

Deadline and rough effort. Partial answers and "I don't know" are useful: flag anything you're unsure of rather than skipping it.

## <Theme heading>

One `##` section per theme. Under each, its questions, most-important-first. Every question is one idea, never compound, with an answer stub directly beneath, and a one-line _why this matters_ only where the question could be misread or invite a throwaway answer.

<question-example>
### What load is the system expected to handle at launch?

_Why this matters: it decides whether we provision for burst traffic now or defer it._

>
</question-example>

## Anything else?

A closing catch-all: anything we didn't ask that we should know?

</questionnaire-template>
