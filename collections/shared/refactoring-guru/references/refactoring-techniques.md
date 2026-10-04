# Refactoring Techniques Reference

Source: https://refactoring.guru/refactoring/techniques

Refactoring techniques fix code smells without changing observable behavior. Apply them incrementally with tests running after each step.

## Table of Contents
- [Composing Methods](#composing-methods) — reorganize method bodies
- [Moving Features Between Objects](#moving-features-between-objects) — relocate code to where it belongs
- [Organizing Data](#organizing-data) — clean up data handling
- [Simplifying Conditional Expressions](#simplifying-conditional-expressions) — tame complex conditions
- [Simplifying Method Calls](#simplifying-method-calls) — clean method interfaces
- [Dealing with Generalization](#dealing-with-generalization) — fix inheritance hierarchies

---

## Composing Methods

Long methods are the root of most evils. These techniques break methods into well-named pieces.

| Technique | Problem | Solution |
|-----------|---------|----------|
| **Extract Method** | A fragment can be grouped | Move it to a new method; replace with a call |
| **Inline Method** | A method body is more obvious than the method itself | Replace calls with the method's content; delete the method |
| **Extract Variable** | An expression is hard to understand | Put it in a self-explanatory variable |
| **Inline Temp** | A temp variable assigned from a simple expression | Replace uses of the variable with the expression itself |
| **Replace Temp with Query** | A temp stores a result for later reuse | Move expression to a method; call the method wherever needed |
| **Split Temporary Variable** | A temp variable is reused for different things | Use separate variables for each purpose |
| **Remove Assignments to Parameters** | A parameter is reassigned inside a method | Use a local variable instead |
| **Replace Method with Method Object** | Intertwined local variables prevent Extract Method | Move the whole method to a new class; locals become fields |
| **Substitute Algorithm** | You want to replace an algorithm with a better one | Replace the whole method body with the new algorithm |

**Key principle:** If you need a comment to explain a block of code, that block should be a named method.

---

## Moving Features Between Objects

Functionality ended up in the wrong place. These techniques safely relocate it.

| Technique | Problem | Solution |
|-----------|---------|----------|
| **Move Method** | Method is used more by another class than its own | Create the method in the other class; redirect or remove the original |
| **Move Field** | A field is used more by another class | Create the field there; redirect all users |
| **Extract Class** | One class does the work of two | Create a new class for part of the functionality |
| **Inline Class** | A class does almost nothing | Move all features to another class; delete it |
| **Hide Delegate** | Client calls B through A (`a.getB().doSomething()`) | Add a delegation method to A so B is hidden |
| **Remove Middle Man** | A class delegates everything | Delete the middle-man; let clients call directly |
| **Introduce Foreign Method** | Utility class lacks a needed method you can't add | Add the method to your client class, pass the utility object as arg |
| **Introduce Local Extension** | Utility class needs several methods you can't add | Create a subclass or wrapper of the utility class |

---

## Organizing Data

Replace primitives with proper abstractions and clean up data relationships.

| Technique | Problem | Solution |
|-----------|---------|----------|
| **Self Encapsulate Field** | Direct access to private fields inside a class | Create getter/setter; use them internally |
| **Replace Data Value with Object** | A primitive has its own behavior and data | Create a class for it |
| **Change Value to Reference** | Many identical instances of a class | Make them share a single reference object |
| **Change Reference to Value** | A reference object is tiny and infrequently changed | Convert to value object |
| **Replace Array with Object** | An array contains heterogeneous data types | Replace with an object; one field per element |
| **Duplicate Observed Data** | Domain data lives in a GUI class | Move data to a separate domain object; sync between them |
| **Change Unidirectional to Bidirectional Association** | Two classes need each other but only one knows | Add the missing association |
| **Change Bidirectional to Unidirectional Association** | A bidirectional association, but one side never uses it | Remove the unused direction |
| **Replace Magic Number with Symbolic Constant** | A literal number has a specific meaning | Replace with a named constant |
| **Encapsulate Field** | A field is public | Make it private; add getter/setter |
| **Encapsulate Collection** | A collection field has simple getter/setter | Return read-only view; add add/remove methods |
| **Replace Type Code with Class** | A numeric type code that doesn't affect behavior | Replace with a class |
| **Replace Type Code with Subclasses** | A type code that directly affects behavior | Create subclasses for each type; extract behaviors |
| **Replace Type Code with State/Strategy** | Type code affects behavior but subclassing is impossible | Replace with a State or Strategy object |
| **Replace Subclass with Fields** | Subclasses differ only in constant-returning methods | Add constants to the parent; delete the subclasses |

---

## Simplifying Conditional Expressions

Conditionals grow complex over time. These techniques make them readable and maintainable.

| Technique | Problem | Solution |
|-----------|---------|----------|
| **Decompose Conditional** | A complex `if/else` or `switch` | Extract the condition and each branch into named methods |
| **Consolidate Conditional Expression** | Multiple conditions lead to the same result | Merge them into one expression; extract to a method |
| **Consolidate Duplicate Conditional Fragments** | Identical code in all branches of a conditional | Move the code outside the conditional |
| **Remove Control Flag** | A boolean variable acts as a control flag | Replace with `break`, `continue`, or `return` |
| **Replace Nested Conditional with Guard Clauses** | Nested conditions make the normal flow hard to see | Isolate edge cases as early-return guard clauses at the top |
| **Replace Conditional with Polymorphism** | A conditional switches behavior based on object type | Create subclasses; move each branch into an overridden method |
| **Introduce Null Object** | Many `null` checks in your code | Return a Null Object that exhibits default/do-nothing behavior |
| **Introduce Assertion** | Code relies on certain conditions being true | Replace assumptions with explicit assertion checks |

---

## Simplifying Method Calls

Clean up method interfaces to make interactions between classes simpler.

| Technique | Problem | Solution |
|-----------|---------|----------|
| **Rename Method** | Method name doesn't explain what it does | Give it a better name |
| **Add Parameter** | Method needs more data to act | Add a new parameter |
| **Remove Parameter** | A parameter is unused | Delete it |
| **Separate Query from Modifier** | A method returns a value *and* changes state | Split into two: one queries, one modifies |
| **Parameterize Method** | Multiple methods do the same thing with different values | Merge into one method with a parameter |
| **Replace Parameter with Explicit Methods** | A method splits behavior based on a parameter value | Create separate explicit methods for each branch |
| **Preserve Whole Object** | You extract several values from an object to pass as parameters | Pass the whole object instead |
| **Replace Parameter with Method Call** | You pass a parameter whose value you could compute | Compute it inside the method; remove the parameter |
| **Introduce Parameter Object** | Repeating group of parameters | Replace the group with a parameter object (new class) |
| **Remove Setting Method** | A field should be set only at creation | Remove the setter; set in constructor only |
| **Hide Method** | A method isn't used outside its class hierarchy | Make it private or protected |
| **Replace Constructor with Factory Method** | Constructor does more than set fields | Create a factory method; clients call it instead |
| **Replace Error Code with Exception** | Method returns a special error code | Throw an exception instead |
| **Replace Exception with Test** | You throw an exception where a test would suffice | Replace with a conditional test |

---

## Dealing with Generalization

Fix problems in inheritance hierarchies — things in the wrong level, or inheritance used where delegation fits better.

| Technique | Problem | Solution |
|-----------|---------|----------|
| **Pull Up Field** | Two subclasses have the same field | Move the field to the superclass |
| **Pull Up Method** | Subclasses have methods that perform similar work | Make the methods identical; move to superclass |
| **Pull Up Constructor Body** | Subclass constructors have mostly identical code | Create a superclass constructor; call it from subclasses |
| **Push Down Method** | Superclass behavior only used by one/few subclasses | Move to those specific subclasses |
| **Push Down Field** | A superclass field is only used by a few subclasses | Move to those subclasses |
| **Extract Subclass** | A class has features used only in some cases | Create a subclass for those cases |
| **Extract Superclass** | Two classes have common fields and methods | Create a shared superclass; pull common elements up |
| **Extract Interface** | Multiple clients use the same subset of a class | Extract that subset into an interface |
| **Collapse Hierarchy** | A subclass is practically the same as its superclass | Merge them |
| **Form Template Method** | Subclasses implement algorithms with similar steps in the same order | Move the structure and identical steps to the superclass; leave differing steps in subclasses |
| **Replace Inheritance with Delegation** | A subclass uses only part of the superclass interface | Create a field for a superclass instance; delegate; remove inheritance |
| **Replace Delegation with Inheritance** | A class delegates all methods to another class | Make the class extend the delegate |

---

## Quick Reference: Smell → Technique Mapping

| Smell | Primary Techniques |
|-------|-------------------|
| Long Method | Extract Method, Decompose Conditional, Replace Temp with Query |
| Large Class | Extract Class, Extract Subclass, Extract Interface |
| Primitive Obsession | Replace Data Value with Object, Replace Type Code with Class |
| Long Parameter List | Introduce Parameter Object, Preserve Whole Object |
| Data Clumps | Extract Class, Introduce Parameter Object |
| Switch Statements | Replace Conditional with Polymorphism, Replace Type Code with Subclasses |
| Temporary Field | Extract Class, Introduce Null Object |
| Refused Bequest | Push Down Method/Field, Replace Inheritance with Delegation |
| Duplicate Code | Extract Method, Extract Superclass, Form Template Method |
| Feature Envy | Move Method, Extract Method |
| Inappropriate Intimacy | Move Method/Field, Replace Inheritance with Delegation |
| Message Chains | Hide Delegate, Extract Method + Move Method |
| Middle Man | Remove Middle Man, Inline Method |
| Divergent Change | Extract Class |
| Shotgun Surgery | Move Method/Field, Inline Class |
| Comments (smell) | Extract Method, Rename Method, Introduce Assertion |
