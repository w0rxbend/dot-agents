---
name: codebase-design
description: Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
---

# Codebase Design

Design **deep modules**: lots of behaviour behind small interface, at clean seam, testable through that interface. Apply these terms and principles wherever code is designed or restructured.

## Glossary

Use these terms exactly. Don't substitute "component," "service," "API," or "boundary."

**Module**: anything with interface and implementation. Scale-agnostic by design: function, class, package, or tier-spanning slice. _Avoid_: unit, component, service.

**Interface**: everything caller must know to use module correctly: type signature plus invariants, ordering constraints, error modes, required configuration, performance characteristics. _Avoid_: API, signature (too narrow: type-level surface only).

**Implementation**: code inside module. Distinct from **Adapter**: small adapter can have large implementation (Postgres repo); large adapter can have small one (in-memory fake). Say "adapter" when seam is topic, else "implementation".

**Depth**: leverage at interface: behaviour caller (or test) can exercise per unit of interface learned. **Deep**: much behaviour behind small interface. **Shallow**: interface nearly as complex as implementation.

**Seam** _(Michael Feathers)_: place to alter behaviour without editing there; *location* of module's interface. Seam placement is separate design decision from what goes behind it. _Avoid_: boundary (overloaded with DDD's bounded context).

**Adapter**: concrete thing satisfying interface at seam. Describes *role* (slot filled), not substance (contents).

**Leverage**: callers' gain from depth: more capability per unit of interface learned. One implementation pays back across N call sites and M tests.

**Locality**: maintainers' gain from depth. Change, bugs, knowledge, verification concentrate in one place, not across callers. Fix once, fixed everywhere.

## Deep vs shallow

**Deep module** = small interface + lots of implementation:

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid):

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing interface, ask:

- Fewer methods?
- Simpler parameters?
- More complexity hidden inside?

## Principles

- **Depth is a property of the interface, not the implementation.** Deep module can be internally composed of small, mockable, swappable parts; they just aren't part of interface. Module can have **internal seams** (private to implementation, used by own tests) plus **external seam** at interface.
- **The deletion test.** Imagine deleting module. If complexity vanishes, it was pass-through. If it reappears across N callers, it earned its keep.
- **The interface is the test surface.** Callers and tests cross same seam. Need to test *past* interface? Module is probably wrong shape.
- **One adapter means a hypothetical seam. Two adapters means a real one.** No seam unless something varies across it.

## Designing for testability

1. **Accept dependencies, don't create them.**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, don't produce side effects.**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area.** Fewer methods = fewer tests. Fewer params = simpler setup.

## Relationships

- **Module** has exactly one **Interface** (surface presented to callers and tests).

## Rejected framings

- **Depth as ratio of implementation-lines to interface-lines** (Ousterhout): rewards padding. Use depth-as-leverage.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow. Interface here includes every fact caller must know.

## Going deeper

- **Deepening a cluster given its dependencies**, see [DEEPENING.md](DEEPENING.md): dependency categories, seam discipline, replace-don't-layer testing.
- **Exploring alternative interfaces**, see [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md): parallel sub-agents design interface several radically different ways; compare on depth, locality, seam placement.
