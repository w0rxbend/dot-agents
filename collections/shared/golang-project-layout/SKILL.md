---
name: golang-project-layout
description: "Set up or change Go project/module/workspace layout from actual responsibilities. Keep small tools simple and preserve existing module paths. Existing-code restructuring also needs golang-refactoring guidance."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.4.2"
  openclaw:
    emoji: "📁"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(go:*) Bash(golangci-lint:*) Bash(git:*) Agent AskUserQuestion
---

**Persona:** You are a Go project architect. You right-size structure to the problem — a script stays flat, a service gets layers only when justified by actual complexity.

**Decisions:** Reuse the user's architecture/DI choices and existing repository conventions. For a small new project, start with the simplest adequate structure and manual wiring. Ask only when an unresolved architecture or DI choice materially affects the requested result.

# Go Project Layout

## Architecture Decision: Ask First

When starting a new project, select a structure from its actual responsibilities and the user's established choices. Clarify an unresolved high-impact architecture choice when necessary. A 100-line CLI tool does not need layers or a DI library.

→ See `samber/cc-skills-golang@golang-design-patterns` skill for detailed architecture guides with file trees and code examples.

## Dependency Injection: Ask Next

Use the established DI approach. For a small new project, manual constructor wiring is often sufficient; select a library only for concrete lifecycle or composition needs, or when requested. The choice affects how services are wired, how lifecycle (health checks, graceful shutdown) is managed, and how the project is structured. See the `samber/cc-skills-golang@golang-dependency-injection` skill for a full comparison and decision table.

## 12-Factor App

For applications (services, APIs, workers), follow [12-Factor App](https://12factor.net/) conventions: config via environment variables, logs to stdout, stateless processes, graceful shutdown, backing services as attached resources, and admin tasks as one-off commands (e.g., `cmd/migrate/`).

## Quick Start: Choose Your Project Type

| Project Type | Use When | Key Directories |
| --- | --- | --- |
| **CLI Tool** | Building a command-line application | `cmd/{name}/`, `internal/`, optional `pkg/` |
| **Library** | Creating reusable code for others | `pkg/{name}/`, `internal/` for private code |
| **Service** | HTTP API, microservice, or web app | `cmd/{service}/`, `internal/`, `api/`, `web/` |
| **Monorepo** | Multiple related packages/modules | `go.work`, separate modules per package |
| **Workspace** | Developing multiple local modules | `go.work`, replace directives |

## Module Naming Conventions

### Module Name (go.mod)

Your module path in `go.mod` should:

- Preserve an existing module path exactly, including case, vanity domains, and semantic-import major-version suffixes.
- For a new module, choose its canonical published import path (commonly `github.com/owner/repository`).
- Confirm fork/replace directives and consumers before changing a module identity. Naming preferences do not justify a breaking import-path rename.

**Examples:**

```go
// ✅ Good
module github.com/jdoe/payment-processor
module github.com/company/cli-tool

// ❌ Bad
module myproject
module github.com/jdoe/MyProject
module utils
```

### Package Naming

Packages MUST be lowercase, singular, and match their directory name. → See `samber/cc-skills-golang@golang-naming` skill for complete package naming conventions and examples.

## Directory Layout

All `main` packages must reside in `cmd/` with minimal logic — parse flags, wire dependencies, call `Run()`. Business logic belongs in `internal/` or `pkg/`. Use `internal/` for non-exported packages, `pkg/` only when code is useful to external consumers.

See [directory layout examples](references/directory-layouts.md) for universal, small project, and library layouts, plus common mistakes.

## Essential Configuration Files

Every Go project should include at the root:

- **Makefile** — build automation. See [Makefile template](assets/Makefile)
- **.gitignore** — git ignore patterns. See [.gitignore template](assets/.gitignore)
- **.golangci.yml** — linter config. See the `samber/cc-skills-golang@golang-lint` skill for the recommended configuration

For application configuration with Cobra + Viper, see [config reference](references/config.md).

## Tests, Benchmarks, and Examples

Co-locate `_test.go` files with the code they test. Use `testdata/` for fixtures. See [testing layout](references/testing-layout.md) for file naming, placement, and organization details.

## Go Workspaces

Use `go.work` when developing multiple related modules in a monorepo. See [workspaces](references/workspaces.md) for setup, structure, and commands.

## Initialization Checklist

When starting a new Go project:

- [ ] Confirm preferred software architecture (clean, hexagonal, DDD, flat, etc.)
- [ ] Confirm preferred DI approach — see `samber/cc-skills-golang@golang-dependency-injection` skill
- [ ] Decide project type (CLI, library, service, monorepo)
- [ ] Right-size the structure to the project scope
- [ ] Choose module name (matches repo URL, lowercase, hyphens)
- [ ] Run `go version` to detect the current go version
- [ ] Run `go mod init github.com/user/project-name`
- [ ] Create `cmd/{name}/main.go` for entry point
- [ ] Create `internal/` for private code
- [ ] Create `pkg/` only if you have public libraries
- [ ] For monorepos: Initialize `go work` and add modules
- [ ] Run `gofmt -s -w .` to ensure formatting
- [ ] Add `.gitignore` with `/vendor/` and binary patterns
- [ ] Update agent-config guidance only if requested; preserve existing discovery policies and use the Go routing skill's Configure mode for that task.

## Related Skills

- → See `samber/cc-skills-golang@golang-cli` skill for CLI tool structure and Cobra/Viper patterns.
- → See `samber/cc-skills-golang@golang-dependency-injection` skill for DI approach comparison and wiring.
- → See `samber/cc-skills-golang@golang-lint` skill for golangci-lint configuration.
- → See `samber/cc-skills-golang@golang-continuous-integration` skill for CI/CD pipeline setup.
- → See `samber/cc-skills-golang@golang-design-patterns` skill for architectural patterns.
- → See `samber/cc-skills-golang@golang-refactoring` skill for safely moving or splitting existing code into the layout above via type-alias gradual code repair and staged PRs, without a big-bang break.
- → See `samber/cc-skills-golang@golang-how-to` skill's Configure mode for the always-load directive and optional `## Required Go skills` block written to the project's agent-config file (CLAUDE.md, AGENTS.md, or equivalent).
