# Sources

Distilled. Not a copy. Read the original before you cite a page.

## Pages

- Refactoring catalog: https://refactoring.com/
- Smell groups used here: the Fowler/Beck list as rendered at https://refactoring.guru/refactoring/smells. refactoring.com publishes refactorings, not this index.
- Martin Fowler, "CodeSmell" (2006), https://martinfowler.com/bliki/CodeSmell.html. A smell is a hint. Confirm a real problem.
- Clean Code summary by wojteklu: https://gist.github.com/wojteklu/73c6914cc446146b8b533c0988cf8d29
- Worxbend current Scala style (`CODE_STYLE.md`): https://github.com/worxbend/worxbend/blob/main/CODE_STYLE.md
- Worxbend older Scala style (`SCALA_CODE_STYLE.md`): https://github.com/worxbend/worxbend/blob/main/SCALA_CODE_STYLE.md
- SonarSource, "Code Smells": https://www.sonarsource.com/resources/library/code-smells/
- JetBrains IDEA tag "code smells": https://blog.jetbrains.com/idea/tag/code-smells/
- IBM, "Code smells": https://www.ibm.com/think/topics/code-smells
- Smell catalog, 56 smells: https://www.codesmells.org/

The JetBrains tag index had seven posts. A second tag page returned 404. Fowler's 2018 second-edition changes article says the smell chapter was rewritten. That chapter is not listed on refactoring.com.

## What each source contributes

- refactoring.com contributes treatment names and the rule that a refactoring preserves behavior.
- refactoring.guru contributes the classic smell groups: bloaters, object-oriented abusers, change preventers, dispensables, couplers, plus Incomplete Library Class.
- The gist contributes names, small functions, few arguments, no flag arguments, no hidden side effects, small types, hidden internals, constructor injection, polymorphism over a repeated switch, one place for boundary checks, value objects, variables near use, callers above callees, comments for intent, deletion of commented-out code, and the six design costs.
- `CODE_STYLE.md` contributes the current worxbend Scala rules. It wins conflicts with the older guide.
- `SCALA_CODE_STYLE.md` contributes numeric limits and naming details the current guide does not restate: prefer under 20 lines, do not exceed 50, stop at 3 or 4 parameters, UpperCamelCase constants, acronyms as words, Mill module shape, MUnit, exhaustive matches, immutable collections.
- SonarSource says a smell is not a bug. Its groups are bloaters, object-oriented abusers, dispensables, and couplers. Inspect. Rank by severity, frequency, and payoff. Change structure only. Cover the change with tests. Prefer less shared mutation.
- IBM uses nine groups and says there is no canonical list. Same caution. Do not delete comments as a class. An imperative index loop is a smell when a pipeline exists.
- JetBrains rejects a rigid taxonomy. Look for a simpler form. Optional only for real absence. Do not replace every null. Do not return null from a caught exception. Do not swallow an exception. Prefer tell-don't-ask over a getter chain in domain code. A builder or a DSL is not a message chain. Search with a Set, a Map, or a library contains. Local obvious mutation may stay. A boolean parameter that selects a second behavior means split the function. Guards at the top. Positive conditions. `else` when only one branch may run. One smell at a time. Test an edge you found. Do not redesign first when the same complexity only moves.
- codesmells.org contributes the further smells in [smells.md](smells.md). Not every conditional is a smell. Base Class depends on Subclass has no listed treatment.

## Winners

- **Mutation.** Sonar and IBM prefer less shared mutation. JetBrains allows local obvious mutation. Worxbend Scala bans shared mutable state and `var` unless a written rule relaxes it. On Scala in a worxbend repo, worxbend wins. Elsewhere, no shared mutation, and local obvious mutation may stay.
- **Null.** JetBrains says do not replace every null with Optional. Worxbend says never null, and never `Option#get`. In Scala, never null. Elsewhere, null only at a boundary, never as a hidden failure. An absence type only for real absence, unwrapped next to the call.
- **Loops.** codesmells.org and IBM treat an imperative index loop as a smell when a pipeline exists. JetBrains treats a search-by-scan as the smell. Scala prefers the collection operation. In Scala, use the collection operation. Elsewhere, replace a scan with the lookup the data owns. Do not rewrite every loop into a pipeline.
- **Comments.** Comment why, not what. IBM says do not delete comments as a class. The gist says delete commented-out code. JetBrains allows a temporary comment while untangling one function. Delete narration and commented-out code. Keep why, warnings, and constraints. Delete the temporary comment before you finish.
- **Cleanup scope.** The gist says leave code cleaner than you found it. `CODE_STYLE.md` forbids unrelated cleanup and churn-only rewrites. `CODE_STYLE.md` wins. Clean only lines this change already touches, unless the user asked for a sweep.
- **Tests.** The gist wants one assert. `CODE_STYLE.md` wants one scenario and domain assertions. `CODE_STYLE.md` wins.
- **Scala guides.** `CODE_STYLE.md` is the current direct-style guide and wins. Numeric limits from `SCALA_CODE_STYLE.md` still apply where the current guide is silent. Import order, braces, blank lines, trailing commas, and the effect toolkit follow `CODE_STYLE.md` and Scalafmt.

## Treatment names this skill refuses

These names are absent from the current refactoring.com catalog. Do not prescribe them:

Extract Interface, Duplicate Observed Data, Replace Array with Object, Form Template Method, Hide Method, Change Bidirectional Association to Unidirectional, Replace Delegation with Inheritance, Introduce Foreign Method, Introduce Local Extension.

Incomplete Library Class used to point at the last two. Wrap the library at the boundary.
