---
name: 12-factor-app
description: The Twelve-Factor App methodology for building scalable, maintainable cloud-native applications. Use when designing backend services, APIs, microservices, or any software-as-a-service application. Triggers on deployment patterns, configuration management, process architecture, logging, and infrastructure decisions.
---

# Community Cloud-Native Applications Best Practices

## When to Apply

Use when:
- Designing new backend services or APIs
- Containerizing apps for Kubernetes or Docker
- Setting up CI/CD pipelines
- Managing configuration across environments
- Adding logging and monitoring
- Planning scaling strategy
- Debugging deployment or environment issues

## Quick Reference

Categories listed in priority order (1 = highest); impact in parentheses.

### 1. Codebase & Version Control (CRITICAL)

- [`code-single-codebase`](references/code-single-codebase.md) - One codebase per app in version control
- [`code-one-app-one-repo`](references/code-one-app-one-repo.md) - Enforce one-to-one mapping between codebase and app
- [`code-deploys-not-branches`](references/code-deploys-not-branches.md) - Represent environments with deploys, not branches
- [`code-shared-as-libraries`](references/code-shared-as-libraries.md) - Factor shared code into libraries managed by dependency manager

### 2. Dependencies (CRITICAL)

- [`dep-explicit-declaration`](references/dep-explicit-declaration.md) - Declare all dependencies explicitly in manifest file
- [`dep-isolate-execution`](references/dep-isolate-execution.md) - Isolate dependencies to prevent system package leakage
- [`dep-no-system-tools`](references/dep-no-system-tools.md) - Never rely on implicit system tools being available
- [`dep-deterministic-builds`](references/dep-deterministic-builds.md) - Use lockfiles for deterministic dependency resolution

### 3. Configuration (CRITICAL)

- [`config-separate-from-code`](references/config-separate-from-code.md) - Strictly separate configuration from code
- [`config-use-env-vars`](references/config-use-env-vars.md) - Store configuration in environment variables
- [`config-no-env-groups`](references/config-no-env-groups.md) - Treat environment variables as granular controls, not grouped environments
- [`config-validate-on-startup`](references/config-validate-on-startup.md) - Validate required configuration at startup
- [`config-never-commit-secrets`](references/config-never-commit-secrets.md) - Never commit secrets or credentials to version control

### 4. Backing Services (HIGH)

- [`svc-as-attached-resources`](references/svc-as-attached-resources.md) - Treat backing services as attached resources
- [`svc-connection-strings`](references/svc-connection-strings.md) - Reference all backing services via connection URLs in config
- [`svc-no-local-vs-remote`](references/svc-no-local-vs-remote.md) - Make no distinction between local and third-party services
- [`svc-detach-attach-without-code`](references/svc-detach-attach-without-code.md) - Services detach and attach without code changes

### 5. Build, Release, Run (HIGH)

- [`build-separate-stages`](references/build-separate-stages.md) - Strictly separate build, release, and run stages
- [`build-immutable-releases`](references/build-immutable-releases.md) - Immutable releases with unique identifiers
- [`build-no-runtime-changes`](references/build-no-runtime-changes.md) - Never modify code at runtime; changes require new release
- [`build-complexity-in-build`](references/build-complexity-in-build.md) - Push complexity into build stage; keep run stage minimal
- [`build-artifact-per-commit`](references/build-artifact-per-commit.md) - One build artifact per commit; deploy same artifact everywhere

### 6. Processes & State (HIGH)

- [`proc-stateless-processes`](references/proc-stateless-processes.md) - Run app as stateless processes
- [`proc-no-sticky-sessions`](references/proc-no-sticky-sessions.md) - Never use sticky sessions; store session data in backing services
- [`proc-no-local-filesystem`](references/proc-no-local-filesystem.md) - Never assume local filesystem persists between requests
- [`proc-compile-at-build`](references/proc-compile-at-build.md) - Compile and bundle assets at build time, not runtime
- [`proc-share-nothing`](references/proc-share-nothing.md) - Processes share nothing with each other

### 7. Concurrency & Scaling (HIGH)

- [`scale-process-model`](references/scale-process-model.md) - Scale out via process model with multiple process types
- [`scale-process-types`](references/scale-process-types.md) - Assign workloads to fitting process types
- [`scale-no-daemonize`](references/scale-no-daemonize.md) - Never daemonize or write PID files; process manager handles that
- [`scale-horizontal-not-vertical`](references/scale-horizontal-not-vertical.md) - Prefer horizontal scaling over vertical
- [`scale-process-formation`](references/scale-process-formation.md) - Define process formation as declarative configuration

### 8. Disposability (HIGH)

- [`disp-disposable-processes`](references/disp-disposable-processes.md) - Processes disposable: start or stop at any moment
- [`disp-fast-startup`](references/disp-fast-startup.md) - Minimize startup time for rapid scaling and recovery
- [`disp-graceful-shutdown`](references/disp-graceful-shutdown.md) - Shut down gracefully on SIGTERM
- [`disp-crash-only`](references/disp-crash-only.md) - Crash-only design that recovers from sudden death
- [`disp-idempotent-operations`](references/disp-idempotent-operations.md) - Idempotent operations, safe to retry after failures

### 9. Port Binding (MEDIUM)

- [`port-self-contained`](references/port-self-contained.md) - App fully self-contained with embedded server
- [`port-export-via-binding`](references/port-export-via-binding.md) - Export services via port binding using PORT environment variable
- [`port-any-protocol`](references/port-any-protocol.md) - Use port binding to export any protocol, not just HTTP

### 10. Dev/Prod Parity (MEDIUM)

- [`parity-minimize-gaps`](references/parity-minimize-gaps.md) - Minimize gaps between development and production
- [`parity-same-backing-services`](references/parity-same-backing-services.md) - Same type and version of backing services in all environments
- [`parity-deploy-frequently`](references/parity-deploy-frequently.md) - Deploy frequently to minimize time gap
- [`parity-developers-deploy`](references/parity-developers-deploy.md) - Involve developers in deploys to minimize personnel gap

### 11. Logging (MEDIUM)

- [`log-event-streams`](references/log-event-streams.md) - Treat logs as event streams, not files
- [`log-no-routing`](references/log-no-routing.md) - Never route or store logs from within app
- [`log-structured-format`](references/log-structured-format.md) - Structured logging for machine-readable event streams
- [`log-unbuffered-stdout`](references/log-unbuffered-stdout.md) - Write logs unbuffered to stdout for real-time streaming

### 12. Admin Processes (MEDIUM)

- [`admin-one-off-processes`](references/admin-one-off-processes.md) - Run admin tasks as one-off processes, not special scripts
- [`admin-same-environment`](references/admin-same-environment.md) - Run admin processes against release with same codebase and config
- [`admin-repl-access`](references/admin-repl-access.md) - Provide REPL access for debugging and data inspection

## How to Use

Read reference files for details and code examples. Production commands in them (migrations, data fixes, REPL writes, deploys, git/image pushes, rollbacks, history rewrites): run only after explicit user confirmation. Heroku CLI sends usage telemetry by default: set `DISABLE_TELEMETRY=true` (export or prefix) wherever `heroku` runs, incl. commands given to user.

- [Section definitions](references/_sections.md) - Category structure and impact levels
- [Rule template](assets/templates/_template.md) - Template for new rules
