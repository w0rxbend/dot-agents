---
name: typescript-project-contracts
description: Maintain TypeScript workspace build boundaries, Solid UI and Hono backend contracts, and pinned editor-extension or Pixi integration toolchains in worxbend repositories.
license: MIT
---

# TypeScript project contracts

Identify the affected package and its runtime from the current workspace manifest, package scripts, lockfile, tsconfig files, entrypoints, and CI. Preserve the installed framework/version train and module format. A successful root script may cover only one component; map its filters and imports before claiming a backend or whole-workspace result.

Read [workspace-boundaries.md](references/workspace-boundaries.md) for pnpm selection, separate Solid/browser and Hono/Node gates, emitted import paths, and async lifecycle tests. Read [pinned-integrations.md](references/pinned-integrations.md) for archived coc.nvim extensions and Pixi/OBS projects. These are distinct modes; load the relevant reference.

Trace the changed contract across its producer and consumer: configuration key → runtime validation, HTTP response → client decoding, or asynchronous result → reactive owner. Type assertions describe assumptions; validate external input where it enters. Keep server-only environment variables and credentials outside browser imports and generated bundles.

For `ops-dashboard`, the observed root build selects `homelab-ui`; its Hono backend has a separate build. The backend is currently a service/health scaffold, and the infrastructure package has no scripts. Source names alone do not establish fleet management, authentication, deployment, or a test harness. Current source remains authoritative.

Choose checks proportional to the affected package and behavior. Distinguish typechecking, bundling, route tests, browser lifecycle checks, and actual editor/OBS integration. Use existing runners when present; record absent gates accurately. A behavior change may justify a focused new test, while a formatting edit does not require a new framework. Preserve archived-project maintenance scope unless revival or migration is requested.
