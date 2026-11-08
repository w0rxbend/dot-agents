# Architecture Review and Dependency Analysis Examples

Every example is graph-first and MCP-first: follow shared workflow, run capabilities in listed order, inspect files only if graph evidence missing.

| Repository | Questions | Capabilities invoked | Expected evidence | Expected answer |
| --- | --- | --- | --- | --- |
| Ovok Core | Trace the login flow through the NestJS auth controller. | `EvidencePack`, `ExplainArchitecture`, `GraphStatistics`, `FindCycles`, `FindDependencies` | controller, route, service, dependency-injection edges; graph hash; confidence. | Concise architecture summary: graph-backed boundaries, risks, evidence node ids, confidence. |
| Ghost | Explain the package entrypoint and public API surface. | `EvidencePack`, `ExplainArchitecture`, `GraphStatistics`, `FindCycles`, `FindDependencies` | package, exports, functions, interfaces; graph hash; confidence. | Concise architecture summary: graph-backed boundaries, risks, evidence node ids, confidence. |
| durable-local | Find storage APIs and consumers before a refactor. | `EvidencePack`, `ExplainArchitecture`, `GraphStatistics`, `FindCycles`, `FindDependencies` | functions, interfaces, dependents, configuration; graph hash; confidence. | Concise architecture summary: graph-backed boundaries, risks, evidence node ids, confidence. |
| 0xsarwagya | Summarize workspace packages and package dependencies. | `EvidencePack`, `ExplainArchitecture`, `GraphStatistics`, `FindCycles`, `FindDependencies` | workspace, packages, framework nodes, dependency edges; graph hash; confidence. | Concise architecture summary: graph-backed boundaries, risks, evidence node ids, confidence. |
| Innosphere | Identify application modules and request ownership. | `EvidencePack`, `ExplainArchitecture`, `GraphStatistics`, `FindCycles`, `FindDependencies` | controllers, modules, routes, services; graph hash; confidence. | Concise architecture summary: graph-backed boundaries, risks, evidence node ids, confidence. |

## Dependency-Analysis Mode

For "what depends on X / what does X depend on" questions, use dependency order instead:

| Repository | Questions | Capabilities invoked | Expected evidence | Expected answer |
| --- | --- | --- | --- | --- |
| durable-local | Find storage APIs and consumers before a refactor. | `EvidencePack`, `FindDependencies`, `FindDependents`, `FindCycles`, `GraphStatistics` | functions, interfaces, dependents, configuration; graph hash; confidence. | Deterministic dependency report: direct/transitive edges, cycles, confidence. |
| 0xsarwagya | Summarize workspace packages and package dependencies. | `EvidencePack`, `FindDependencies`, `FindDependents`, `FindCycles`, `GraphStatistics` | workspace, packages, framework nodes, dependency edges; graph hash; confidence. | Deterministic dependency report: direct/transitive edges, cycles, confidence. |
