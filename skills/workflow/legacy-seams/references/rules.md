# Rules

Apply to the untested code you must change. One seam. One blocking dependency. The seam edit does not change logic.

When two sources disagree, follow [sources.md](sources.md). Do not pick a new winner here.

## Pin the behavior

- Before editing, write characterization tests at the change point.
- Assert the observed result, quirks included. Do not assert the result you wish the code had.
- Run those tests on the current code. They pass before you edit.
- A quirk you intend to change is a later edit. It gets its own failing test under `test-driven-development`.
- Do not weaken or delete a characterization test to make a later edit look green.

## Name the seam

- Name the seam: the place where behavior can vary without editing that place.
- Name the enabling point: the place where this change selects the substitute.
- Select the substitute only at that enabling point. Do not hide a second choice inside the legacy body.
- The production path still selects the real dependency at that same point.

## Choose the seam kind

- Prefer a parameter seam or an object seam.
- A parameter seam passes the dependency in from the caller that already has it.
- An object seam overrides a method, or supplies a different object, at the place the object is created or passed.
- Use a link seam or a preprocessing seam only when no explicit seam can reach the dependency.
- A link seam's enabling point is the build or the runtime path that chooses the linked code. Make the test path and the production path obvious.
- A preprocessing seam's enabling point is the definition that replaces the text. Do not leave a production maze of conditional compilation.
- If threading a parameter would cross unrelated frames, use the object seam at construction instead. Do not add tramp parameters to avoid naming the seam.

## Keep the edit separate

- The edit that opens the seam preserves behavior. Results, errors, order, and side effects stay.
- Ship that edit before any logic change. Do not mix them.
- Substitute only the blocking dependency: clock, randomness, I/O, a global, or a hidden construction.
- Call pure single-implementation code directly. Do not put an interface, a fake, or a wrapper on it.
- Do not substitute a collaborator the test can already call.

## When the body cannot be covered

- If you cannot get the legacy body under test in this change, do not edit inside it.
- Put the new behavior in new code. Test that code on its own.
- Call it from one line in the old path. That line is the only edit in the old path.
- The new code does not take legacy types. Translate at the seam.

## Boundary and cleanup

- Translate foreign legacy types at the seam. They do not leak into the new model.
- A translation the old system does not see is transitional when its only job is coexistence.
- An anti-corruption translation that remains part of the target design is not transitional. Do not delete that one under this rule.
- Do not add a pass-through type, a locator, or a container to create the seam.
- Do not add a forwarder whose interface is as large as the call it wraps.
- Delete a transitional seam once callers no longer need it. Do not leave it as a new layer.
