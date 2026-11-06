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
allowed-tools: Read Edit Write Glob Grep Bash(go version:*) Bash(go mod init:*) Bash(go work init:*) Bash(go work use:*) Bash(go build:*) Bash(go test:*) Bash(go vet:*) Bash(gofmt:*) Bash(golangci-lint run:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent AskUserQuestion
---

**Persona:** Go project architect. Right-size structure to problem: scripts stay flat; services get layers only when real complexity justifies them.

**Decisions:** Reuse user's architecture/DI choices and repository conventions. Small new project: simplest adequate structure, manual wiring. Ask only when unresolved architecture or DI choice materially changes requested result.

# Go Project Layout

## Architecture Decision: Ask First

New project: pick structure from its actual responsibilities. 100-line CLI tool needs no layers or DI library.

→ See `samber/cc-skills-golang@golang-design-patterns` skill for architecture guides with file trees and code examples.

## Dependency Injection: Ask Next

Pick library only for concrete lifecycle or composition needs, or on request. See `samber/cc-skills-golang@golang-dependency-injection` skill for full comparison and decision table.

## 12-Factor App

Applications (services, APIs, workers) follow [12-Factor App](https://12factor.net/): config via environment variables, logs to stdout, stateless processes, graceful shutdown, backing services as attached resources, admin tasks as one-off commands (e.g., `cmd/migrate/`).

## Quick Start: Choose Your Project Type

| Project Type | Use When | Key Directories |
| --- | --- | --- |
| **CLI Tool** | Command-line application | `cmd/{name}/`, `internal/`, optional `pkg/` |
| **Library** | Reusable code for others | packages at module root (official go.dev layout), `internal/` for private code; `pkg/` optional convention |
| **Service** | HTTP API, microservice or web app | `cmd/{service}/`, `internal/`, `api/`, `web/` |
| **Monorepo** | Multiple related packages/modules | `go.work`, separate modules per package |
| **Workspace** | Developing multiple local modules | `go.work`, replace directives |

## Module Naming Conventions

### Module Name (go.mod)

Module path in `go.mod`:

- Preserve existing module path exactly: case, vanity domains, semantic-import major-version suffixes.
- New module: use its canonical published import path (commonly `github.com/owner/repository`).
- Confirm fork/replace directives and consumers before changing module identity. Naming preferences never justify breaking import-path rename.

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

Packages MUST be lowercase, singular, matching directory name. → See `samber/cc-skills-golang@golang-naming` skill for complete package naming conventions and examples.

## Directory Layout

Keep `main` packages minimal: parse flags, wire dependencies, call `Run()`. Single-binary module may keep `main` at module root (go.dev/doc/modules/layout allows it). Several binaries: each under `cmd/{name}/`. Business logic goes in `internal/` or importable packages. `internal/` for non-exported packages; `pkg/` only when code is useful to external consumers.

See [directory layout examples](references/directory-layouts.md): universal, small project and library layouts, common mistakes.

## Essential Configuration Files

Every Go project root should include:

- **Makefile** — build automation. See [Makefile template](assets/Makefile)
- **.gitignore** — git ignore patterns. Copy [.gitignore template](assets/gitignore) to `.gitignore`
- **.golangci.yml** — linter config. See `samber/cc-skills-golang@golang-lint` skill for recommended configuration

Application configuration with Cobra + Viper: see [config reference](references/config.md).

## Tests, Benchmarks, and Examples

Co-locate `_test.go` files with code under test. Fixtures go in `testdata/`. See [testing layout](references/testing-layout.md) for file naming, placement, organization.

## Go Workspaces

Use `go.work` for multiple related modules in monorepo. See [workspaces](references/workspaces.md) for setup, structure, commands.

## Initialization Checklist

New Go project:

- [ ] Confirm preferred software architecture (clean, hexagonal, DDD, flat, etc.)
- [ ] Confirm preferred DI approach — see `samber/cc-skills-golang@golang-dependency-injection` skill
- [ ] Decide project type (CLI, library, service, monorepo)
- [ ] Right-size structure to project scope
- [ ] Choose module name (matches repo URL, lowercase, hyphens)
- [ ] Run `go version` to detect current go version
- [ ] Run `go mod init github.com/user/project-name`
- [ ] Create `cmd/{name}/main.go` for entry point
- [ ] Create `internal/` for private code
- [ ] Create `pkg/` only for public libraries
- [ ] Monorepos: initialize `go work`, add modules
- [ ] Run `gofmt -s -w .` for formatting
- [ ] Add `.gitignore` with `/vendor/` and binary patterns
- [ ] Update agent-config guidance only if requested. Preserve existing discovery policies; use Go routing skill's Configure mode for it.

## Related Skills

- → See `samber/cc-skills-golang@golang-cli` skill for CLI tool structure, Cobra/Viper patterns.
- → See `samber/cc-skills-golang@golang-continuous-integration` skill for CI/CD pipeline setup.
- → See `samber/cc-skills-golang@golang-refactoring` skill to move or split existing code into this layout safely: type-alias gradual code repair, staged PRs, no big-bang break.
- → See `samber/cc-skills-golang@golang-how-to` skill's Configure mode for always-load directive and optional `## Required Go skills` block in project's agent-config file (CLAUDE.md, AGENTS.md or equivalent).
