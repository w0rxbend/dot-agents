---
name: strategic-ddd
description: "When splitting or connecting domain models, classify each subdomain as core, supporting, or generic and record the context map the code already has, with one ubiquitous language per bounded context and translation at the boundary. Use when the same word means two things, when wiring two models, or when placing modules and schemas. Use architecture-patterns for tactical DDD inside one context and architecture to choose monolith versus services."
license: MIT
---

# Strategic DDD

Classify the subdomain. Record the contexts the code already has. One language inside each context. Translate at the boundary. Name the relationship before you wire it.

## When to Use

Use when you split a model, connect two models, or decide where a module or a schema lives.

Skip a change that stays inside one model and does not add a term or a dependency. Skip a layering choice that does not cross contexts.

Other skills keep their jobs:

- `architecture-patterns` owns tactical DDD and layering inside one context.
- `architecture` owns monolith versus services, and whether a domain model is worth its cost.
- `designing-apis` owns the wire contract after the relationship is named.
- `grasp-knowledge` owns which type inside one model gets a behavior.

## Before the edit

1. Read [references/rules.md](references/rules.md).
2. List the models this change touches. Quote the terms each model already uses.
3. Classify each subdomain as core, supporting, or generic. Do that before you deepen a model.
4. Record the context map from the modules, schemas, and owners that exist. Label a wished split as not built.

## While editing

- Keep one meaning for each term inside the context you edit. Reject a second meaning.
- Treat the same word in another context as a different concept. Translate it at the boundary.
- Do not import another context's domain types. Cross with a published language, an event, or an anti-corruption translation.
- Name the relationship before you add the call, the event, or the shared type.
- Share a kernel only when it is small, explicit, and jointly owned. Otherwise duplicate the concept.
- Put modules, packages, and schemas on bounded contexts. Do not add a technical layer that mixes two models.

## Stop

Stop when each boundary you touched has one language on each side, a named relationship, and a map that matches the code. Do not redraw the rest of the system.

## Report

For each area you touched: subdomain class, contexts that exist, relationship named, what is translated, and what you refused to share. Mark any split you did not find in the code.

## Limitations

This skill does not design entities, aggregates, or repositories. It does not choose a deployable topology. It does not invent a target map. Cite [references/sources.md](references/sources.md). Conflict winners live only in that file.
