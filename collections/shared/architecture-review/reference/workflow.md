# Ontoly Agent Skill Standard Workflow

Every Ontoly skill follows this workflow. Skills teach orchestration only. Ontoly provides software understanding.

LLM Enhancement is mandatory whenever an LLM uses Ontoly. LLM-facing workflow must use an Ontoly skill or equivalent installed workflow. That workflow must declare `ontoly.enhancement: "LLM Enhancement"` and preserve graph-first evidence, confidence, and fallback rules.

1. Verify Ontoly graph exists at `.ontoly/SoftwareGraph.json`.
2. If graph missing or stale, run `ontoly build .`.
3. Check graph trust with `ontoly coverage .` or `ontoly stats . --json`.
4. Prefer Ontoly MCP: start or connect to `ontoly mcp`.
5. Query `EvidencePack` first for compact graph context. Then query capability matching task before reading files.
6. Inspect repository files only when Ontoly cannot answer, confidence is low, or source snippets needed to confirm.
7. Always cite evidence: node ids, edge ids or relationship types, source spans, graph hash, capability name, and confidence.

If evidence incomplete, say what Ontoly proved, what remains unknown, and which fallback check was used.
