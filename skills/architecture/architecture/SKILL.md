---
name: architecture
description: "Trade-off analysis and pattern selection for a system or service: classify the project, gather requirements and constraints, choose between monolith/modular monolith/microservices, CRUD vs DDD, repository vs direct ORM, sync vs event-driven, and record the decision. Use when weighing architectural options before building; use architecture-patterns for code-level Clean/Hexagonal/DDD structure and designing-apis for API contracts."
risk: safe
source: community
date_added: "2026-02-27"
---

# Architecture Decision Framework

## When to Use

- Choosing overall shape for new system or major extension (monolith, modular monolith, services, serverless)
- Deciding if pattern (DDD, CQRS, event-driven, repository layer, microservices) is worth its cost here
- Comparing two or more technical options against explicit quality attributes
- Reviewing proposed design for over- or under-engineering

Not for: folder/layer structure inside one codebase (`architecture-patterns`), API resource and error design (`designing-apis`), schema and indexes (`database-design`), multi-service transactions (`saga-orchestration`), deployment topology (`deploying-applications`).

## Selective Reading Rule

**Read ONLY files relevant to request.**

| File | Description | When to Read |
|------|-------------|--------------|
| `context-discovery.md` | Questions to ask, project classification | Starting design |
| `trade-off-analysis.md` | Trade-off framework, ADR templates | Comparing options, documenting decisions |
| `pattern-selection.md` | Decision trees, anti-patterns | Choosing patterns |
| `patterns-reference.md` | Pattern quick lookup | Pattern comparison |
| `examples.md` | MVP, SaaS, Enterprise examples | Calibrating to project size |

## Workflow

1. **Discover context** (`context-discovery.md`): users, scale, team size and skills, timeline, budget, existing systems, compliance.
2. **Name quality attributes that matter** and rank them: e.g. time to market, availability, latency, cost, operability, security, evolvability. Ranking makes trade-offs explicit.
3. **Generate at least two options,** always including simplest viable one.
4. **Evaluate** each option against ranked attributes (`trade-off-analysis.md`). Run each through decision trees in `pattern-selection.md`.
5. **Decide and record** ADR for anything hard to reverse: context, options, decision, consequences, revisit trigger. ADR templates: `trade-off-analysis.md`. General ADR writing conventions: `documentation-and-adrs` skill.
6. **Plan validation:** spike, prototype, load test or fitness function proving riskiest assumption.

## Core Principle

**Start simple; add complexity only when a requirement proves it necessary.** Patterns can be added later; removing them is much harder. When in doubt, choose simpler option.

| Signals you may need more structure | Signals of over-engineering |
|-------------------------------------|-----------------------------|
| Business rules change often, differ by context | Mostly CRUD, simple validation |
| Several teams need to deploy independently | One small team owns everything |
| Components need very different scaling or availability | Everything scales together |
| Data source or integration must be swappable, and actually changes | "We might switch databases some day" |

## Validation Checklist

Before finalizing:

- [ ] Requirements and constraints written down
- [ ] Quality attributes ranked
- [ ] At least two options compared, including simplest one
- [ ] Each significant decision has trade-off analysis and ADR
- [ ] Team expertise matches chosen patterns
- [ ] Riskiest assumption has validation plan

## Related Skills

| Skill | Use For |
|-------|---------|
| `database-design` | Database choice, schema, migrations, HA/DR |
| `12-factor-app` | Cloud-native service conventions |
