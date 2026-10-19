---
name: architecture
description: "Trade-off analysis and pattern selection for a system or service: classify the project, gather requirements and constraints, choose between monolith/modular monolith/microservices, CRUD vs DDD, repository vs direct ORM, sync vs event-driven, and record the decision. Use when weighing architectural options before building; use architecture-patterns for code-level Clean/Hexagonal/DDD structure and designing-apis for API contracts."
risk: safe
source: community
date_added: "2026-02-27"
---

# Architecture Decision Framework

> "Requirements drive architecture. Trade-offs inform decisions. ADRs capture rationale."

## When to Use

- Choosing an overall shape for a new system or a major extension (monolith, modular monolith, services, serverless)
- Deciding whether a pattern (DDD, CQRS, event-driven, repository layer, microservices) is worth its cost here
- Comparing two or more technical options against explicit quality attributes
- Reviewing a proposed design for over- or under-engineering

Not for: folder/layer structure inside one codebase (`architecture-patterns`), API resource and error design (`designing-apis`), schema and index decisions (`database-design`), multi-service transaction design (`saga-orchestration`), deployment topology (`deploying-applications`).

## Selective Reading Rule

**Read ONLY files relevant to the request.**

| File | Description | When to Read |
|------|-------------|--------------|
| `context-discovery.md` | Questions to ask, project classification | Starting architecture design |
| `trade-off-analysis.md` | Trade-off framework and ADR templates | Comparing options, documenting decisions |
| `pattern-selection.md` | Decision trees, anti-patterns | Choosing patterns |
| `patterns-reference.md` | Quick lookup for patterns | Pattern comparison |
| `examples.md` | MVP, SaaS, Enterprise examples | Calibrating to project size |

## Workflow

1. **Discover context** (`context-discovery.md`): users, scale, team size and skills, timeline, budget, existing systems, compliance.
2. **Name the quality attributes that matter** and rank them: e.g. time to market, availability, latency, cost, operability, security, evolvability. Ranking forces trade-offs to be explicit.
3. **Generate at least two options,** always including the simplest viable one.
4. **Evaluate** each option against the ranked attributes (`trade-off-analysis.md`), and run it through the decision trees in `pattern-selection.md`.
5. **Decide and record** an ADR for anything hard to reverse: context, options, decision, consequences, and the trigger that would make you revisit it. ADR templates are in `trade-off-analysis.md`; the `documentation-and-adrs` skill covers ADR writing conventions in general.
6. **Plan validation:** a spike, prototype, load test or fitness function that proves the riskiest assumption.

## Core Principle

**Start simple; add complexity only when a requirement proves it necessary.** You can add patterns later; removing them is much harder.

| Signal you may need more structure | Signal you are over-engineering |
|------------------------------------|---------------------------------|
| Business rules change often and differ by context | Mostly CRUD with simple validation |
| Several teams need to deploy independently | One small team owns everything |
| Components have very different scaling or availability needs | Everything scales together |
| Data source or integration must be swappable and actually changes | "We might switch databases some day" |

## Validation Checklist

Before finalizing:

- [ ] Requirements and constraints are written down
- [ ] Quality attributes are ranked
- [ ] At least two options compared, including the simplest one
- [ ] Each significant decision has a trade-off analysis and an ADR
- [ ] Team expertise matches the chosen patterns
- [ ] The riskiest assumption has a validation plan

## Related Skills

| Skill | Use For |
|-------|---------|
| `architecture-patterns` | Clean/Hexagonal/DDD structure inside a service |
| `database-design` | Database choice, schema, migrations, HA/DR |
| `designing-apis` | API contracts between components |
| `saga-orchestration` | Consistency across services |
| `deploying-applications` | Deployment architecture |
| `12-factor-app` | Cloud-native service conventions |
