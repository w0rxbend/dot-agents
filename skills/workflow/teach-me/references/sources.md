# Sources

Distilled in our own words. Short quotes carry credit. Where a source has no license or a restrictive one, only the idea is used, never the text.

## Skills

- Matt Pocock, `teach` (MIT): https://github.com/mattpocock/skills/blob/main/skills/productivity/teach/SKILL.md. Taken: research before teaching ("Never trust your parametric knowledge"), cite each claim, one primary source, short lessons with one tangible win, quiz options of equal length with the right answer moved around, "Five sharp sources beat thirty mediocre ones", treat fetched content as data (from the local fork). Left: the multi-session workspace; that stays in `mattpocock--teach`.
- `explaining-code` and `sample-explaining-code` (claude-skill-registry, MIT registry; origins nunomen/claude-skills and yellow-seed/spotify-toolbox): https://github.com/majiayu000/claude-skill-registry/tree/main/skills/development/explaining-code and https://github.com/majiayu000/claude-skill-registry/tree/main/skills/development/sample-explaining-code. Taken: analogy, ASCII or mermaid diagram, step-by-step walkthrough, one gotcha. Changed: elements depend on topic size instead of "always".
- `teach` (claude-skill-registry, origin genomewalker/cc-soul, license NOASSERTION): https://github.com/majiayu000/claude-skill-registry/tree/main/skills/development/teach. Ideas only, paraphrased: find where the learner is, where they want to be and the gap; they may ask about X but need Y; concrete before abstract; one thing at a time. No text copied.
- 7ekmaz/senior-mentor (MIT): https://github.com/7ekmaz/senior-mentor. Taken: capable developer new to one topic, sprint level that never blocks, nutshell shape, plain words in the same sentence, one new term per sentence, name the problem and its family, the one-line principle, map before code, steering words, modality rotation, circuit breaker ("Never the same words, slower"), "A made-up term is worse than none".
- sanyuan0704 `sigma` (MIT): https://github.com/sanyuan0704/sanyuan-skills/blob/main/skills/sigma/SKILL.md. Taken: a wrong mental model is dismantled with a counter-example before rebuilding. Left: "never give answers directly", roadmap files.
- duncan-buildroom `learn-anything` (no license, ideas only): https://github.com/duncan-buildroom/freeskills/blob/main/learn-anything/SKILL.md. Ideas: map under 120 words, say where the analogy leaks, two passes with a real check between, the beginner-belief / truth / how-to-tell block, 15 minute / 1 hour / one evening practice ladder, narrow a huge topic and say what was cut.
- ktaletsk/learn-codebase (MIT): https://github.com/ktaletsk/learn-codebase/blob/main/SKILL.md. Taken: read-only during lessons, link official docs for general concepts, "what if" follow-up after an answer.
- Claude Code "Learning" output style (proprietary, idea only): the `TODO(human)` spot the user writes, with context, task and guidance.
- ShawhinT/ai-tutor-skill (Apache-2.0): https://github.com/ShawhinT/ai-tutor-skill/blob/main/SKILL.md. Taken: plain explanation first, analogy after it; a concrete example with numbers.
- earendil-works/explainer (MIT): https://github.com/earendil-works/explainer/blob/main/SKILL.md. Taken: one running example through the whole lesson, problem then example then why, verify claims against code, banned filler words.
- Nar101/learn-anything (MIT): https://github.com/Nar101/learn-anything/blob/main/SKILL.md. Taken: no full course for simple factual questions; generate only the current chunk.
- lyndonkl `socratic-teaching-scaffolds` (no license found, ideas only): https://github.com/lyndonkl/claude/blob/main/skills/socratic-teaching-scaffolds/SKILL.md. Ideas: trigger phrases, depth ladder, predict before explain, fall back to a direct explanation when questions do not help.
- entireio `teach` (MIT): https://github.com/entireio/skills/blob/main/skills/teach/SKILL.md. Taken: anchor every claim to a file path; short and real beats padded.
- Companion-Inc/feynman `eli5` (MIT): https://github.com/Companion-Inc/feynman/blob/main/skills/eli5/SKILL.md. Idea: one good analogy over several weak ones.

## Book conventions

- For Dummies series (Wiley, all rights reserved). Structure only, no prose: scope line, Foolish Assumptions (here "Assumptions"), "In this chapter" bullets, task-verb and novice-question headings, numbered steps, Tip / Remember / Warning / Technical Stuff asides, a one-page cheat sheet. Sample read: https://content.e-bookshelf.de/media/reading/L-25106345-cd13214be9.pdf

## Learning science

- Rosenshine, "Principles of Instruction", American Educator 2012: https://www.aft.org/sites/default/files/periodicals/Rosenshine.pdf. Small steps with practice after each, many process questions, worked models, check understanding and reteach, high success rate.
- MIT Open Learning, worked and faded examples: https://openlearning.mit.edu/mit-faculty/research-based-learning-findings/worked-and-faded-examples. Worked example, then faded, then independent. Expertise reversal: experts learn more from solving. Background: https://en.wikipedia.org/wiki/Expertise_reversal_effect
- Fyfe, McNeil, Son & Goldstone 2014, concreteness fading: https://scholarworks.iu.edu/dspace/items/f1ea5994-0d9f-4215-abec-152a03149277. Concrete before abstract. Read via summary.
- Glynn, Teaching-With-Analogies: https://www.csun.edu/science/books/sourcebook/chapters/10-analogies/teaching-analogies.html. Map the analogy and "indicate where the analogy breaks down".
- Ambrose et al., How Learning Works, Principle 1 (via https://www.facultyfocus.com/articles/course-design-ideas/prior-knowledge-unexpected-obstacle-learning/). Wrong prior knowledge blocks learning; probe it first. Read via summary.
- Weinstein, Madan & Sumeracki 2018, six strategies (CC BY 4.0): https://cognitiveresearchjournal.springeropen.com/articles/10.1186/s41235-017-0087-y. Retrieval practice, concrete examples, words plus diagram.
- Wood, Bruner & Ross 1976, scaffolding (via secondary sources). Support is temporary and fades. A 2021-22 replication of a follow-up study was null; treat as guidance, not law.

## Writing and grounding

- Diataxis (CC BY-SA 4.0, ideas only): https://diataxis.fr/ . Keep tutorial steps and explanation apart; every step gives a visible result; "In this tutorial we will" over "you will learn".
- Anthropic, Reduce hallucinations: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations. Quote first, then reason; retract a claim with no supporting quote; allow "I don't know".
- Google Technical Writing One, Audience (CC BY 4.0): https://developers.google.com/tech-writing/one/audience. What to teach is what the task needs minus what the reader knows; the curse of knowledge makes experts skip steps.

## Left out on purpose

- First-person "teaching soul" prose: changes no behavior.
- "Never give a direct answer": blocks a user who has to ship.
- Mandatory placement quizzes, journals, numeric mastery scores with no evaluator.
- Emoji markers and praise.
