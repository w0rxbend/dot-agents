# Sources

Distilled. Not a copy. Read the original before you cite a page.

## Pages

- Martin Fowler, "Bounded Context" (2014), https://martinfowler.com/bliki/BoundedContext.html
- Martin Fowler, "Ubiquitous Language" (2006), https://martinfowler.com/bliki/UbiquitousLanguage.html
- Eric Evans, "Context Mapping with an AI-based Component" (2026), https://www.domainlanguage.com/articles/context-mapping-an-ai-based-component/
- Eric Evans, "AI Components for a Deterministic System" (2025), https://www.domainlanguage.com/articles/ai-components-deterministic-system/
- Olaf Zimmermann, "Strategic Domain-Driven Design", https://github.com/socadk/design-practice-repository/blob/master/activities/DPR-StrategicDDD.md

The DPR page is the practice write-up. It points at Evans for the original patterns and at Vernon for subdomains versus bounded contexts. Those books are not copied here.

## What each source contributes

- Fowler's bounded-context page says a large domain does not get one unified model. Each context has a consistent model. The same word in two parts of an organization can be two concepts, mapped at the boundary. Draw the relationships. Culture and representation both set boundaries.
- Fowler's ubiquitous-language page ties the words in the code to the words used with the people who own the domain. The language changes when it is awkward or ambiguous. A second meaning inside one model will not survive contact with code.
- Evans's 2026 mapping article treats a specific model endpoint as its own context, not "the LLM" in general. A published language can be conformed to. An anti-corruption check rejects outputs outside the local taxonomy. The same integration can conform in one aspect and translate in another. Pick the aspect this change must protect. A cleaner map that shows a split you did not build is not the map.
- Evans's 2025 article separates inventing categories from classifying into categories that already exist. The deterministic system owns the frozen categories. A fresh taxonomy on each call is not a model the rest of the system can join. Constrain the probabilistic output to those categories.
- The DPR page lists the relationship names used here: shared kernel, open host service, published language, customer-supplier, conformist, anti-corruption layer, partnership, and separate ways. It treats them as organizational facts first. Tactic design inside one context is a different activity.

## Winners

- **Map versus wish.** Evans's 2026 article forbids filing a split that the code does not have. An exploratory sketch stays labeled as not the system. This beats a tidier diagram.
- **Subdomain versus context.** Classification (core, supporting, generic) describes the problem. A bounded context is a model boundary that exists in code and ownership. Classifying a subdomain does not create a context and does not authorize a split.
- **Shared kernel.** The DPR summary allows a common kernel of code. This skill allows it only when that kernel is small, explicit, and jointly owned. Otherwise duplicate the concept. Cross-context duplication is not a defect by itself.
- **Published language.** The DPR page lists it beside the relationship patterns. In this skill it is the crossing form an open host or a conformist uses, together with an event or an anti-corruption translation. Naming a published language does not replace naming the relationship.
- **Gray relationships.** Evans notes that one edge can both conform and translate. Name the relationship this change must protect, and say what you did not draw. Do not invent a second context to make the gray go away.
- **Unsplit code.** The DPR page also mentions a big ball of mud as a label. Do not introduce that label as a pattern. If no boundary exists, write that the code is unsplit.
- **Inside one context.** Layers, entities, and aggregates stay with `architecture-patterns`. Which type owns a behavior stays with `grasp-knowledge`. Service topology stays with `architecture`.
