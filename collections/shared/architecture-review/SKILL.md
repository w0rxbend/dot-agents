---
name: architecture-review
description: Graph-backed architecture and dependency review with the Ontoly CLI/MCP - module boundaries, package topology, service ownership, dependents, cycles and architectural risk, cited by graph node ids. Use only when the Ontoly CLI or MCP server is available in the repository; for tool-agnostic design trade-offs use architecture.
license: AGPL-3.0-only
compatibility: Portable Agent Skills format; requires Ontoly CLI and MCP-capable or
  CLI-capable coding agent.
metadata:
  ontoly.skill.version: 1.3.3
  ontoly.min.version: 1.3.3
  ontoly.capabilities: ExplainArchitecture, GraphStatistics, FindCycles, FindDependencies,
    FindDependents, EvidencePack
  ontoly.category: architecture
  ontoly.enhancement: LLM Enhancement
  ontoly.deprecated: 'false'
source_repo: 0xsarwagya/ontoly
source_type: community
source: community
date_added: '2026-09-21'
risk: unknown
---

# Architecture Review (Ontoly)

## When to Use

- Ontoly available: `ontoly` on PATH, or `ontoly mcp` server connected
- Questions such as: "What are the main packages and services?", "Which modules depend on X?", "What would a change to X affect?", "Are there dependency cycles?", "Who owns this request path?"

If Ontoly not installed, do not use this skill. Use `architecture` for design trade-offs, ordinary code search for dependency questions.

## Required Workflow

Follow [the shared Ontoly workflow](reference/workflow.md). When task needs detail, also read [graph evidence rules](reference/graph.md), [MCP usage](reference/mcp.md), [best practices](reference/best-practices.md) and [fallback rules](reference/fallbacks.md).

In short:

1. Ensure `.ontoly/SoftwareGraph.json` exists. If missing or stale, run `ontoly build .`.
2. Check graph trust with `ontoly coverage .` or `ontoly stats . --json`.
3. Query `EvidencePack` first, then capabilities for mode below.
4. Inspect repository files only when Ontoly cannot answer, confidence is low, or source quote needed.

## Modes and Capabilities

| Mode | Question shape | Capabilities, in order |
|------|----------------|------------------------|
| Architecture review | Boundaries, topology, ownership, risk | `EvidencePack`, `ExplainArchitecture`, `GraphStatistics`, `FindCycles`, `FindDependencies` |
| Dependency analysis | "What depends on X / what does X use / impact of changing X" | `EvidencePack`, `FindDependencies`, `FindDependents`, `FindCycles`, `GraphStatistics` |

Required evidence fields: [capability notes](reference/capabilities.md).

## Output Contract

Return:

- answer or plan
- capabilities invoked
- graph evidence: node ids, edge types, source spans, graph hash when available
- confidence: high, medium, or low
- fallback reason if repository files were inspected

Templates: [architecture review](templates/architecture-review.md), [dependency review](templates/dependency-review.md). Worked examples: [examples](examples.md).

## Boundaries

Do not implement compiler, query, MCP, SDK, or business logic in skill. Separate graph facts from inference.

## Learn More

- Documentation: https://ontoly.xyz/docs
- Ontoly Agent Skills: https://ontoly.xyz/skills
