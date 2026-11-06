# Model migration and prompting

Route for model upgrades, migration planning, model-specific prompting, latest/current/default prompting guidance. First search current official OpenAI docs for exact requested topic and model, then open or fetch relevant official page via available docs or official-domain web capability. Until that search and actual page fetch finish, do not run resolver, open bundled references or rely on guide URL.

## Choose the target before loading more context

- **Explicit model target:** Keep user's exact requested target, including explicitly requested GPT-5.5 or GPT-5.6 migration. Do not run latest-model resolver or substitute newer model. Search and fetch current guidance for that exact model. GPT-5.6 migration must not load GPT-6 guidance or references.
- **Unspecified, latest, current, or default target:** Search and fetch `https://developers.openai.com/api/docs/guides/latest-model` first. Use matching `latest-model.md` metadata only when dynamic migration resolution is needed; then run platform-specific resolver below and keep its returned model and exact guide URLs.
- **Latest/current/default prompting:** Follow dynamic-target route, then use returned prompting guide.
- **Pure model selection:** Use `references/model-selection.md` instead. Do not run resolver.

POSIX shells: invoke resolver through `sh`, without assuming executable bit:

```sh
sh <skill-dir>/scripts/resolve-latest-model-info
```

Windows: CommonJS entry point, Node.js 18 or newer:

```text
node <skill-dir>\scripts\resolve-latest-model-info.cjs
```

If Windows Node runtime is unavailable and `load_workspace_dependencies` is callable, use its returned runtime, retry once. Do not execute extensionless POSIX wrapper directly on Windows.

Do not suppress or redirect resolver stdout. Success: JSON with nonempty `model`, `migrationGuideUrl` and `promptingGuideUrl` fields. If command fails or any required field is missing, retry platform-specific command once, then fall back to current official docs, finally to disclosed bundled references.

## Retrieve only the guidance this request needs

Treat returned guide URLs as opaque: fetch exact URLs; do not derive, substitute or append a model query. Retry exact guide URL if response has only a title or no substantive body.

- Requested migration or upgrade plan: fetch `migrationGuideUrl`.
- Fetch `promptingGuideUrl` only when user asks for prompting guidance or migration requires prompt change. Extract only `## Prompting best practices` through next H2 heading.
- Explicitly named-model prompting: fetch that model's official prompting guidance, extract only `## Prompting best practices` through next H2 heading. Do not load migration reference or run resolver.
- Actual GPT-6 migration or implementation plan: fetch `https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#migration-quickstart`. Specifically requested GPT-6 prompting: fetch `https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#prompting-best-practices`. Read `references/upgrading-to-gpt-6-astra.md` only when fetched official guidance does not resolve needed compatibility gates, scoped code changes, tier-aware routing, validation or other migration-specific judgment. Never load it for docs-only questions on model tiers, family alias, Pro mode, reasoning effort or current guidance that fetched official docs already answer.
- Read `references/prompting-guide.md` only when prompting guidance or prompt changes are needed and current official guidance is unavailable.
- Read `references/upgrade-guide.md` only when current official migration guidance is unavailable. Disclose bundled fallback use.

## Keep implementation changes scoped

Change active model defaults and directly related prompt surfaces only when user requested that work. Update registries, model pickers, capability metadata, routing, pricing or tests only when in scope and current official docs verify relevant values.

Keep each workload's cost, latency, quality, reasoning, tool, endpoint and output-contract role. Do not collapse tiered router into one flagship model, replace intentionally pinned fallbacks, or rewrite historical examples, fixtures, eval baselines, provider comparisons, or unrelated SDK and authentication configuration.

If safe migration needs endpoint, request-schema or tool-handler change, or other work outside requested scope, report exact compatibility blocker and smallest follow-up. Do not silently change behavior.
