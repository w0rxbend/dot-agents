# Deepening

How to safely deepen cluster of shallow modules, given dependencies. Uses vocabulary from [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**.

## Dependency categories

Classify each deepening candidate's dependencies. Category decides how to test deepened module across its seam.

### 1. In-process

Pure computation, in-memory state, no I/O. Always deepenable: merge modules, test through new interface. No adapter needed.

### 2. Local-substitutable

Dependencies with local test stand-ins (PGLite for Postgres, in-memory filesystem). Deepenable if stand-in exists; test deepened module with stand-in running in suite. Seam is internal; no port at module's external interface.

### 3. Remote but owned (Ports & Adapters)

Your own services across network boundary (microservices, internal APIs). Define **port** (interface) at seam. Deep module owns logic; transport injected as **adapter**. Tests use in-memory adapter; production uses HTTP/gRPC/queue adapter.

Recommendation shape: *"Define a port at the seam, implement an HTTP adapter for production and an in-memory adapter for testing, so the logic sits in one deep module even though it's deployed across a network."*

### 4. True external (Mock)

Third-party services you don't control (Stripe, Twilio, etc.). Deepened module takes them as injected port; tests provide mock adapter.

## Seam discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.** No port unless at least two adapters are justified (typically production + test). Single-adapter seam is mere indirection.
- **Internal seams vs external seams.** Don't expose internal seams through interface only because tests use them.

## Testing strategy: replace, don't layer

- Once tests exist at deepened module's interface, old unit tests on shallow modules are waste; delete them.
- Write new tests at deepened module's interface. The **interface is the test surface**.
- Assert on observable outcomes through interface, not internal state.
- Tests should survive internal refactors: they describe behaviour, not implementation. If test must change when implementation changes, it's testing past interface.
