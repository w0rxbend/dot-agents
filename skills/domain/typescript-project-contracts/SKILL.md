---
name: typescript-project-contracts
description: Maintain TypeScript workspace build boundaries, Solid UI and Hono backend contracts, and pinned editor-extension or Pixi integration toolchains in worxbend repositories. Use when changing builds, package scripts or cross-package contracts in a worxbend TypeScript workspace.
license: MIT
---

# TypeScript project contracts

Find affected package and runtime from current workspace manifest, scripts, lockfile, tsconfig files, entrypoints and CI. Keep installed framework/version train and module format. Passing root script may cover only one component; map its filters and imports before claiming backend or whole-workspace result.

Read [workspace-boundaries.md](references/workspace-boundaries.md) for pnpm selection, separate Solid/browser and Hono/Node gates, emitted import paths and async lifecycle tests. Read [pinned-integrations.md](references/pinned-integrations.md) for archived coc.nvim extensions and Pixi/OBS projects. Distinct modes; load the relevant one.

Trace changed contract across producer and consumer: configuration key → runtime validation, HTTP response → client decoding, or asynchronous result → reactive owner. Type assertions are assumptions; validate external input at entry. Keep server-only environment variables and credentials out of browser imports and generated bundles.

For `ops-dashboard`, observed root build selects `homelab-ui`; Hono backend builds separately. Backend is currently a service/health scaffold; infrastructure package has no scripts. Source names alone do not establish fleet management, authentication, deployment or test harness. Current source is authoritative.

Scale checks to affected package and behavior. Distinguish typechecking, bundling, route tests, browser lifecycle checks and actual editor/OBS integration. Use existing runners when present; record absent gates accurately. Behavior change may justify focused new test; formatting edit does not need new framework. Keep archived-project maintenance scope unless revival or migration is requested.
