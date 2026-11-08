# Smells

A smell is a hint. It is not a bug. Confirm a real cost before you change existing code. Do not introduce one in new code. Rank by severity, how often it bites, and payoff. One smell at a time. Cover the behavior with a test. Stop when the cure creates the opposite smell.

Treatment names are current [refactoring.com](https://refactoring.com/) names. The grouped list is the Fowler/Beck catalog as rendered by refactoring.guru. refactoring.com does not publish this index. Names that are absent from the current catalog are listed in [sources.md](sources.md). Do not prescribe those absent names.

A single clear branch is fine. A sealed match with exhaustive cases is fine. A guard at the top is fine.

## Bloaters

- **Long Method.** Sniff near 10 to 12 lines, or when a block needs a comment. A single straight sequence may stay. Some long methods are fine. Treatment: Extract Function, Decompose Conditional, Replace Temp with Query, Introduce Parameter Object, Preserve Whole Object, Replace Function with Command.
- **Large Class.** The type has many unrelated reasons to change. Treatment: Extract Class.
- **Primitive Obsession.** A domain idea is still a string, a number, or a boolean. Treatment: Replace Primitive with Object, Replace Type Code with Subclasses, Introduce Parameter Object.
- **Long Parameter List.** Past 3 or 4 parameters, or the same group repeats at many calls. Treatment: Introduce Parameter Object, Preserve Whole Object, Replace Parameter with Query, Remove Flag Argument.
- **Data Clumps.** The same few fields travel together. Treatment: Extract Class, Introduce Parameter Object, Preserve Whole Object.

## Object-oriented abusers

- **Switch Statements.** The same type test repeats. One sealed match in one place is fine. Treatment: Replace Conditional with Polymorphism, Replace Type Code with Subclasses, Introduce Special Case.
- **Temporary Field.** A field is set only on some paths. Treatment: Extract Class, Introduce Special Case, Move Function.
- **Refused Bequest.** A subtype ignores or disables parent behavior. Treatment: Replace Superclass with Delegate.
- **Alternative Classes with Different Interfaces.** Two types do the same job under different names. Treatment: Change Function Declaration, Move Function, Extract Superclass.

## Change preventers

- **Divergent Change.** One type is edited for many unrelated reasons. Treatment: Extract Class, Move Function.
- **Shotgun Surgery.** One change edits many types. Treatment: Move Function, Move Field, Inline Class.
- **Parallel Inheritance Hierarchies.** A new subtype forces a twin subtype elsewhere. Treatment: Move Function, Move Field.

## Dispensables

- **Comments.** A comment narrates the next line. Keep why, a warning, or a constraint the code cannot say. Do not delete comments as a class. Treatment: Extract Function, Introduce Assertion, and a name that makes the narration useless.
- **Duplicate Code.** The same knowledge lives in two places. Look-alike text with different rules is not a duplicate. Treatment: Extract Function, Pull Up Field, Pull Up Constructor Body, Substitute Algorithm, Parameterize Function.
- **Lazy Class.** The type no longer earns its file. Treatment: Inline Class, Collapse Hierarchy.
- **Data Class.** Fields and accessors only. The behavior lives elsewhere. Treatment: Encapsulate Variable, Encapsulate Collection, Remove Setting Method, Move Function.
- **Dead Code.** Unused type, branch, parameter, or import. Treatment: Remove Dead Code, Inline Function, Collapse Hierarchy.
- **Speculative Generality.** A hook, flag, base, or parameter has no caller today. Treatment: Collapse Hierarchy, Inline Function, Inline Class, Remove Dead Code, Change Function Declaration.

## Couplers

- **Feature Envy.** A function uses another type's data more than its own. Treatment: Move Function, Extract Function.
- **Inappropriate Intimacy.** Two types reach into each other's internals. Treatment: Move Function, Move Field, Extract Class, Hide Delegate.
- **Message Chains.** Domain code walks `a.b().c().d()`. A builder or a DSL is not this smell. Treatment: Hide Delegate, Extract Function, Move Function.
- **Middle Man.** The type only forwards calls. Treatment: Remove Middle Man, Inline Function, Inline Class.

## Other classic

- **Incomplete Library Class.** A library type needs one more operation, and you cannot change the library. Wrap it at your boundary. Do not prescribe a treatment name that the current catalog dropped. See [sources.md](sources.md).

## Further smells

These names come from [codesmells.org](https://www.codesmells.org/). One line each. Apply the same confirm-the-cost rule.

- **Combinatorial Explosion.** Each new variant multiplies branches. Use one polymorphic or data-driven path.
- **Null Check.** Null tests spread past the boundary. Push the check to the edge. Use an absence type only for real absence.
- **Oddball Solution.** One place solves a shared problem a different way. Make one solution the shared one.
- **Required Setup/Teardown.** The caller must remember a ritual or the call is wrong. Put the ritual in the type that owns the resource.
- **Callback Hell.** Nested callbacks hide the sequence. Name each step. Sequence them in one place.
- **Dubious Abstraction.** The abstraction has one implementation and no second caller. Inline it.
- **Flag Argument.** A boolean picks a second behavior. Split the function. Treatment: Remove Flag Argument.
- **Special Case.** A rare value is handled with scattered conditions. Treatment: Introduce Special Case.
- **Afraid To Fail.** Failure comes back as null, empty, or a fake success. Return the failure. Do not swallow it.
- **Binary Operator in Name.** The name joins two jobs with and/or. Split the function.
- **Indecent Exposure.** The public surface is wider than any caller needs. Narrow it.
- **Type Embedded in Name.** The name repeats the declared type. Drop the type word.
- **Global Data.** Hidden shared mutable state. Pass the value. Treatment: Encapsulate Variable.
- **Hidden Dependencies.** A function uses a service the signature does not show. Pass it, or construct it in one place.
- **Tramp Data.** A value is passed through types that never use it. Move the call to the user.
- **Imperative Loops.** An index loop restates a pipeline the language already has. Use the pipeline. A search that should be a Set or Map lookup is the smell. Do not rewrite every loop.
- **Mutable Data.** Shared mutation. Keep mutation local and obvious, or remove it. Worxbend Scala bans shared mutable state. See [rules.md](rules.md).
- **Side Effects.** A function both answers and changes state. Split the command from the query.
- **Boolean Blindness.** A boolean hides which case it is. Use a named type, or two functions.
- **Fallacious Comment.** The comment lies. Fix the comment or the code. Do not keep both.
- **Fallacious Method Name.** The name claims a different job than the body. Rename, or split.
- **Inconsistent Names.** One idea has many words. Use the word the file already uses.
- **Magic Number.** A bare number or string carries domain meaning. Name it.
- **Uncommunicative Name.** The name does not say the role. Rename.
- **Base Class depends on Subclass.** The parent mentions a child. Invert the dependency. This smell has no standard treatment on codesmells.org.
- **Conditional Complexity.** Conditions nest. Treatment: Decompose Conditional, Consolidate Conditional Expression, Replace Conditional with Polymorphism.
- **Inappropriate Static.** A static reaches for state or a collaborator. Pass the collaborator.
- **Clever Code.** The reader must decode a trick. Write the obvious form.
- **Complicated Boolean Expression.** Many and/or/not. Treatment: Extract Variable, Decompose Conditional. Prefer a positive condition.
- **Complicated Regex.** The pattern cannot be read. Name the parts, or parse in steps.
- **Inconsistent Style.** This change invents a second local style. Match the file. The formatter owns layout.
- **Obscured Intent.** The reader cannot see the goal. Extract a function and name the goal.
- **Status Variable.** A field tracks progress the control flow already shows. Use the control flow, or a sealed state.
- **Vertical Separation.** Caller and callee sit far apart for no reason. Treatment: Slide Statements. Put the caller above the callee.

## Construction

- Take small steps. Each step preserves behavior.
- Refactor before a hard change. Refactor again after it works.
- Extract when a block needs a comment to be understood.
- Keep data and the behavior that uses it together.
- Give one duplicated piece of knowledge one function.
- Name so a what-comment is unnecessary.
- Delete unused code and unused generality.
- Fix one smell at a time.
- Add a test for an edge you discovered.
- Do not redesign first when the same complexity only moves.
