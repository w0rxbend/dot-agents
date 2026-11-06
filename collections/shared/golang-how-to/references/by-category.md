# Golang skills — full catalog by category

42 skills. ⭐️ marks skills recommended for all Go projects. ⚙️ marks skills a company-specific skill can supersede.

---

## Table of Contents

- [Code Quality](#code-quality)
  - [`samber/cc-skills-golang@golang-code-style` ⭐️ ⚙️](#sambercc-skills-golanggolang-code-style-%EF%B8%8F-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-documentation` ⭐️ ⚙️](#sambercc-skills-golanggolang-documentation-%EF%B8%8F-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-error-handling` ⭐️ ⚙️](#sambercc-skills-golanggolang-error-handling-%EF%B8%8F-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-lint`](#sambercc-skills-golanggolang-lint)
  - [`samber/cc-skills-golang@golang-naming` ⭐️ ⚙️](#sambercc-skills-golanggolang-naming-%EF%B8%8F-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-safety` ⭐️](#sambercc-skills-golanggolang-safety-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-security` ⭐️ 🧠](#sambercc-skills-golanggolang-security-%EF%B8%8F-)
  - [`samber/cc-skills-golang@golang-structs-interfaces` ⚙️](#sambercc-skills-golanggolang-structs-interfaces-%EF%B8%8F)
- [Architecture & Design](#architecture--design)
  - [`samber/cc-skills-golang@golang-concurrency` ⚙️](#sambercc-skills-golanggolang-concurrency-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-context` ⚙️](#sambercc-skills-golanggolang-context-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-data-structures` ⭐️](#sambercc-skills-golanggolang-data-structures-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-database` ⭐️ ⚙️](#sambercc-skills-golanggolang-database-%EF%B8%8F-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-dependency-injection` ⚙️](#sambercc-skills-golanggolang-dependency-injection-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-design-patterns` ⭐️ ⚙️](#sambercc-skills-golanggolang-design-patterns-%EF%B8%8F-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-modernize` ⭐️](#sambercc-skills-golanggolang-modernize-%EF%B8%8F)
- [QA & Performance](#qa--performance)
  - [`samber/cc-skills-golang@golang-benchmark` 🧠](#sambercc-skills-golanggolang-benchmark-)
  - [`samber/cc-skills-golang@golang-observability` ⚙️](#sambercc-skills-golanggolang-observability-%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-performance` 🧠](#sambercc-skills-golanggolang-performance-)
  - [`samber/cc-skills-golang@golang-testing` ⭐️ 🧠 ⚙️](#sambercc-skills-golanggolang-testing-%EF%B8%8F--%EF%B8%8F)
  - [`samber/cc-skills-golang@golang-troubleshooting` ⭐️ 🧠](#sambercc-skills-golanggolang-troubleshooting-%EF%B8%8F-)
- [Project Setup](#project-setup)
  - [`samber/cc-skills-golang@golang-cli`](#sambercc-skills-golanggolang-cli)
  - [`samber/cc-skills-golang@golang-continuous-integration`](#sambercc-skills-golanggolang-continuous-integration)
  - [`samber/cc-skills-golang@golang-dependency-management`](#sambercc-skills-golanggolang-dependency-management)
  - [`samber/cc-skills-golang@golang-pkg-go-dev`](#sambercc-skills-golanggolang-pkg-go-dev)
  - [`samber/cc-skills-golang@golang-popular-libraries`](#sambercc-skills-golanggolang-popular-libraries)
  - [`samber/cc-skills-golang@golang-project-layout`](#sambercc-skills-golanggolang-project-layout)
  - [`samber/cc-skills-golang@golang-stay-updated`](#sambercc-skills-golanggolang-stay-updated)
- [APIs](#apis)
  - [`samber/cc-skills-golang@golang-graphql`](#sambercc-skills-golanggolang-graphql)
  - [`samber/cc-skills-golang@golang-grpc`](#sambercc-skills-golanggolang-grpc)
  - [`samber/cc-skills-golang@golang-swagger`](#sambercc-skills-golanggolang-swagger)
- [Dependency Injection](#dependency-injection)
  - [`samber/cc-skills-golang@golang-dependency-injection` ⚙️](#sambercc-skills-golanggolang-dependency-injection-%EF%B8%8F-1)
  - [`samber/cc-skills-golang@golang-google-wire`](#sambercc-skills-golanggolang-google-wire)
  - [`samber/cc-skills-golang@golang-uber-dig`](#sambercc-skills-golanggolang-uber-dig)
  - [`samber/cc-skills-golang@golang-uber-fx`](#sambercc-skills-golanggolang-uber-fx)
  - [`samber/cc-skills-golang@golang-samber-do`](#sambercc-skills-golanggolang-samber-do)
- [Frameworks](#frameworks)
  - [`samber/cc-skills-golang@golang-spf13-cobra`](#sambercc-skills-golanggolang-spf13-cobra)
  - [`samber/cc-skills-golang@golang-spf13-viper`](#sambercc-skills-golanggolang-spf13-viper)
- [samber/\*](#samber)
  - [`samber/cc-skills-golang@golang-samber-do`](#sambercc-skills-golanggolang-samber-do-1)
  - [`samber/cc-skills-golang@golang-samber-hot`](#sambercc-skills-golanggolang-samber-hot)
  - [`samber/cc-skills-golang@golang-samber-lo`](#sambercc-skills-golanggolang-samber-lo)
  - [`samber/cc-skills-golang@golang-samber-mo` 🧠](#sambercc-skills-golanggolang-samber-mo-)
  - [`samber/cc-skills-golang@golang-samber-oops`](#sambercc-skills-golanggolang-samber-oops)
  - [`samber/cc-skills-golang@golang-samber-ro` 🧠](#sambercc-skills-golanggolang-samber-ro-)
  - [`samber/cc-skills-golang@golang-samber-slog`](#sambercc-skills-golanggolang-samber-slog)
- [Testing](#testing)
  - [`samber/cc-skills-golang@golang-stretchr-testify`](#sambercc-skills-golanggolang-stretchr-testify)
  - [`samber/cc-skills-golang@golang-testing` ⭐️ 🧠 ⚙️](#sambercc-skills-golanggolang-testing-%EF%B8%8F--%EF%B8%8F-1)

## Code Quality

### `samber/cc-skills-golang@golang-code-style` ⭐️ ⚙️

Golang code formatting, conventions, project-level style consistency — gofmt, goimports, line length, var declarations, blank lines, comment heuristics.

Use when: formatting rules, style review, or project coding standards. Not for naming conventions (→ `golang-naming`), linter configuration (→ `golang-lint`), or doc comments (→ `golang-documentation`).

---

### `samber/cc-skills-golang@golang-documentation` ⭐️ ⚙️

Golang documentation standards — package docs, godoc conventions, example functions, README structure, CHANGELOG, llms.txt, API reference generation.

Use when: writing or reviewing Go doc comments, README files, or API reference. Not for code comments explaining logic (→ `golang-code-style`).

---

### `samber/cc-skills-golang@golang-error-handling` ⭐️ ⚙️

Golang error handling best practices — error creation, wrapping with fmt.Errorf and errors.Is/As, sentinel errors, custom error types, panic recovery.

Use when: writing or reviewing error propagation, wrapping, logging, or recovery patterns. For samber/oops specifics → `golang-samber-oops`. For preventing panics → `golang-safety`.

---

### `samber/cc-skills-golang@golang-lint`

Golang linting — golangci-lint configuration, presets, custom rules, CI integration, nolint suppressions, linter selection, output interpretation.

Use when: setting up or tuning golangci-lint, interpreting lint failures, or deciding which linters to enable. For style conventions not enforced by linters → `golang-code-style`.

---

### `samber/cc-skills-golang@golang-naming` ⭐️ ⚙️

Golang naming conventions across all identifier types — packages, constructors, structs, interfaces, constants, errors, receivers, acronyms, test functions. Covers MixedCaps rules, Get-prefix, utils/helpers anti-patterns.

Use when: naming new type, function, package, or constant. Not for broader formatting (→ `golang-code-style`).

---

### `samber/cc-skills-golang@golang-safety` ⭐️

Defensive Golang coding — prevents panics, silent data corruption, runtime bugs. Nil safety, append aliasing, map concurrent access, float comparison, zero-value design, numeric overflow.

Use when: writing or reviewing code that could panic or silently produce wrong results. Not for external threats (→ `golang-security`) or error handling idioms (→ `golang-error-handling`).

---

### `samber/cc-skills-golang@golang-security` ⭐️ 🧠

Golang security best practices — injection prevention (SQL, command, XSS), cryptography, filesystem/network safety, secrets management, cookie security, tool configuration. Audit and review modes.

Use when: auditing codebase for vulnerabilities, writing security-sensitive code, or reviewing auth/crypto/secrets handling. Not for runtime correctness bugs (→ `golang-safety`).

---

### `samber/cc-skills-golang@golang-structs-interfaces` ⚙️

Golang struct and interface design — composition, embedding, type assertions, interface segregation, struct tags (JSON/YAML/DB), pointer vs value receivers.

Use when: designing types, choosing value vs pointer receivers, writing struct tags, or working with interface hierarchies. For architectural patterns using interfaces → `golang-design-patterns`.

---

## Architecture & Design

### `samber/cc-skills-golang@golang-concurrency` ⚙️

Golang concurrency patterns — goroutines, channels, sync primitives, context cancellation, worker pools, fan-out/fan-in, pipelines, errgroup.

Use when: writing concurrent code, coordinating goroutines, or reviewing for race conditions. For context propagation specifically → `golang-context`. When cancelling goroutines via context, load both.

---

### `samber/cc-skills-golang@golang-context` ⚙️

Idiomatic context.Context usage — creation, cancellation, timeouts, values, propagation patterns, WithoutCancel, common anti-patterns.

Use when: propagating deadlines and cancellation signals, or passing request-scoped values. Not for code that merely accepts ctx as first parameter.

---

### `samber/cc-skills-golang@golang-data-structures` ⭐️

Golang data structures internals and usage — slices (capacity growth, append aliasing), maps, channels, sync primitives, container/\*, generic collections, when to use each.

Use when: choosing data structure, understanding slice/map performance characteristics, or using container/list, container/heap, or ring.

---

### `samber/cc-skills-golang@golang-database` ⭐️ ⚙️

Golang database access patterns — parameter binding, connection pooling, transactions, migrations, sqlboiler/sqlc code generation, query builders.

Use when: writing SQL queries, designing repository patterns, or configuring database connections. For query security (injection) → also consult `golang-security`.

---

### `samber/cc-skills-golang@golang-dependency-injection` ⚙️

Dependency injection patterns in Golang — constructor injection, interface-based DI, wire/dig/fx comparison, when DI is worth the complexity.

Use when: deciding whether to use DI, designing constructor signatures, or comparing DI libraries. For specific DI library → `golang-google-wire`, `golang-uber-dig`, `golang-uber-fx`, or `golang-samber-do`.

---

### `samber/cc-skills-golang@golang-design-patterns` ⭐️ ⚙️

Idiomatic Golang design patterns — functional options, constructors, builder pattern, middleware chains, circuit breaker, architecture guides.

Use when: choosing architectural patterns, designing APIs, or implementing resilience patterns. For type-level design (embedding, receivers) → `golang-structs-interfaces`.

---

### `samber/cc-skills-golang@golang-modernize` ⭐️

Modernize Golang code with recent language features — range-over-int, min/max builtins, iterators, slices/maps/cmp/slog stdlib packages, testing patterns (t.Context, b.Loop, synctest), tooling upgrades.

Use when: upgrading codebase to newer Go version or replacing pre-generics patterns. Not for lint rule enforcement (→ `golang-lint`).

---

## QA & Performance

### `samber/cc-skills-golang@golang-benchmark` 🧠

Golang benchmarking, profiling, performance measurement — pprof, trace, CPU/memory/block profiles, flame graphs, benchstat, CI regression detection, continuous profiling.

Use when: measuring performance, capturing profiles, comparing benchmark runs, or setting up CI regression detection. For applying optimization patterns → `golang-performance`. For debugging crash → `golang-troubleshooting`.

---

### `samber/cc-skills-golang@golang-observability` ⚙️

Golang production observability — structured logging (slog), Prometheus metrics, OpenTelemetry tracing, pprof profiling endpoints, alerting, Grafana dashboards.

Use when: instrumenting service for production monitoring. Not for temporary deep-dive investigation (→ `golang-benchmark`, `golang-performance`).

---

### `samber/cc-skills-golang@golang-performance` 🧠

Golang performance optimization — allocation reduction, CPU efficiency, memory layout, GC tuning, pooling, caching, hot-path optimization.

Use when: applying optimization patterns after profiling. Not for measurement methodology (→ `golang-benchmark`) or debugging workflow (→ `golang-troubleshooting`).

---

### `samber/cc-skills-golang@golang-testing` ⭐️ 🧠 ⚙️

Production-ready Golang tests — table-driven tests, fuzzing, fixtures, goroutine leak detection (goleak), snapshot testing, code coverage, integration tests, parallel tests.

Use when: writing or reviewing tests. For testify-specific APIs → `golang-stretchr-testify`. For measurement methodology → `golang-benchmark`.

---

### `samber/cc-skills-golang@golang-troubleshooting` ⭐️ 🧠

Systematic Golang debugging — common pitfalls, test-driven debugging, pprof capture, Delve debugger, race detection, GODEBUG tracing, production debugging.

Use when: debugging panic, unexpected output, or hard-to-reproduce bug. Not for interpreting profiles (→ `golang-benchmark`) or applying optimization patterns (→ `golang-performance`).

---

## Project Setup

### `samber/cc-skills-golang@golang-cli`

Golang CLI application development — project layout, exit codes, signal handling, I/O patterns, argument parsing, terminal UX.

Use when: building CLI tool from scratch. For cobra-specific APIs → `golang-spf13-cobra`. For viper configuration → `golang-spf13-viper`.

---

### `samber/cc-skills-golang@golang-continuous-integration`

CI/CD pipeline configuration for Golang projects using GitHub Actions — build, test, lint, release workflows.

Use when: setting up or improving CI pipeline for Go project.

---

### `samber/cc-skills-golang@golang-dependency-management`

Golang module dependency strategies — go.mod conventions, versioning, replace directives, tool dependencies, multi-module workspaces.

Use when: managing go.mod, handling replace directives, or structuring multi-module repo.

---

### `samber/cc-skills-golang@golang-pkg-go-dev`

Golang package and module exploration via `godig`, a pkg.go.dev API client (CLI + MCP server) — docs, symbols, versions, importers, licenses, known vulnerabilities.

Use when: looking up module's versions, CVEs, docs/symbols, or importers, or searching pkg.go.dev. For upgrading deps → `golang-dependency-management`; for choosing library → `golang-popular-libraries`.

---

### `samber/cc-skills-golang@golang-popular-libraries`

Curated recommendations for production-ready Golang libraries — when stdlib is enough vs when to reach for a package.

Use when: choosing library for new concern (HTTP, logging, testing, etc.). For deep guidance on specific library → library-specific skill.

---

### `samber/cc-skills-golang@golang-project-layout`

Golang project structure and workspace setup — cmd/internal/pkg conventions, monorepo layout, CLI project structure, when to keep things flat.

Use when: starting new project or restructuring existing one. For architectural patterns within project → `golang-design-patterns`.

---

### `samber/cc-skills-golang@golang-stay-updated`

Resources for staying current with Golang — official channels, community hubs, key people to follow, learning resources.

Use when: tracking Go releases, proposals, community news.

---

## APIs

### `samber/cc-skills-golang@golang-graphql`

GraphQL API development in Golang with gqlgen/graphql-go — schema definition, resolvers, subscriptions, dataloader, federation.

Use when: building GraphQL API in Go.

---

### `samber/cc-skills-golang@golang-grpc`

gRPC in Golang — protobuf organization, service definitions, streaming, interceptors, error codes, code generation workflow.

Use when: building or consuming gRPC service. For OpenAPI/REST documentation → `golang-swagger`.

---

### `samber/cc-skills-golang@golang-swagger`

OpenAPI/Swagger docs with swaggo/swag — annotation comments, code generation, framework integrations (gin, echo, fiber, chi), security definitions.

Use when: generating OpenAPI documentation from Go code annotations.

---

## Dependency Injection

### `samber/cc-skills-golang@golang-dependency-injection` ⚙️

See "Architecture & Design" section above.

---

### `samber/cc-skills-golang@golang-google-wire`

Compile-time dependency injection with google/wire — provider sets, injector generation, wire.Build, structured DI patterns.

Use when: codebase imports `github.com/google/wire` or team has chosen compile-time DI. For runtime DI with reflection → `golang-uber-dig`.

---

### `samber/cc-skills-golang@golang-uber-dig`

Reflection-based DI with uber-go/dig — Provide/Invoke, dig.In/dig.Out, named values, value groups, optional dependencies, Decorate.

Use when: codebase imports `go.uber.org/dig`. For higher-level lifecycle and modules → `golang-uber-fx`.

---

### `samber/cc-skills-golang@golang-uber-fx`

Application framework with uber-go/fx — fx.New, fx.Provide/Invoke, fx.Module, lifecycle hooks, fx.Annotate, fx.Decorate, signal-aware Run.

Use when: codebase imports `go.uber.org/fx`. For raw DI without lifecycle → `golang-uber-dig`.

---

### `samber/cc-skills-golang@golang-samber-do`

Dependency injection with samber/do — type-safe service containers, lifecycle management, scopes, health checks, graceful shutdown.

Use when: codebase imports `github.com/samber/do`.

---

## Frameworks

### `samber/cc-skills-golang@golang-spf13-cobra`

CLI command trees with spf13/cobra — command hierarchy, RunE hooks, flag management, shell completion, usage templates, testing with SetArgs.

Use when: codebase imports `github.com/spf13/cobra`. For configuration layering → `golang-spf13-viper`. For general CLI architecture → `golang-cli`.

---

### `samber/cc-skills-golang@golang-spf13-viper`

Layered configuration with spf13/viper — flag > env > file > KV > default precedence, BindPFlag, hot reload, test isolation, remote KV integration.

Use when: codebase imports `github.com/spf13/viper`. For CLI command structure → `golang-spf13-cobra`. For general CLI architecture → `golang-cli`.

---

## samber/\*

### `samber/cc-skills-golang@golang-samber-do`

See "Dependency Injection" section above.

---

### `samber/cc-skills-golang@golang-samber-hot`

In-memory caching with samber/hot — 9 eviction algorithms (LRU, LFU, TinyLFU, W-TinyLFU, S3FIFO, ARC, SIEVE), TTL, loaders, sharding, stale-while-revalidate, Prometheus metrics.

Use when: codebase imports `github.com/samber/hot`.

---

### `samber/cc-skills-golang@golang-samber-lo`

Functional programming helpers with samber/lo — 500+ type-safe generic functions for slices, maps, channels, strings. Immutable (lo), parallel (lop), mutable (lom), iterators (loi), SIMD.

Use when: codebase imports `github.com/samber/lo`. Not for streaming pipelines (→ `golang-samber-ro`).

---

### `samber/cc-skills-golang@golang-samber-mo` 🧠

Monadic types with samber/mo — Option, Result, Either, Future, IO, Task, State for type-safe nullable values, error handling, functional composition.

Use when: codebase imports `github.com/samber/mo`.

---

### `samber/cc-skills-golang@golang-samber-oops`

Structured error handling with samber/oops — error builders, stack traces, error codes, context attributes, public vs developer messages, panic recovery, APM integration.

Use when: codebase imports `github.com/samber/oops`.

---

### `samber/cc-skills-golang@golang-samber-ro` 🧠

Reactive streams with samber/ro — 150+ type-safe operators, cold/hot observables, 5 subject types, 40+ plugins, automatic backpressure, Go context integration.

Use when: codebase imports `github.com/samber/ro`. Not for finite slice transforms (→ `golang-samber-lo`).

---

### `samber/cc-skills-golang@golang-samber-slog`

Structured logging pipeline with samber/slog-\* packages — multi-handler routing (slog-multi), sampling, formatting, HTTP middleware, 20+ backend sinks.

Use when: codebase imports any `github.com/samber/slog-*` package.

---

## Testing

### `samber/cc-skills-golang@golang-stretchr-testify`

Testing with stretchr/testify — assert, require, mock, and suite packages. Assertions, mock expectations, argument matchers, suite lifecycle, custom matchers.

Use when: codebase imports `github.com/stretchr/testify`. For test architecture and strategy → `golang-testing`.

---

### `samber/cc-skills-golang@golang-testing` ⭐️ 🧠 ⚙️

See "QA & Performance" section above.
