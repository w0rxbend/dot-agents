# Upgrading to GPT-6 Astra

Use when user asks to migrate an existing OpenAI API integration, repository, prompt stack, agent, model router or model picker to GPT-6 Astra.

Default explicit target: `gpt-6-astra`. Verify `gpt-6` family alias's currently documented routing and availability before using it. Not every old model usage is an Astra candidate: keep Terra for balanced work, Luna as primary faster or cheaper model.

Before changing code, get current live GPT-6 model guidance via already-callable official docs search and fetch, or immediately via official-domain web search and fetch:

https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md

For prompt changes, also read only `## Prompting best practices` section from:

https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#prompting-best-practices

Live docs are canonical for current model IDs, parameters, limits, pricing and feature availability. Skill-specific workflow below covers repository inspection, scope preservation and validation. Fallback after it holds all non-prompting guidance, including access notices, examples, caveats and `## Migration quickstart`. Full prompting section: `references/prompting-guide.md`. When refreshing, keep all guide content unless website-specific rather than useful to skill; record any omission. Strip website metadata and component markup, keep their readable content. Resolve site-relative links against `https://developers.openai.com`, section-only links against canonical model-guide URL above.

## Core principle

No blind model-string replacement.

First preserve each usage site's behavior, latency class, cost class, reasoning level, endpoint contract, tool semantics, cache behavior and output contract. Then make smallest safe migration. Adopt new GPT-6 capabilities only when they solve a measured problem or user explicitly asks.

Model upgrade alone does not authorize adding reasoning fields, changing request schemas or rewriting tests. Set supported reasoning effort explicitly to preserve source model's effective behavior. Verify omitted defaults; do not guess.

## Migration posture

Classify every usage site before editing:

1. `simple Astra migration`
   - One flagship model usage.
   - Same endpoint and request shape can stay.
   - Reasoning effort explicit, or old effective value known.
   - No cache, vision, file, tool or parser behavior needs implementation changes.
2. `tier-aware family migration`
   - Repository exposes multiple model roles, model choices, fallbacks, routers, pricing data or capability metadata.
   - Map each role to Astra, Terra or Luna; do not replace everything with Astra.
3. `compatibility migration`
   - Safe move needs parameter, endpoint, cache, state, tool-loop or multimodal-detail changes.
   - Make these changes only when implementation work is inside user's requested scope. Otherwise report exact blocker and smallest follow-up.
4. `prompt migration`
   - API shape can stay, but representative traces show prompt-specific regression.
   - Make surgical prompt edit tied to that failure. Do not rewrite a working prompt stack wholesale.
   - If task is updating prompting guidance, edit only directly tied prompt surface. Do not modify runtime request code, model schemas or tests unless prompt change requires it.
5. `optional feature adoption`
   - Pro mode, persisted reasoning, explicit caching, Programmatic Tool Calling or multi-agent behavior added deliberately.
   - Keep separate from baseline migration so its effect is measurable.
6. `leave unchanged`
   - Historical examples, documentation about old models, snapshots, fixtures, eval baselines, comparison code, intentionally pinned fallbacks, unsupported providers or ambiguous usages.

If intent is unclear, prefer leaving usage unchanged and listing it for confirmation over silently changing its role.

## Inventory before editing

Search beyond literal model IDs. Inventory:

- model strings, aliases, environment variables, CLI flags, config defaults and deployment settings;
- SDK calls to Responses, Chat Completions, Batch or provider adapters;
- reasoning settings, token budgets, sampling settings and latency timeouts;
- function tools, hosted tools, structured outputs, response parsers and replay logic;
- system, developer, user and tool-description prompts tied to each usage;
- routers, fallbacks, model allowlists, enums, regexes, validation schemas and capability maps;
- model picker UI, display labels, descriptions, context limits, pricing metadata and provider catalogs;
- prompt-cache keys, retention options, stable-prefix construction and cache metrics;
- image, PDF, file, OCR and computer-use inputs;
- tests, fixtures, snapshots, evals, analytics labels, billing tables and docs.

When changing a default model, search every active default surface: runtime config, environment/config files, setup docs, tests, CLI defaults, deployment examples. Update them together.

Per usage site, record:

- source model and why it appears used;
- endpoint and SDK/client surface;
- prompt surface;
- effective reasoning effort, including defaults;
- latency, cost, context and quality role;
- tools, structured outputs, caching, state replay and multimodal inputs;
- downstream parsers or user-visible contracts;
- migration class and validation plan.

## Choose the target model by role

Starting map; validate against repository's workload:

| Existing role | Starting target | Reason |
| --- | --- | --- |
| GPT-5.6 Sol or an earlier flagship | `gpt-6-astra` | Astra is flagship-equivalent tier. |
| Balanced quality, latency, and cost | `gpt-5.6-terra` | Terra is balanced option. |
| Faster or cheaper work, classification, extraction, routing, high-volume, or strict-latency route | `gpt-5.6-luna` | Luna is primary speed and cost option. |
| GPT-4.1 or GPT-4o latency-sensitive flow | Start with Luna; evaluate Terra or Astra if quality requires it | Flagship replacement can change latency and cost materially. |
| Reasoning-heavy or hardest quality-first flow | Start with Astra at old effective effort | Preserve reasoning contract before tuning. |
| Router, fallback, or model picker | Add family by role | Do not collapse multi-model design into Astra. |
| Third-party or provider-specific model | Leave unchanged unless user explicitly requests provider migration | Model-name similarity is not a safe mapping. |

Limits to check in live docs:

- Each model's context window and maximum output.
- Long-context pricing thresholds per route.
- Token pricing for GPT-6.

Do not invent prices, limits or capability flags. Fetch from current docs before updating registry or UI.

For model pickers and registries, keep existing model entries by default. Add GPT-6 Astra, keep existing Terra and Luna options unless user explicitly asks to replace or remove them. Do not invent pricing, context limits, capabilities or metadata unless confirmed from canonical docs.

If using `gpt-6` alias, record returned `response.model` during validation. Do not assume alias and explicit Astra slug appear identically in dashboards, rate-limit configuration, analytics or billing metadata.

## Structured outputs, parsers, and tool contracts

Keep output contracts explicit:

- preserve JSON schemas, required fields, enums, refusal handling, parser expectations;
- preserve tool names, parameter schemas, call IDs, retry behavior;
- keep citations, evidence fields or native artifacts when downstream consumers need them;
- validate final answer still satisfies contract, not merely that a tool call succeeded.

Do not fix failing migration by weakening schema, deleting required behavior, removing routes, dropping tools or changing business logic unless user explicitly asked for that product change.

## Prompt migration judgment

Once model and API baseline work, run representative traces before editing prompts. Change prompts only for measured failures. When prompt changes are needed, read `references/prompting-guide.md` for exact canonical prompting section.

## Upgrade workflow

1. Fetch current live GPT-6 docs. Fetch Prompting Best Practices section only when prompt changes are needed.
2. Inventory every usage site plus adjacent prompt, config, registry, parser and test surfaces.
3. Classify each usage by role and migration class.
4. Pick Astra, Terra or Luna by existing workload's role.
5. Preserve old effective reasoning effort explicitly when supported. For unsupported settings, follow canonical migration guidance.
6. Run compatibility gates:
   - endpoint and SDK support;
   - Chat Completions plus function tools;
   - cache topology and cache fields;
   - context length and long-context cost;
   - image, PDF, and file detail;
   - structured outputs and parsers;
   - Responses state replay and tool continuation;
   - mixed-model routing and unsupported new fields.
7. Apply smallest safe model, config, registry and prompt changes.
8. Do not add optional Pro, persisted reasoning, PTC, explicit caching, async tools or multi-agent behavior unless needed and measurable.
9. Run existing tests and representative evals.
10. Report changed, unchanged, blocked and confirmation-needed sites separately.

## Validation matrix

Prefer controlled comparison:

1. old model + old prompt + old settings;
2. GPT-6 target + same prompt + preserved effective reasoning;
3. GPT-6 target + same prompt + one lower supported effort;
4. GPT-6 target + smallest prompt or API fix a measured failure requires;
5. optional feature treatment, isolated from baseline.

Measure what matters for workflow:

- task success and user-visible quality;
- structured-output validity and parser success;
- tool choice, tool arguments, retries, loop count and completion rate;
- TTFT, end-to-end latency, timeout rate and concurrency behavior;
- input, output, reasoning, cached and cache-write tokens;
- total cost per successful task;
- long-context, compaction and replay behavior;
- image/PDF token use and visual/OCR accuracy;
- completeness, preserved behavior, citations and validation evidence.

For routers and pickers, test at least one representative workload per role. Verify cheapest or fastest tier is not accidentally used for quality-critical work, and Astra is not accidentally used for every workload.

## Required final report

Return:

- `Current usage inventory`: each model site, endpoint, role, prompt surface and old effective reasoning.
- `Target mapping`: Astra, Terra, Luna, unchanged or confirmation-needed, with reason.
- `Changes made`: model strings, reasoning settings, prompts, registries, metadata, tests and API-shape changes.
- `Compatibility checks`: Chat Completions/tools, caching, state replay, multimodal detail, context/cost, schemas and mixed-model routing.
- `Prompt changes`: each surgical edit and the failure mode it addresses.
- `Validation`: commands, evals, traces, before/after measurements and remaining gaps.
- `Unchanged sites`: historical, pinned, ambiguous or intentionally role-specific usages.
- `Blockers and open questions`: exact issue, why guessing is unsafe, smallest next step.

Never call migration complete merely because model strings changed. Complete only when affected behavior and contracts are validated, or remaining gaps are stated explicitly.

## Introduction

GPT-6 Astra is our most intelligent model yet, with state-of-the-art performance in computer use, browsing, software engineering, science, and professional work. It excels at carrying out multistep workflows across code, browsers, and professional software. In <a href="https://openai.com/index/gpt-6-astra/" target="_blank" rel="noopener noreferrer">several evaluations</a>, Astra achieves stronger results while using substantially fewer output tokens—delivering a lower estimated API cost per task than earlier models despite its higher per-token pricing.

GPT-6 Astra is also our most aligned model yet. It excels at exercising care, respecting task boundaries, and communicating transparently. When instructions leave room for interpretation, it uses the context it has to fill in routine gaps and asks focused questions when the answer could change the outcome. It incorporates new requirements, changes course when asked, and answers side questions without losing track of the broader task.

To build with Astra, set `model` to `gpt-6-astra` in a [Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses) request.

## What's new

- **Async tool calling:** GPT-6 Astra can continue reasoning, call other tools, or answer independent parts of a request while your application runs a tool. Set `async: true` on a function or custom tool and return its result when ready using the original `call_id`. Your application still executes the tool and manages pending work. See [Async tool calling](https://developers.openai.com/api/docs/guides/async-tool-calling) for basic usage and a developer-defined wait-tool pattern.
- **Mid-turn steering:** Send additional user instructions while GPT-6 Astra is working, such as a correction or a change in requirements. Over a WebSocket connection, the Responses API preserves completed work and includes the update in a continuation. See [Mid-turn steering](https://developers.openai.com/api/docs/guides/steering) for the event flow and tool-result handling.
- **Change reasoning mid-conversation while preserving cache:** Add a `configuration_update` input item to increase reasoning effort for difficult work or reduce it for routine follow-ups without rewriting the original prompt prefix. The updated reasoning effort applies until another `configuration_update` input item overrides it. See [Change reasoning mid-conversation](https://developers.openai.com/api/docs/guides/reasoning#change-reasoning-mid-conversation) for examples and compatibility.
- **Misalignment monitoring:** As part of our <a href="https://openai.com/index/path-to-astra/" target="_blank" rel="noopener noreferrer">strengthened safeguards</a> for GPT-6 Astra, our systems asynchronously monitor for misalignment and trigger alerts when necessary. See [Misalignment monitoring](https://developers.openai.com/api/docs/guides/safety-checks/misalignment-monitoring) for more information.
- **Limitations:** GPT-6 Astra does not support the `none` reasoning effort. [Fast mode](https://developers.openai.com/api/docs/guides/fast-mode) is unavailable for GPT-6 Astra with EU data residency.

GPT-6 Astra also supports the existing API capabilities available with GPT-5.6, including [computer use](https://developers.openai.com/api/docs/guides/tools-computer-use), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [streaming](https://developers.openai.com/api/docs/guides/streaming-responses), [Programmatic Tool Calling](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling), [multi-agent orchestration](https://developers.openai.com/api/docs/guides/responses-multi-agent), [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), [persisted reasoning](https://developers.openai.com/api/docs/guides/reasoning#preserve-reasoning-across-calls), [compaction](https://developers.openai.com/api/docs/guides/compaction), and [pro mode](https://developers.openai.com/api/docs/guides/reasoning#reasoning-mode).

## Migration quickstart

### Migrate with Codex

Codex can apply the recommended changes in this guide with the <a href="https://github.com/openai/skills/tree/main/skills/.curated/openai-docs" target="_blank" rel="noopener noreferrer">OpenAI Docs skill</a>.

```text
$openai-docs migrate this project to GPT-6 Astra
```

To use this skill in other coding agents, download it from the <a href="https://github.com/openai/skills/tree/main/skills/.curated/openai-docs" target="_blank" rel="noopener noreferrer">OpenAI skills repository</a>.

### Update API and model parameters

Set `model` to `gpt-6-astra`, then check the following:

- **Reasoning effort:** If you currently use `none` or `minimal`, start with `low` and compare results. Otherwise, preserve your current effective [reasoning effort](https://developers.openai.com/api/docs/guides/reasoning#reasoning-effort). Use `reasoning.effort` in Responses or `reasoning_effort` in Chat Completions.
- **Tool calling:** Use the [Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses#migrating-from-chat-completions). GPT-6 Astra supports Chat Completions, but tool calling requires Responses.
- **Unsupported parameters:** Remove `temperature`, `top_p`, and `top_logprobs`. For Chat Completions, also remove `logprobs`. For Responses, remove `message.output_text.logprobs` from `include`.
- **Fast mode:** For EU data residency, use Standard processing. GPT-6 Astra does not support `service_tier: "fast"` or `service_tier: "priority"` with EU data residency. Fast mode for GPT-6 Astra does not include a latency SLA. See [Fast mode compatibility](https://developers.openai.com/api/docs/guides/fast-mode#is-fast-mode-compatible-with-data-residency-zero-data-retention-and-a-baa).
- **Changing reasoning effort:** If your application changes effort between responses, use `configuration_update` items in standard, single-agent requests. Keep request-level `reasoning.effort` unchanged to preserve the prompt prefix for caching. Check the [compatibility limits](https://developers.openai.com/api/docs/guides/reasoning#change-reasoning-mid-conversation) before adopting this feature.
- **Prompt caching:** When migrating from GPT-5.5 or earlier, replace `prompt_cache_retention` with `prompt_cache_options.ttl` set to `"30m"`. Review the [prompt caching changes](https://developers.openai.com/api/docs/guides/prompt-caching#summary-of-model-differences), including cache boundaries and cache-write billing.
- **Unnecessary approval pauses:** If you run into issues where the model keeps asking for approval before proceeding, use the [initiative and follow-through guidance](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#initiative-and-follow-through) to prompt for more autonomous execution. See the rest of [Prompting best practices](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#prompting-best-practices) for guidance on instruction following, writing style, subagent delegation, and testing.
