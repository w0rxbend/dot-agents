# Model selection

Route for model recommendations, comparisons, latest/current/default choices when user is not requesting migration or prompting guidance.

1. Search current official OpenAI docs for exact requested workload and any explicitly named model, then open or fetch relevant official page. Current or latest family guidance: `https://developers.openai.com/api/docs/guides/latest-model`.
2. Use any available official docs or first-party-domain search. Read actual source. Do not recommend from search snippet, guessed default or bundled snapshot.
3. Match documented model to user's requested modality, quality, latency, cost, context, workload. Distinguish flagship, balanced, high-throughput, coding, audio, image or other specialized roles only when fetched current docs support it.
4. Keep explicitly requested model or existing target. Cite current official page. State uncertainty about availability, pricing, limits or account access.

Pure model selection needs no migration metadata. **Do not run the resolver.**

Read `references/latest-model.md` only when fetched current official sources cannot answer. Disclose bundled fallback use; it may be outdated.
