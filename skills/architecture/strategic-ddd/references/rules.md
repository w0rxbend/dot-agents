# Rules

Apply when you split or connect models, or when you place a module, a package, or a schema. Record what exists. Do not draw a target and call it the map.

When two sources disagree, follow [sources.md](sources.md). Do not pick a new winner here.

## Subdomains

- Classify each subdomain as core, supporting, or generic before you deepen the model.
- A core subdomain is the part the business differentiates. Deepen that model.
- A supporting subdomain exists for the core and is not the product. Keep it simpler than the core.
- A generic subdomain is a known problem with a standard model. Keep it thin, or put that standard model behind the boundary.
- A subdomain class is not a bounded context. Classification does not authorize a code split.

## One language

- Keep one ubiquitous language inside a bounded context.
- Reject a second meaning for the same term in that model.
- Use the terms the code and the owners already use. Do not rename them to a glossary the code does not use.
- A term that is awkward for the people who own the context is a model problem. Do not paper over it with a synonym in the same context.

## Boundaries

- The same word in two contexts is two concepts. Translate it at the boundary.
- Do not import another context's domain types.
- Cross with a published language, an event, or an anti-corruption translation.
- The translation owns both directions that the call needs. The caller does not see the foreign type.
- A probabilistic or third-party component whose language differs is its own context. Constrain its output to the deterministic model's terms at the boundary.
- Do not let a prompt, a score, or a vendor type become a term in the core language unless the existing code already conforms and the map says so.

## Relationships

Name the relationship before you wire it. Use one of these, and only when the code and the ownership match:

- Partnership: both sides fail delivery together, and they plan the interface together.
- Customer-supplier: the downstream context can negotiate what the upstream provides.
- Conformist: the downstream takes the upstream model as-is and cannot change it.
- Anti-corruption layer: the downstream translates so the upstream model does not enter.
- Open host service: one published protocol serves many consumers.
- Shared kernel: a small, explicit part, jointly owned.
- Separate ways: the contexts do not integrate. Do not add the wire.

Do not name customer-supplier when the downstream cannot change the upstream. Do not name partnership because two teams talk. Do not add a relationship the code does not have in order to tidy the map.

## The map

- Record the context map from the code and the ownership that exist.
- Do not draw a split that has not been made.
- Label an exploratory sketch as not the system. Do not file it as the map.
- If the code has no boundary, write that. Do not invent contexts to hide the tangle.
- A gray relationship gets the one name this change must protect. Say what you left out.

## Sharing and placement

- Share a kernel only when it is small, explicit, and jointly owned. Otherwise duplicate the concept per context.
- Duplication across contexts is allowed. A shared type that neither owner can change alone is not a kernel.
- Place modules, packages, and schemas on bounded contexts.
- A technical layer inside one context may stay. A layer that mixes two contexts' domain types may not.
- Do not move a schema onto a shared database module so that two languages import one row type.
