# Codex self-knowledge

Manual-first route. Only for genuinely broad Codex setup, orientation, customization, troubleshooting, local-state guidance or system-map synthesis across skills, plugins, MCP, hooks, `AGENTS.md`, automations and product surfaces. Mixed Chat/Work/Codex comparisons go to `official-docs.md`.

Narrow Codex docs questions (single feature such as Codex Goals, specific setting, documented behavior, exact error, requested page citation): search exact official topic first, then actually open or fetch page via available docs or official-domain web capability, before inspecting local files or bundled references. Do not fetch manual, read bundled references, inspect local config or caches, or widen targeted lookup into broad product synthesis. Current or latest model questions follow model-selection route.

## Start with the manual

Reuse manual and outline paths already set in same thread if both stay usable and current. Refresh before relying on a path fetched over about a day ago, from another thread or uncertain source, or missing likely-current information.

Otherwise run bundled manual helper first. Skip without probing only when policy explicitly makes session read-only, shell execution unavailable, or every allowed temp cache location unavailable. Workspace-only write access is not enough: helper needs allowed writable temp cache. Guessed sandbox restriction is not evidence helper is unavailable.

Resolve `<skill-dir>` to installed skill directory, then run:

```bash
node <skill-dir>/scripts/fetch-codex-manual.mjs
```

Helper picks first usable cache location automatically (skips dirs not owned by current user or world-writable; never loosen permissions to make one usable), in this order:

1. `$TMPDIR/openai-docs-cache`
2. `%TEMP%\openai-docs-cache`
3. `%TMP%\openai-docs-cache`
4. `/private/tmp/openai-docs-cache`
5. `/tmp/openai-docs-cache`

Explicit override only when allowed cache must be picked manually:

```bash
node <skill-dir>/scripts/fetch-codex-manual.mjs --cache-dir <cache-dir>
```

On Windows, `%TEMP%` and `%TMP%` are discovered automatically; typical PowerShell override is `$env:TEMP\openai-docs-cache`. Helper handles configured HTTP(S) proxies, falls back to `curl` when needed. Do not require POSIX-only environment prefix or unneeded cache override.

Helper verifies current source; returns manual path, outline path, freshness status, heading outline. Use outline to find relevant headings and line ranges; read or search only returned manual and outline paths. Do not inspect unrelated repositories, caches, source trees or local state to establish public Codex product claim.

If asked whether manual is current enough to rely on now, rerun helper when allowed temp cache is available; answer from its reported status and returned paths.

## Fill only genuine documentation gaps

If manual answers a claim, stop retrieving sources for it; its official source pages and known anchors suffice as citations. Continue user's broader task when docs lookup was only one dependency.

If helper was legitimately skipped, actually fails, or fresh manual lacks a material or likely-current claim, do narrowest official follow-up: search exact topic via available docs or approved-domain web capability, then open or fetch clearly relevant official result. Page-specific citation can justify same narrow follow-up.

Undocumented Codex term, mode, acronym or exact error: first check adjacent manual terminology; map to closest documented concept when possible. If exact term is material or likely current, do one targeted official search-and-fetch. If still undocumented, say so. Do not expand into internal knowledge bases, private source trees, guessed roadmap details or account-specific workarounds.

If official docs conflict with callable capability verified in current session, state conflict explicitly and prefer verified behavior for this environment. Otherwise resolve unsupported claims with bounded uncertainty, or route user to support, an administrator or product feedback.

## Choose the smallest matching Codex surface

- Prompt or thread context: one-off task constraints.
- Repository `AGENTS.md`: durable team conventions, commands, verification expectations; nested files apply more specifically in their subtree.
- Project `.codex/config.toml`: trusted-repository settings, including sandbox, MCP, hooks, model and reasoning defaults.
- Global config or global guidance: personal defaults across repositories.
- Skill: reusable workflow, optionally with focused references or scripts.
- Plugin: installable bundle of skills, tools, commands, MCP configuration, hooks, apps, assets or related metadata.
- MCP server or app connector: authorized live external data and actions. For private Google Docs, Calendar, Slack, GitHub, Notion or similar workspace data, use authenticated connector, not web search or memory.
- Automation: scheduled checks, reminders, monitors or follow-ups; existing-thread heartbeat when continuity matters.
- Hook: mechanical enforcement around lifecycle events, tool calls, commands or edits.

Split requests mixing one-off, durable, repository-scoped and recurring behavior; do not force them onto one surface. Example: "always do this, but only for this PR" goes in current prompt or thread unless user explicitly wants persistence or enforcement.

Surface recommendation: state what to use, why it fits, what to avoid, supporting manual or official docs.

Product surfaces: distinguish terminal-first CLI work, editor-attached IDE work, desktop planning or review, hosted cloud execution, in-app browser testing, user's existing Chrome session, desktop Computer Use. Keep `config.toml` defaults, `requirements.toml` constraints and managed or administrator policy separate. API key does not establish ChatGPT, Codex cloud, connector or account access.

Plugin or app failures: before inferring cause, check installed bundle, enabled state, connector authorization, MCP setup, restart or new-thread expectations, workspace policy. Route billing, entitlements, undocumented rollout labels and unsupported access paths to right support or administrative owner.

Memory may supply user preferences or context; explicit prompt instructions beat it. Memory is not a source for current external facts. Sandbox or network denials need narrowly scoped escalation with clear justification. Destructive commands, writes outside workspace and broad access changes need explicit approval.

Official anchors for page-specific citations: `concepts/customization#agents-guidance`, `concepts/customization#skills`, `plugins/build#plugin-structure`, `concepts/customization#mcp`, `config-advanced#hooks`, `app/automations#thread-automations`, `config-reference#configtoml`.
