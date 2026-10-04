# Design Patterns Reference

Source: https://refactoring.guru/design-patterns

## Table of Contents
- [Creational Patterns](#creational-patterns) — object creation
- [Structural Patterns](#structural-patterns) — object composition
- [Behavioral Patterns](#behavioral-patterns) — object interaction & responsibility

---

## Creational Patterns

Object creation mechanisms that increase flexibility and reuse.

---

### Factory Method
**Also known as:** Virtual Constructor  
**Intent:** Provides an interface for creating objects in a superclass, but allows subclasses to change the type of objects that will be created.

**Problem:** Code is tightly coupled to concrete classes. Adding new variants means modifying existing code and spreading `new ClassName()` calls everywhere.

**Solution:** Replace direct object construction with a factory method. Subclasses override this method to create the specific type they need. All products share a common interface.

**When to use:**
- You don't know ahead of time what class you need to instantiate
- You want subclasses to decide which objects to create
- You want to provide a hook for subclasses in a library/framework

**Pros:** Avoids tight coupling between creator and concrete products. Supports Single Responsibility (creation in one place). Supports Open/Closed (new product types without breaking existing code).  
**Cons:** Can lead to many subclasses; the hierarchy can become complex.

**Relations:** Abstract Factory is built on Factory Methods. Template Method often calls Factory Methods.

---

### Abstract Factory
**Intent:** Produces families of related objects without specifying their concrete classes.

**Problem:** You need to create families of related products (e.g., UI widgets: Button + Checkbox + Dialog) that must be consistent with each other. Hardcoding specific product families makes it hard to swap them.

**Solution:** Declare an abstract factory interface with creation methods for each product type. Implement one concrete factory per product variant/family. Client code works only with abstract interfaces.

**When to use:**
- Code needs to work with multiple families of related products
- You want to swap entire product families (e.g., light theme → dark theme, Windows UI → macOS UI)

**Pros:** Products from one factory are compatible. Avoids tight coupling between client and concrete products. Single Responsibility, Open/Closed.  
**Cons:** Interface may become bloated as new product types are added.

**Relations:** Often implemented with Factory Methods. Can use Singleton for factory objects. Comparable to Builder (different focus: families vs. step-by-step construction).

---

### Builder
**Intent:** Constructs complex objects step by step. Separates construction from representation, producing different representations using the same construction process.

**Problem:** A constructor with many parameters is unwieldy — many parameters are optional, and you end up with "telescoping constructors" or fat objects that accept null/dummy values.

**Solution:** Extract construction steps into a builder object. A Director can orchestrate the steps. Clients call builder methods to set what they need and retrieve the finished object.

**When to use:**
- Constructing complex objects with many optional parameters
- When you want the same construction process to produce different representations
- To build composite trees or other complex structures step by step

**Pros:** Construct objects step-by-step, defer steps, run steps recursively. Reuse the same construction code for different representations. Single Responsibility.  
**Cons:** Increases overall code complexity.

**Relations:** Often used with Composite to build tree structures. Can be implemented as Singleton. Compared to Abstract Factory (both build objects, but Builder focuses on step-by-step construction of a single complex object).

---

### Prototype
**Also known as:** Clone  
**Intent:** Copies existing objects without making code dependent on their classes.

**Problem:** You need to duplicate an object but can't access its private fields from outside. You also don't want to couple the copying code to a specific class.

**Solution:** Delegate cloning to the object itself. All clonable objects implement a `clone()` method that copies both public and private fields.

**When to use:**
- Code shouldn't depend on concrete classes of objects being copied
- You want to reduce the number of subclasses that differ only in initialization
- Objects need to be configured in various ways — clone a pre-configured prototype instead

**Pros:** Clone complex objects without coupling to their classes. Avoid repeated initialization code. Produce complex objects more conveniently.  
**Cons:** Cloning complex objects with circular references can be tricky.

---

### Singleton
**Intent:** Ensures a class has only one instance and provides a global access point to it.

**Problem:** Two separate concerns: (1) ensure a single instance exists (e.g., a shared database connection), (2) provide global access to that instance.

**Solution:** Make the constructor private; provide a static `getInstance()` method that creates the instance on first call and returns the cached instance on subsequent calls.

**When to use:**
- A single shared resource must have only one controlling object (database, config, logger, cache)
- Stricter control over global variables is needed

**Pros:** Guaranteed single instance. Global access point. Lazy initialization.  
**Cons:** Violates Single Responsibility. Masks bad design. Difficult to unit test (tight coupling). Requires special care in multithreaded environments.

---

## Structural Patterns

Explain how to assemble objects and classes into larger, flexible structures.

---

### Adapter
**Also known as:** Wrapper  
**Intent:** Allows objects with incompatible interfaces to collaborate.

**Problem:** You have a class that does what you need, but its interface is incompatible with the rest of your code (e.g., a third-party analytics library expecting JSON but your code uses XML).

**Solution:** Create an adapter that wraps one object and translates calls into a format the other object understands. The adapter implements the target interface and delegates calls (with translation) to the wrapped object.

**When to use:**
- You want to use an existing class but its interface doesn't match what you need
- You want to create a reusable class that works with classes that don't necessarily have compatible interfaces
- Legacy code integration / third-party library adaption

**Pros:** Single Responsibility (data conversion separated from business logic). Open/Closed (add adapters without breaking existing client code).  
**Cons:** Overall code complexity increases.

---

### Bridge
**Intent:** Splits a large class (or closely related classes) into two separate hierarchies — abstraction and implementation — that can be developed independently.

**Problem:** You're extending a class in two independent dimensions (e.g., Shape × Color), causing an explosion of subclasses (`RedCircle`, `BlueSquare`, etc.).

**Solution:** Extract one of the dimensions into a separate hierarchy. The original class holds a reference to an object from the new hierarchy instead of having all state in one place.

**When to use:**
- You want to divide a monolithic class with multiple orthogonal variants
- You need to extend a class in multiple independent dimensions
- Runtime switching of implementations is required

**Pros:** Platform-independent classes and apps. Client code works with high-level abstractions. Open/Closed, Single Responsibility.  
**Cons:** Harder to use with highly cohesive classes.

---

### Composite
**Also known as:** Object Tree  
**Intent:** Composes objects into tree structures to represent part-whole hierarchies, treating individual objects and compositions uniformly.

**Problem:** You have a tree of objects (e.g., a file system, UI widget hierarchy, organizational chart). Client code needs special-case logic to handle leaves vs. containers.

**Solution:** Define a common interface for both leaf and container nodes. Containers implement the interface by delegating work to their children and summing results.

**When to use:**
- Implementing tree-like object structures
- Client code should treat simple and complex elements uniformly

**Pros:** Work with complex tree structures conveniently via polymorphism. Open/Closed.  
**Cons:** Hard to provide a common interface for classes whose functionality differs too much.

---

### Decorator
**Also known as:** Wrapper  
**Intent:** Attaches new behaviors to objects by placing them inside special wrapper objects.

**Problem:** Extending behavior through subclassing causes a combinatorial explosion when many independent features can be combined (e.g., a notification system that can send email + SMS + Slack in any combination).

**Solution:** Wrap objects in decorators that implement the same interface. Decorators forward requests to the wrapped object and can execute additional behavior before or after.

**When to use:**
- Assign extra behaviors to objects at runtime without breaking code that uses those objects
- When extension by subclassing is impractical due to the number of combinations
- When behaviors can be layered/stacked (e.g., logging + caching + compression)

**Pros:** Extend object behavior without making a new subclass. Add/remove at runtime. Combine multiple behaviors by wrapping with several decorators. Single Responsibility.  
**Cons:** Hard to remove a specific wrapper from the wrapper stack. Decorator order matters. Initial config code can look ugly.

---

### Facade
**Intent:** Provides a simplified interface to a library, framework, or complex set of classes.

**Problem:** Your code must work with many objects of a complex subsystem. You have to initialize them, track dependencies, execute in the right order. Business logic becomes tightly coupled to subsystem internals.

**Solution:** A facade class provides a simple interface to the complex subsystem. It doesn't expose everything — just what clients need.

**When to use:**
- You need a simple, clean interface to a complex subsystem
- You want to structure a subsystem into layers
- You want to minimize coupling between your code and a third-party library

**Pros:** Isolates code from subsystem complexity.  
**Cons:** A facade can become a "god object" coupled to everything.

---

### Flyweight
**Intent:** Fits more objects into available RAM by sharing common state among many fine-grained objects.

**Problem:** Creating a large number of similar objects consumes too much memory. Most of the state is common across instances (intrinsic state), only a little varies per instance (extrinsic state).

**Solution:** Extract the shared (intrinsic) state into flyweight objects and share them. Pass the varying (extrinsic) state externally when the flyweight's methods are called.

**When to use:**
- A program needs to support a huge number of similar objects that barely fit into RAM
- Objects contain duplicate states that can be extracted and shared

**Pros:** Significant RAM savings when many similar objects exist.  
**Cons:** Trading RAM for CPU cycles (extrinsic state must be recalculated). Complicates code.

---

### Proxy
**Intent:** Provides a placeholder or surrogate for another object, controlling access to it.

**Problem:** You need to do something before or after accessing a heavy or sensitive object (lazy init, logging, access control, caching), but you can't modify the original class.

**Solution:** Create a proxy class that implements the same interface as the original service. The proxy forwards requests to the service object, performing pre/post work.

**Common proxy types:**
- *Virtual* (lazy initialization of heavy objects)
- *Protection* (access control)
- *Remote* (local representative of a remote object)
- *Caching* (cache results of expensive operations)
- *Logging* (keep history of requests)

**When to use:**
- Lazy initialization of a heavyweight service object
- Access control to a sensitive object
- Caching request results
- Logging service requests

**Pros:** Control service object without clients knowing. Manage service object's lifecycle. Works when service object isn't ready/available.  
**Cons:** Response may be delayed. Code complication.

---

## Behavioral Patterns

Concerned with algorithms and the assignment of responsibilities between objects.

---

### Chain of Responsibility
**Also known as:** CoR, Chain of Command  
**Intent:** Passes requests along a chain of handlers. Each handler decides to process the request or pass it to the next.

**Problem:** You have a series of sequential checks or processing steps (e.g., auth, validation, caching, rate limiting). Chaining them in code becomes a spaghetti mess and steps can't be reused independently.

**Solution:** Extract each check/step into a separate handler with a reference to the next handler. Pass the request down the chain. Any handler can stop propagation.

**When to use:**
- Multiple handlers for a request, determined at runtime
- Handlers must be executed in a specific order
- The set of handlers and their order should change dynamically
- Middleware pipelines, event handling

**Pros:** Control order of request handling. Decouple sender from receivers. Open/Closed.  
**Cons:** Some requests may go unhandled.

---

### Command
**Also known as:** Action, Transaction  
**Intent:** Turns requests into standalone objects containing all request information. Enables parameterization, queuing, logging, and undo operations.

**Problem:** You need to parameterize UI elements with actions, support undo/redo, queue or schedule operations, or implement reversible transactions.

**Solution:** Create a Command interface with an `execute()` method. Each specific command encapsulates its receiver and the call parameters. Invokers call `execute()` without knowing the implementation.

**When to use:**
- You need undoable operations
- You want to parameterize objects with operations
- Scheduling, queuing, or logging operations
- Implementing transactional behavior

**Pros:** Single Responsibility (separate invocation logic). Open/Closed. Implement undo/redo. Assemble complex commands from simple ones (Composite Commands / Macros).  
**Cons:** Code becomes complex (new class layer between senders and receivers).

---

### Iterator
**Intent:** Lets you traverse elements of a collection without exposing its underlying representation.

**Problem:** You have a complex data structure (tree, graph, stack) and need to traverse it. Adding traversal logic to the collection pollutes it, and clients can't traverse the same collection in different ways simultaneously.

**Solution:** Extract traversal into a separate iterator object. The iterator tracks position and exposes a `next()` method. Different iterators can implement different traversal algorithms on the same collection.

**When to use:**
- The underlying collection type should be transparent to traversal code
- Multiple traversal algorithms needed on the same collection
- Uniform interface for traversing different collection types

**Pros:** Single Responsibility (traversal extracted). Open/Closed (new iterators without changing collections). Parallel iteration of same collection.  
**Cons:** Overkill for simple collections. Less efficient than direct traversal for some specialized collections.

---

### Mediator
**Also known as:** Intermediary, Controller  
**Intent:** Reduces chaotic dependencies between objects by restricting direct communications and routing them through a mediator.

**Problem:** Components are directly coupled to each other, making reuse hard. Changing one component may break others. Classic example: a UI form where fields enable/disable/validate each other.

**Solution:** Components communicate only via a mediator interface. The mediator handles routing, correlation, and sequencing of interactions.

**When to use:**
- Multiple objects are tightly coupled in hard-to-change ways
- Reusing a component in another context is difficult because of all its dependencies
- You find yourself creating a huge number of subclasses just to reuse basic behavior

**Pros:** Single Responsibility (communication extracted). Open/Closed. Reduce coupling between components.  
**Cons:** The mediator can become a God Object over time.

---

### Memento
**Also known as:** Snapshot  
**Intent:** Saves and restores an object's previous state without revealing the implementation details.

**Problem:** You want to implement undo/restore but exposing an object's internals to capture state would break encapsulation.

**Solution:** The originator creates snapshots of its own state (mementos). Only the originator can read/write snapshot contents. A caretaker stores mementos without understanding their contents.

**When to use:**
- Undo/redo functionality
- Snapshotting / state rollback
- You need to take snapshots of an object's state to restore it later

**Pros:** Produce snapshots without violating encapsulation. Simplify originator code (caretaker maintains undo history).  
**Cons:** RAM-intensive if clients create mementos frequently. Caretakers must track originator lifecycle.

---

### Observer
**Also known as:** Event-Subscriber, Listener  
**Intent:** Defines a subscription mechanism to notify multiple objects about events happening to an observed object.

**Problem:** Some objects need to know when another object changes, but you don't want to tightly couple them. Polling is wasteful; broadcasting to everyone is noisy.

**Solution:** A publisher maintains a list of subscribers and notifies them by calling their update interface method when interesting events occur. Subscribers can subscribe/unsubscribe dynamically.

**When to use:**
- Changes to one object require changing others, and you don't know how many objects need to change
- Objects should be able to notify other objects without making assumptions about who those objects are
- Event systems, reactive programming, MVC model-view sync

**Pros:** Open/Closed (introduce new subscriber classes without changing publisher). Establish runtime relationships between objects.  
**Cons:** Subscribers are notified in random order. Memory leaks if subscribers forget to unsubscribe (zombie listeners).

---

### State
**Intent:** Lets an object alter its behavior when its internal state changes — it appears to change its class.

**Problem:** A class with state-dependent behavior uses massive `if/switch` blocks that grow unmanageable as states are added.

**Solution:** Extract each state into its own class with a shared interface. The context holds a reference to the current state object and delegates all state-specific behavior to it. Transition = swap the state object.

**When to use:**
- An object behaves differently depending on its state, with many states and frequent state changes
- Class code contains massive conditionals that depend on current state
- Similar state-dependent code is duplicated across multiple classes

**Pros:** Single Responsibility (state-specific code in separate classes). Open/Closed (add states without changing context). Eliminate bulky state-machine conditionals.  
**Cons:** Overkill for a few states or infrequent state changes.

**Relations:** Bridge, State, Strategy (similar structure, different intent). State is like Strategy but states are aware of each other and initiate transitions.

---

### Strategy
**Intent:** Defines a family of algorithms, encapsulates each one, and makes them interchangeable.

**Problem:** A class has multiple behavioral variants and uses conditionals to select the right one. Adding new variants requires modifying the class.

**Solution:** Extract each algorithm into its own class (strategy). The context holds a reference to a strategy and delegates the algorithm work to it. Strategies are interchangeable at runtime.

**When to use:**
- You want to use different variants of an algorithm within an object and switch between them at runtime
- You have a lot of similar classes that differ only in how they execute some behavior
- To isolate the business logic of a class from the algorithm implementation details

**Pros:** Swap algorithms at runtime. Isolate implementation from algorithm-using code. Replace inheritance with composition. Open/Closed.  
**Cons:** Clients must be aware of different strategies. Many modern languages support functional/lambda approaches that achieve the same without the extra classes.

---

### Template Method
**Intent:** Defines the skeleton of an algorithm in a superclass, deferring some steps to subclasses without changing the overall algorithm structure.

**Problem:** Multiple classes implement the same algorithm with only minor differences. The common parts are duplicated everywhere.

**Solution:** Define the algorithm's steps as methods in a base class. "Skeleton" steps are `abstract` (subclasses must implement). Optional steps have default implementations (subclasses can override).

**When to use:**
- You want clients to extend only particular steps of an algorithm, not the whole algorithm
- You have multiple classes with nearly identical algorithms (some different steps)
- Frameworks use Template Method to let users extend hook methods

**Pros:** Let clients override only certain parts. Pull duplicate code into a superclass.  
**Cons:** Template methods can become hard to maintain as they grow. Liskov Substitution violations possible.

**Relations:** Factory Method is a specialization of Template Method. Template Method uses inheritance; Strategy uses composition.

---

### Visitor
**Intent:** Separates algorithms from the objects on which they operate, letting you add new operations to existing object structures without modifying them.

**Problem:** You need to add a new operation to a class hierarchy, but modifying all those classes is risky or impossible (e.g., a library you don't own).

**Solution:** Place the new behavior in a separate visitor class. Pass a visitor object to each element, which calls the appropriate visitor method for its type (double dispatch).

**When to use:**
- An object structure contains many classes with differing interfaces, and you want to perform operations across all of them
- Many distinct/unrelated operations on an object structure without polluting their classes
- Operations change often but the object structure rarely changes

**Pros:** Open/Closed (add new behaviors without changing element classes). Single Responsibility (multiple behaviors in separate classes). Accumulate state across traversal.  
**Cons:** Requires updating all visitors when a class is added to the hierarchy. Can break encapsulation.
