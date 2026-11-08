---
name: improve-codebase-architecture
description: Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
disable-model-invocation: true
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities**: refactors turning shallow modules deep. Goal: testability and AI-navigability.

Command is _informed_ by project domain model, built on shared design vocabulary:

- Call Skill tool with "codebase-design" for architecture vocabulary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and principles (the deletion test, "the interface is the test surface", "one adapter = hypothetical seam, two = real"). Use these terms exactly in every suggestion. Don't drift into "component," "service," "API," or "boundary."
- Domain language in `GLOSSARY.md` names good seams. ADRs in `docs/adr/` record decisions this command should not re-litigate.

## Process

### 1. Explore

**Scope before you scan: YAGNI.** Deepening pays off in easier future changes, so favor recently changed areas. Decide *where* to look first:

- If user named a direction (module, subsystem, pain point), take it and skip inference below.
- Otherwise, scan a good stretch of commit history (`git log --oneline`) for hot spots: recurring files and areas. Look there first. If changes scatter with no clear hot spot, widen the net.

First read `GLOSSARY.md` and any ADRs for the touched area.

Then spawn a sub-agent to walk the codebase. No rigid heuristics: explore organically, note friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow**, interface nearly as complex as implementation?
- Where were pure functions extracted just for testability, while bugs hide in their call sites (no **locality**)?
- Where do tightly-coupled modules leak across seams?
- What is untested, or hard to test through current interface?

Apply **deletion test** to anything suspected shallow: would deleting it concentrate complexity, or just move it? Signal you want: "yes, concentrates".

### 2. Present candidates as an HTML report

Write self-contained HTML file to OS temp dir so nothing lands in repo. Fresh private dir per run: `mktemp -d` (uses `$TMPDIR`, else `/tmp`; on Windows a new folder under `%TEMP%`). Path: `<dir>/architecture-review.html`. Open it (`xdg-open <path>` on Linux, `open <path>` on macOS, `start <path>` on Windows) and tell user the absolute path.

**Tailwind via CDN** for layout and styling. **Mermaid via CDN** for diagrams. Mix Mermaid with hand-crafted CSS/SVG. Mermaid for graph-shaped relationships (call graphs, dependencies, sequences). Hand-built divs/SVG for editorial visuals (mass diagrams, cross-sections, collapse animations). Be visual.

Per candidate, render a card with:

- **Files**: files/modules involved
- **Problem**: why current architecture causes friction
- **Solution**: plain English: what would change
- **Benefits**: gains in locality and leverage, and how tests improve
- **Before / After diagram**: side-by-side, custom-drawn, showing shallowness and deepening
- **Recommendation strength**: one of `Strong`, `Worth exploring`, `Speculative`, as a badge

End with **Top recommendation** section: which candidate to tackle first, and why.

**Use GLOSSARY.md vocabulary for domain, `/codebase-design` vocabulary for architecture.** If `GLOSSARY.md` defines "Order," talk about "the Order intake module," not "the FooBarHandler," and not "the Order service."

**ADR conflicts**: surface a candidate contradicting an existing ADR only when friction is real enough to warrant revisiting the ADR. Mark it clearly in the card (e.g. a warning callout: _"contradicts ADR-0007, but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

See [HTML-REPORT.md](HTML-REPORT.md) for HTML scaffold, diagram patterns, styling guidance.

Do NOT propose interfaces yet. After writing the file, ask user: "Which of these would you like to explore?"

### 3. Grilling loop

Once user picks a candidate, call Skill tool with "grilling" to walk the decision tree together: constraints, dependencies, deepened module's shape, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize. Call Skill tool with "domain-modeling" to keep domain model current:

- **Naming a deepened module after a concept not in `GLOSSARY.md`?** Add the term. Create the file lazily if missing.
- **Sharpening a fuzzy term during conversation?** Update `GLOSSARY.md` right there.
- **User rejects candidate with a load-bearing reason?** Offer an ADR, framed as: _"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"_ Offer only when a future explorer would need the reason to avoid re-suggesting it. Skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want alternative interfaces for deepened module?** Call Skill tool with "codebase-design" and use its design-it-twice parallel sub-agent pattern.
