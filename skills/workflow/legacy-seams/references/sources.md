# Sources

Distilled. Not a copy. Read the original before you cite a page.

## Pages

- Martin Fowler, "Legacy Seam" (2024), https://martinfowler.com/bliki/LegacySeam.html
- Michael Feathers, "Seam Types", InformIT excerpt, https://www.informit.com/articles/article.aspx?p=359417&seqNum=3
- Martin Fowler, "Strangler Fig" (2024), https://martinfowler.com/bliki/StranglerFigApplication.html
- Ian Cartwright, Rob Horn, and James Lewis, "Legacy Mimic" (2022), https://martinfowler.com/articles/patterns-legacy-displacement/legacy-mimic.html
- John Ousterhout, "Modular Design", CS 190 notes, https://web.stanford.edu/~ouster/cgi-bin/cs190-winter18/lecture.php?topic=modularDesign
- Scott Wlaschin, "Six approaches to dependency injection", https://fsharpforfunandprofit.com/posts/dependencies/

## What each source contributes

- Fowler names the seam and the enabling point. Behavior changes at the seam without editing that place. The enabling point is where the choice is made. His examples include a function parameter, a service locator, and a module-level rebinding. He also uses a seam to redirect flow while displacing legacy behavior. This skill keeps the parameter and the object seam.
- Feathers names preprocessing seams, link seams, and object seams. Each has an enabling point. Object seams are explicit. Link and preprocessing seams put the enabling point outside the program text, so tests that depend on them are easier to miss.
- The strangler fig page is a modernization program: grow the new path beside the old one, split at seams, and accept transitional code that later goes away. Choosing and sequencing that program belongs to `code-refactoring-tech-debt`.
- Legacy Mimic is a transitional translation. A providing mimic sits behind a legacy interface. A consuming mimic calls one. The old system does not take the new types. A translation that remains in the target design is an anti-corruption boundary, not a mimic.
- Ousterhout's notes treat a pass-through method as a shallow module. A seam is not a reason to add a forwarder.
- Wlaschin separates an impure dependency (I/O, clock, randomness) from a pure function that has one implementation. Pass the impure dependency in, or keep it at the edge. Call the pure function. Do not add an abstraction, a locator, or a container for it.

## Winners

- **Locator and container.** Fowler's bliki shows both a locator and a rebinding function. Wlaschin rejects a locator. This skill rejects a locator, a container, and a pass-through type.
- **Which seam.** Feathers prefers an object seam. Fowler's first example is a parameter. Both are allowed. Pick the enabling point with the smaller edit. Do not thread a parameter through unrelated frames when construction already reaches the dependency.
- **What the test pins.** The characterization test records the result the code produces now, including a quirk. A failing test for a wanted behavior belongs to `test-driven-development`, and it comes after this edit.
- **Transitional code.** Strangler and Legacy Mimic allow a temporary adapter. Delete it when no caller needs it. Do not promote it into a permanent layer. A lasting anti-corruption translation stays.
- **Scope.** The strangler fig page does not authorize a system replacement inside this skill.
