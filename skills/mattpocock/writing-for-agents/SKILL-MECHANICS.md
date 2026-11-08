# Skill mechanics

Skill-specific branch of [`writing-for-agents`](SKILL.md): what changes when document is a skill (frontmatter, invocation choice, router skills). Everything else about writing it: universal reference in `SKILL.md`.

## Invocation

Two choices, trading the two loads:

- **Model-invoked** skill keeps a `description`, so agent can fire it autonomously and other skills can reach it. Typing its name still works: model-invocation always _includes_ user reach. Description only ever adds agent discovery, never removes human's. Description is skill's top-level context pointer, forced to stay loaded at all times: permanent context load for discoverability. All-reference model-invoked skill is also one home for shared reference: other skills can invoke it, so reference several skills need lives in one place. Mechanics: omit `disable-model-invocation`; write model-facing description carrying trigger branches (pointer-writing rules in `SKILL.md` apply in full).
- **User-invoked** skill strips description from agent's reach: only human typing its name can invoke it; no other skill can. Zero context load, but spends cognitive load: you are the index that must remember it exists. Mechanics: set `disable-model-invocation: true`. `description` becomes human-facing: one-line summary, trigger lists stripped.

Pick model-invocation only when agent must reach skill on its own, or another skill must. If it only ever fires by hand, make it user-invoked; pay no context load.

Reference shared by two user-invoked skills can live in neither: with no descriptions, neither can fire the other. Push it to plain file outside skill system: external reference any skill can point at.

## Splitting by invocation

Invocation cut of splitting (sequence cut lives in `SKILL.md`). Split off a model-invoked skill when a distinct leading word should trigger it on its own (trigger word you actually use in your prompts), or another skill must reach it. New always-loaded description costs context load, so that independent reach must be worth it.

## Router skills

When user-invoked skills multiply past what you can remember, cure that piled-up cognitive load with a **router skill**: one user-invoked skill naming the others and when to reach for each, so human remembers one skill, not many. It can only hint, never fire them: user-invoked skills have no description, so nothing but the human can reach them.
