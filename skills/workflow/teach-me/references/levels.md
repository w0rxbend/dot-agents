# Levels

Read the section for the chosen level. Read **Expert reader** too when the user knows this exact topic. Section names refer to [lesson-template.md](lesson-template.md).

Length yardstick: one screen is about 400 words, code blocks excluded.

## quick

For: "I need the gist before a meeting", or a small area of code.

- **Research:** 1-3 sources. The files the topic touches, or one official page for the installed version.
- **Headings**, in this order, written as shown. The template is not used.
  1. `Assuming: <one line>`: who you assume the reader is. Never ask.
  2. `In a nutshell`: what it is, in 2 plain sentences.
  3. `Picture it`: one analogy, then one line on where it breaks. No map.
  4. `Must-knows`: 3-5 items, each one sentence with its source.
  5. `Warning`: the biggest trap.
  6. `Minimal example`: a snippet, from the repo when possible.
  7. `Predict this`: one prediction question, with the answer labelled underneath, so the reply never blocks.
- **Length:** one screen, about 300-500 words.
- **Delivery:** one reply.
- **Stop:** after the close. Offer `full` in the Skipped line when the topic is bigger than one screen.

## full (default)

For: "I start on this feature tomorrow and have never seen it."

- **Research:** 3-8 sources. Trace one real call path through the repo when the topic touches it. Read the official docs for the installed version.
- **Sections:** every template section except the deep-only ones. Walkthrough of 3-5 steps.
- **Length:** each pass at most about 900 words.
- **Delivery:** two passes, then a feedback turn.
  1. Pass 1: About this lesson, Assumptions, Big picture, Words you will meet, steps 1-3, then one check question. Stop and wait.
  2. Pass 2: feedback on the answer, the remaining steps, Common mistakes, Cheat sheet, Where to go next, then Check yourself last. Stop and wait.
  3. Feedback turn: what was right, what was wrong, one "what if". This is not a pass.
  The user can say `continue` to skip a wait. A wrong answer in pass 1 triggers the circuit breaker before pass 2.
- **Over length:** cut in this order. Move Words-table terms inline. Cut the map down to the diagram alone. Push step 3 to pass 2.
- **Stop:** after the feedback turn.

## deep

For: "I will own this area. Teach me all of it, including why it is built this way."

- **Research:** 8-15 sources. Everything in `full`, plus design reasons (docs, ADRs, commit messages, issues), rejected alternatives, failure modes, version changes and limits. Up front, research only the plan and chunk 1. Research each later chunk on its own turn.
- **Sections:** every template section, including Why it is built this way, Failure modes, Faded example and Practice ladder. The chunk map sets the order, not the template.
- **Chunks:** 3-5, each at most about 900 words. Say the count up front. Content beyond 5 chunks becomes a follow-up lesson named in Skipped.
  1. Chunk 1: About this lesson, Assumptions, Big picture, Words you will meet, the first worked step.
  2. Middle chunks: the remaining steps, Common mistakes.
  3. Second-to-last: Why it is built this way, Failure modes, Faded example.
  4. Last: Practice ladder, Cheat sheet, Where to go next, the saved-guide offer (SKILL.md step 6).
  With 3 chunks, chunk 2 holds both the middle and the second-to-last content.
- **Delivery:** one chunk per turn. Every chunk but the last ends with a Check yourself question and waits. Support fades: worked step, then faded example, then Practice ladder done alone.
- **Over length:** use the `full` cut order. Push the overflow step to the next chunk.
- **Stop:** after the last chunk.

## Expert reader

Applies only when the user knows this exact topic, not a neighbouring tool. Knowing sbt does not make the user a Mill expert; use sbt as the bridge instead (SKILL.md step 3).

Cut the scaffolding: skip the analogy and the full worked example. Use Check yourself and, in `deep`, Practice ladder as the problems; then Cheat sheet and Where to go next. Experts learn more from solving than from reading solved examples.
