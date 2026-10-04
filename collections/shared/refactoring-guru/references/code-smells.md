# Code Smells Reference

Source: https://refactoring.guru/refactoring/smells

Code smells are indicators of problems in code that can be addressed during refactoring. They're symptoms — not root causes — so look for what's driving the smell before applying a fix.

## Table of Contents
- [Bloaters](#bloaters) — code that has grown too large
- [Object-Orientation Abusers](#oo-abusers) — misapplied OO principles
- [Change Preventers](#change-preventers) — code that resists change
- [Dispensables](#dispensables) — unnecessary code
- [Couplers](#couplers) — over-coupling between classes

---

## Bloaters

Code, methods, and classes that have grown so large they're hard to work with. These accumulate over time as features are added without discipline.

---

### Long Method
**Signs:** A method contains too many lines of code. Generally any method over 10 lines warrants scrutiny.

**Why it happens:** Developers keep adding lines ("it's just two lines more") rather than extracting new methods. Comments inside methods often indicate that logic could be its own named method.

**Treatments:**
- **Extract Method** — group a fragment into a new method named after its purpose
- **Replace Temp with Query** — replace temp variables holding expression results with a method call
- **Introduce Parameter Object** / **Preserve Whole Object** — when local variables block extraction
- **Replace Method with Method Object** — when intertwined locals prevent extraction
- **Decompose Conditional** — move complex conditionals into their own methods

**Payoff:** Shorter methods are easier to understand, test, and maintain. Long methods hide duplication.

---

### Large Class
**Signs:** A class has many fields, many methods, and too many lines of code.

**Why it happens:** Classes start small and grow as features are added. Easier to add to an existing class than create a new one.

**Treatments:**
- **Extract Class** — spin off a set of fields/methods into a new class
- **Extract Subclass** — if behavior is used only in some cases
- **Extract Interface** — if multiple clients use the same subset of behavior
- **Duplicate Observed Data** — if a large class mixes GUI and domain data

**Payoff:** Removes need to remember a huge number of attributes. Reduces duplication.

---

### Primitive Obsession
**Signs:** Using primitives (int, string, float) instead of small domain objects. Using constants to encode type codes (e.g., `USER_ROLE = 1`). Using strings as field names in data arrays.

**Why it happens:** It feels like overkill to create a small class for a "simple" value.

**Treatments:**
- **Replace Data Value with Object** — create a class for the primitive when it needs behavior
- **Introduce Parameter Object** / **Preserve Whole Object** — replace groups of primitives
- **Replace Type Code with Class/Subclasses/State-Strategy** — replace type code integers

**Payoff:** More flexible code. Better understanding through named domain types.

---

### Long Parameter List
**Signs:** More than 3–4 parameters for a method.

**Why it happens:** Methods were made more universal to avoid dependencies; logic from multiple methods was merged.

**Treatments:**
- **Replace Parameter with Method Call** — if a parameter can be computed by calling another method
- **Preserve Whole Object** — pass the object instead of its extracted fields
- **Introduce Parameter Object** — group related parameters into a new class

**Payoff:** Shorter, more readable method signatures. Easier to test.

---

### Data Clumps
**Signs:** The same group of fields or parameters always appears together across different classes and methods (e.g., host, port, user, password for a connection).

**Why it happens:** Poor structure; copy-paste programming.

**Treatments:**
- **Extract Class** — move the clump into its own class
- **Introduce Parameter Object** / **Preserve Whole Object** — replace parameter groups

**Payoff:** Reduces code size. Makes the implicit grouping explicit and named.

---

## OO Abusers

Incomplete or incorrect application of object-oriented programming principles.

---

### Switch Statements
**Signs:** A complex `switch` operator or long sequence of `if/else` based on object type.

**Why it happens:** OO was not applied. The same switch may be scattered across multiple places; adding a new case requires finding all occurrences.

**Rule of thumb:** When you see `switch`, think about polymorphism.

**Treatments:**
- **Extract Method** + **Move Method** — isolate the switch and move it to the right class
- **Replace Type Code with Subclasses** or **Replace Type Code with State/Strategy** — when switching on type codes
- **Replace Conditional with Polymorphism** — the key fix; move each branch to a subclass override
- **Replace Parameter with Explicit Methods** — when method branches only differ by parameter
- **Introduce Null Object** — when one branch handles `null`

**When to ignore:** Switch for simple, unchanging actions. Factory pattern switches.

---

### Temporary Field
**Signs:** A field in an object is only set and used under certain conditions; at other times it's empty/null.

**Why it happens:** Extra fields were added to pass data between methods instead of using parameters.

**Treatments:**
- **Extract Class** — move the temporary fields and the methods that use them into a new class
- **Introduce Null Object** — create an alternative class that does nothing when the fields aren't set

---

### Refused Bequest
**Signs:** A subclass uses only some of the methods/properties inherited from its parent. Inherited behavior is unneeded or makes no sense.

**Why it happens:** Inheritance was used for code reuse without a true IS-A relationship.

**Treatments:**
- **Push Down Method** / **Push Down Field** — move unneeded items from parent to only the subclasses that need them
- **Replace Inheritance with Delegation** — if a subclass has nothing in common with a superclass

**When to ignore:** If the subclass simply refuses some behaviors without causing confusion.

---

### Alternative Classes with Different Interfaces
**Signs:** Two classes perform the same function but have different method names for the same operations.

**Why it happens:** Developed independently without awareness of each other.

**Treatments:**
- **Rename Method** — make method names consistent
- **Move Method** / **Extract Superclass** — if only part of the functionality is duplicated

---

## Change Preventers

Making one change forces many changes elsewhere. A sign of poor separation of concerns.

---

### Divergent Change
**Signs:** You frequently have to change many unrelated methods in the same class when you make any one modification (e.g., adding a new product type requires changing find, display, and order methods in the same class).

**Why it happens:** Too many responsibilities in a single class; poor cohesion.

**Opposite of Shotgun Surgery.**

**Treatments:**
- **Extract Class** — separate concerns into different classes
- **Extract Superclass** / **Extract Subclass** if appropriate

**Payoff:** Improved code organization. Reduce code duplication.

---

### Shotgun Surgery
**Signs:** Making a small change requires many small changes scattered across many different classes.

**Why it happens:** A single responsibility was spread across many classes.

**Opposite of Divergent Change.**

**Treatments:**
- **Move Method** / **Move Field** — consolidate the behavior into a single class
- **Inline Class** — if a class is no longer doing enough on its own

**Payoff:** Better organization. Less to change per modification.

---

### Parallel Inheritance Hierarchies
**Signs:** When you create a subclass for one class, you find you also need to create a subclass for another class.

**Why it happens:** Hierarchies grew in parallel without being unified.

**Treatments:**
- Make instances of one hierarchy refer to instances of the other, then remove the duplication using **Move Method** / **Move Field**

---

## Dispensables

Unnecessary code whose removal makes the codebase cleaner and easier to understand.

---

### Comments (as Smell)
**Signs:** A method is filled with explanatory comments — every non-obvious line is documented.

**Why it's a smell:** Comments often compensate for bad code. If code needs a comment to explain *what* it does, consider renaming/extracting instead.

**Treatments:**
- **Extract Method** — move the commented block into a self-named method
- **Rename Method** — make the method name describe what it does
- **Introduce Assertion** — replace comments about preconditions with assertions

**Note:** Comments explaining *why* (intent) are valuable; comments explaining *what* are a smell.

---

### Duplicate Code
**Signs:** Two or more code fragments look almost identical.

**Why it happens:** Developers work independently; copy-paste programming; "almost right" temptation.

**Treatments:**
- Same class duplicates → **Extract Method**
- Subclass duplicates → **Extract Method** + **Pull Up Method/Field**
- Identical constructors → **Pull Up Constructor Body**
- Similar but not identical → **Form Template Method**
- Different algorithms → **Substitute Algorithm**
- Different classes → **Extract Superclass** or **Extract Class** + delegate
- Duplicate conditionals → **Consolidate Conditional Expression** + **Extract Method**

**Payoff:** Shorter, clearer code. Change once, applied everywhere.

---

### Lazy Class
**Signs:** A class doesn't do enough to justify its existence — almost nothing, no planned expansion.

**Why it happens:** Planned features weren't implemented; class became superfluous after refactoring.

**Treatments:**
- **Inline Class** — fold its contents into the class that uses it
- **Collapse Hierarchy** — if it's a subclass

---

### Data Class
**Signs:** A class contains only fields, getters, and setters. No behavior. Just a dumb data container.

**Why it happens:** New classes were added for structure but business logic ended up elsewhere.

**Treatments:**
- **Move Method** / **Extract Method** — if other classes manipulate this class's data, move that behavior here
- **Hide Method** — make setters private if fields shouldn't be set after construction
- **Remove Setting Method** — for fields that should be immutable

**Note:** Data classes used as data transfer objects (DTOs) in layered architectures may be fine.

---

### Dead Code
**Signs:** A variable, parameter, field, method, or class is no longer used anywhere.

**Why it happens:** Requirements changed; code was abandoned instead of deleted.

**Treatments:** Just delete it. Source control has the history.

---

### Speculative Generality
**Signs:** Unused hooks, abstract classes, parameters, or methods added "just in case" for future needs.

**Treatments:**
- **Collapse Hierarchy** — remove abstract classes that aren't adding value
- **Inline Class** — fold unused delegation classes
- **Remove Parameter** — remove unused parameters
- **Rename Method** — rename overly abstract names to concrete ones

**When to ignore:** Unit testing infrastructure that looks like dead code but is required by tests.

---

## Couplers

These smells contribute to excessive coupling or show delegation gone too far.

---

### Feature Envy
**Signs:** A method accesses the data of another object more than its own data. It "envies" the other class.

**Why it happens:** Fields were moved to a data class but the operations on them weren't moved along.

**Treatments:**
- **Move Method** — move the method to the class whose data it uses most
- **Extract Method** — if only part of the method has envy, extract that part and move it

**When to ignore:** When behavior is intentionally separated (Strategy, Visitor patterns).

---

### Inappropriate Intimacy
**Signs:** One class uses the internal fields and methods of another class too freely.

**Why it happens:** Classes weren't properly encapsulated; too much coupling at design time.

**Treatments:**
- **Move Method** / **Move Field** — move the accessed parts closer to the accessor
- **Extract Class** — if both classes share common data/behavior, extract a third class
- **Hide Delegate** — have one class delegate to the other instead of reaching through
- **Replace Inheritance with Delegation** — if a subclass is too intimate with its superclass

---

### Message Chains
**Signs:** Code has chains like `a.getB().getC().getD()`. Client depends on navigation structure.

**Why it happens:** Client needs a deeply-nested piece of data and reaches through to get it.

**Treatments:**
- **Hide Delegate** — add a method on the intermediate object to hide the chain
- **Extract Method** + **Move Method** — extract the chain-using code and move it closer to the data

---

### Middle Man
**Signs:** A class does almost nothing except delegate every method to another class.

**Why it happens:** Over-application of Hide Delegate; delegation kept growing until nothing remained.

**Treatments:**
- **Remove Middle Man** — let clients call the end object directly
- **Inline Method** — fold the delegation into the calling code

---

### Incomplete Library Class
**Signs:** A library class doesn't have a method you need, and you can't modify it.

**Treatments:**
- **Introduce Foreign Method** — add the method to your client class and pass the library object as argument
- **Introduce Local Extension** — create a subclass or wrapper of the library class with the additional methods
