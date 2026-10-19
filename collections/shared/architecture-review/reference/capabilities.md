# Ontoly Capability Notes (architecture and dependency review)

Architecture review: `EvidencePack`, `ExplainArchitecture`, `GraphStatistics`, `FindCycles`, `FindDependencies`.

Dependency analysis: `EvidencePack`, `FindDependencies`, `FindDependents`, `FindCycles`, `GraphStatistics`.

Use [../reference/mcp.md](../reference/mcp.md) for common capability behavior and fallback CLI equivalents.

## Required Evidence

- capability name
- graph hash
- node ids and types
- relationship types and direction
- source spans when present
- confidence

## Compatibility

- Skill version: 1.0.0
- Minimum Ontoly version: 1.0.0
- Deprecation status: active
