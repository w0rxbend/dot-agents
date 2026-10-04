# Pattern Selection Guide

A decision guide to help match symptoms and problems to the right design pattern. Use this as a triage layer — identify the symptom, find the pattern(s), then read the full entry in `design-patterns.md`.

---

## By Symptom

### "I'm creating objects and the code is getting messy"

| If... | Consider |
|-------|---------|
| You don't know which class to instantiate until runtime | **Factory Method** |
| You need families of related objects that must be compatible | **Abstract Factory** |
| You're constructing an object with many optional parameters | **Builder** |
| You need to copy complex objects without depending on their class | **Prototype** |
| You need exactly one instance of a class globally | **Singleton** |

---

### "My class hierarchy is exploding"

| If... | Consider |
|-------|---------|
| You're creating subclasses to combine behavior variants (e.g., RedCircle, BlueSquare) | **Bridge** (separate dimensions into independent hierarchies) |
| You have an existing class structure and want to add behaviors by combining them | **Decorator** (wrap objects to add behavior) |
| Subclasses differ only in which algorithm they use | **Strategy** (extract algorithm into a separate class) |
| Subclasses represent state-dependent behavior | **State** (extract states into classes) |

---

### "My code is tightly coupled to concrete classes"

| If... | Consider |
|-------|---------|
| You can't swap out the type of objects you create | **Factory Method** or **Abstract Factory** |
| You depend directly on a complex subsystem | **Facade** (simplified interface) |
| The interface of a class is incompatible with your code | **Adapter** (translate the interface) |
| You need to control access to an object | **Proxy** |
| Components are directly communicating with each other | **Mediator** |

---

### "I need to add behavior to objects without modifying them"

| If... | Consider |
|-------|---------|
| Adding behavior to individual objects at runtime | **Decorator** |
| Adding a new operation across an existing class hierarchy | **Visitor** |
| Adding pre/post logic without modifying the target class | **Proxy** |

---

### "I have complex conditional logic"

| If... | Consider |
|-------|---------|
| Switch/if-else based on object type | **Replace Conditional with Polymorphism** → may need **Strategy** or **State** |
| Object behavior changes based on internal state with big conditionals | **State** |
| Multiple algorithm variants selected at runtime | **Strategy** |
| A request must pass through a series of checks | **Chain of Responsibility** |
| A request needs to be routed to different handlers | **Command** or **Chain of Responsibility** |

---

### "I need to notify objects when something changes"

| If... | Consider |
|-------|---------|
| Objects need to react to changes in another object | **Observer** |
| Multiple objects must stay in sync | **Observer** (publisher/subscriber) |
| You want to decouple event producers from consumers | **Observer** |
| Objects need to coordinate through a central point | **Mediator** |

---

### "I need to traverse or operate on a tree/graph structure"

| If... | Consider |
|-------|---------|
| You want to treat leaf and composite nodes uniformly | **Composite** |
| You want to add operations to a tree without changing node classes | **Visitor** |
| You need to traverse a collection without exposing internals | **Iterator** |

---

### "I need undo/redo or state snapshots"

| If... | Consider |
|-------|---------|
| Undo/redo operations, action history | **Command** (encapsulate operations as objects) |
| Saving and restoring an object's state | **Memento** |

---

### "I'm duplicating code across multiple algorithms/steps"

| If... | Consider |
|-------|---------|
| Multiple classes implement the same algorithm with minor differences | **Template Method** |
| The same algorithm has multiple interchangeable implementations | **Strategy** |
| Steps need to be reordered/skipped per context | **Builder** or **Chain of Responsibility** |

---

### "I have memory/performance concerns with many similar objects"

| If... | Consider |
|-------|---------|
| Many objects share most of their state | **Flyweight** (share intrinsic state) |
| Object is expensive to create and rarely changes | **Prototype** (clone pre-built instances) |
| Expensive resource should be created only when first needed | **Proxy** (virtual proxy with lazy init) or **Singleton** |

---

## By Pattern Category

### Creational (How objects are created)
- Need flexibility in object creation → **Factory Method**
- Need product families → **Abstract Factory**
- Need complex step-by-step construction → **Builder**
- Need to clone existing objects → **Prototype**
- Need exactly one instance → **Singleton**

### Structural (How objects are composed)
- Incompatible interfaces → **Adapter**
- Independent variation along two dimensions → **Bridge**
- Part-whole trees → **Composite**
- Add behavior at runtime → **Decorator**
- Simplify complex subsystem → **Facade**
- Share memory-heavy objects → **Flyweight**
- Control access to another object → **Proxy**

### Behavioral (How objects communicate)
- Chain of handlers → **Chain of Responsibility**
- Encapsulate requests as objects → **Command**
- Traverse collections → **Iterator**
- Centralize communication → **Mediator**
- Save/restore state → **Memento**
- One-to-many notification → **Observer**
- State-dependent behavior → **State**
- Interchangeable algorithms → **Strategy**
- Algorithm skeleton with overridable steps → **Template Method**
- Add operations without modifying classes → **Visitor**

---

## Pattern Relationships (Common Confusions)

| Often confused | Key difference |
|----------------|---------------|
| **Adapter** vs **Bridge** | Adapter resolves incompatibility between *existing* classes. Bridge is designed upfront to let abstraction and implementation vary independently. |
| **Decorator** vs **Proxy** | Decorator adds functionality; Proxy controls access. Proxy usually manages the lifecycle of its subject. |
| **Facade** vs **Mediator** | Facade simplifies access to a subsystem (one-way: client → subsystem). Mediator enables communication between objects in a subsystem (multi-directional). |
| **Strategy** vs **State** | Strategy: client picks an algorithm; strategies don't know about each other. State: transitions are managed internally; states are aware of each other. |
| **Template Method** vs **Strategy** | Template Method uses *inheritance* (subclass overrides steps). Strategy uses *composition* (inject the algorithm object). |
| **Command** vs **Strategy** | Command encapsulates a *request* (what to do, to whom, when). Strategy encapsulates an *algorithm* (how to do something). |
| **Composite** vs **Decorator** | Both use recursive composition. Composite aggregates children (tree). Decorator adds behavior by wrapping (chain). |
| **Factory Method** vs **Abstract Factory** | Factory Method creates *one* product. Abstract Factory creates *families* of products. |
| **Iterator** vs **Visitor** | Iterator accesses elements sequentially. Visitor performs an operation on each element. |

---

## Anti-Pattern Check

Before applying a pattern, verify it's actually needed:

- **Don't use Singleton** just because you want a global variable. Prefer dependency injection.
- **Don't use Abstract Factory** if you only have one product family. A simple Factory Method suffices.
- **Don't use Visitor** if the object structure changes often — you'd need to update all visitors.
- **Don't use Mediator** as a dumping ground — it can become a God Object.
- **Don't use Observer** without considering memory leaks from unsubscribed listeners.
- **Don't use Flyweight** unless profiling shows memory is actually a bottleneck.
