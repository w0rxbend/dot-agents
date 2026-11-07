---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a GLOSSARY.md, or recording or editing an ADR.
---

# Domain Modeling

*Active* discipline while designing: challenge terms, invent edge-case scenarios, write glossary and decisions down as soon as they crystallise. Merely *reading* `GLOSSARY.md` for vocabulary is not this skill: use it when changing the model, not only consuming it.

## File structure

Most repos have one context:

```
/
├── GLOSSARY.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If `GLOSSARY-MAP.md` exists at root, repo has multiple contexts. Map points to where each one lives:

```
/
├── GLOSSARY-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── GLOSSARY.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── GLOSSARY.md
│       └── docs/adr/
```

Create files lazily: only when you have something to write. If no `GLOSSARY.md` exists, create one when first term is resolved. If no `docs/adr/` exists, create it when first ADR is needed.

## During the session

### Challenge against the glossary

When user's term conflicts with existing language in `GLOSSARY.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When user uses vague or overloaded terms, propose precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships come up, stress-test them with specific scenarios. Invent edge-case scenarios that force user to be precise about boundaries between concepts.

### Cross-reference with code

When user states how something works, check whether code agrees. Surface any contradiction: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Update GLOSSARY.md inline

Update `GLOSSARY.md` as soon as a term is resolved; don't batch updates. Use format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md).

Keep `GLOSSARY.md` free of implementation details. Do not treat `GLOSSARY.md` as spec, scratch pad, or repository for implementation decisions. It is a glossary only.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse**: changing your mind later has meaningful cost
2. **Surprising without context**: future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: real alternatives existed and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use format in [ADR-FORMAT.md](./ADR-FORMAT.md).
