---
name: golang-lint
description: "Configure or interpret golangci-lint, formatters, exclusions, and CI checks for Go. Match the project's v1/v2 version. Run fixes with exclusive file ownership; parallel reviewers do not justify overlapping autofix edits."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.4.1"
  openclaw:
    emoji: "🧹"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
        - golangci-lint
    install:
      - kind: brew
        formula: golangci-lint
        bins: [golangci-lint]
allowed-tools: Read Edit Write Glob Grep Bash(go build:*) Bash(go test:*) Bash(go vet:*) Bash(go version:*) Bash(golangci-lint:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent
paths:
  - "**/*.go"
  - ".golangci.yml"
---

**Persona:** Go code quality engineer.

**Orchestration mode:** Assign edits by disjoint files or isolated worktrees. Linter categories often hit same lines, so category split alone is not safe edit ownership.

**Modes:**

- **Setup mode** — `.golangci.yml`, linter choice, CI: follow configuration and workflow sections in order.
- **Coding mode** — run read-only lint checks during edits. Run `--fix` only after file owner finishes editing, then inspect diff and rerun affected checks.
- **Interpret/fix mode** — lint output, suppressions, fixes in existing code: start at "Interpreting Output" and "Suppressing Lint Warnings".

**Dependencies:**

- Check project's pinned golangci-lint version first. Prefer its binary release or existing CI install. [official installation guide](https://golangci-lint.run/docs/welcome/install/local/) explains why building with `go install` is not recommended default. v2 source builds use `github.com/golangci/golangci-lint/v2/cmd/golangci-lint`.

# Go Linting

## Overview

Run `golangci-lint` per repository's local and CI workflow.

Existing project configuration decides enabled linters. Small Go project can use tool defaults. Add or expand configuration when requested setup or concrete checks need it. [example configuration](./assets/.golangci.yml) is adaptable starting point, not mandatory policy for every repository.

## Quick Reference

```bash
# Run all configured linters
golangci-lint run ./...

# Auto-fix issues where possible
golangci-lint run --fix ./...

# Format code (golangci-lint v2+)
golangci-lint fmt ./...

# Run a single linter only
golangci-lint run --enable-only govet ./...

# List all available linters
golangci-lint linters

# Verbose output with timing info
golangci-lint run --verbose ./...
```

## Configuration

[recommended .golangci.yml](./assets/.golangci.yml): 33 linters. **[linter reference](./references/linter-reference.md)** covers configuration, linter categories (correctness, style, complexity, performance, security), all 33+ linter descriptions, and when each helps.

## Suppressing Lint Warnings

Use `//nolint` sparingly. Fix root cause first.

```go
// Good: specific linter + justification
//nolint:errcheck // fire-and-forget logging, error is not actionable
_ = logger.Sync()

// Bad: blanket suppression without reason
//nolint
_ = logger.Sync()
```

Rules:

1. **//nolint MUST name linter**: `//nolint:errcheck` not `//nolint`
2. **//nolint MUST include justification comment**: `//nolint:errcheck // reason`
3. **`nolintlint` enforces both rules**: flags bare `//nolint` and missing reasons
4. **NEVER suppress security linters** (gosec, bodyclose, sqlclosecheck) without very strong reason

**[nolint directives](./references/nolint-directives.md)**: when to suppress, writing justifications, per-line vs per-function patterns, anti-patterns.

## Development Workflow

1. **Linters SHOULD run after every significant change**: `golangci-lint run ./...`
2. **Auto-fix where possible**: `golangci-lint run --fix ./...`
3. **Format before commit**: `golangci-lint fmt ./...`
4. **Incremental adoption on legacy code**: set `issues.new-from-rev` in `.golangci.yml` to lint only new/changed code, then clean up old code gradually

Makefile targets (recommended):

```makefile
lint:
	golangci-lint run ./...

lint-fix:
	golangci-lint run --fix ./...

fmt:
	golangci-lint fmt ./...
```

CI pipeline setup (GitHub Actions with `golangci-lint-action`): see `samber/cc-skills-golang@golang-continuous-integration` skill.

## Interpreting Output

Issue format:

```
path/to/file.go:42:10: message describing the issue (linter-name)
```

Name in parentheses is flagging linter. Use it to:

- Look up what linter checks in [reference](./references/linter-reference.md)
- Suppress false positive with `//nolint:linter-name // reason`

## Common Issues

| Problem | Solution |
| --- | --- |
| "deadline exceeded" | Set or raise `run.timeout` in `.golangci.yml`; golangci-lint v2 default is no timeout (`0`) |
| Too many issues on legacy code | Set `issues.new-from-rev: HEAD~1` to lint only new code |
| Linter not found | Check `golangci-lint linters`; may need newer version |
| Linter conflicts | Disable less useful one, with comment saying why |
| v1 config errors after upgrade | Run `golangci-lint migrate` to convert config |
| Slow on large repos | Reduce `run.concurrency` or exclude paths via `linters.exclusions.paths` / `formatters.exclusions.paths` |

## Parallelizing Legacy Codebase Cleanup

If delegation is authorized and available, reviewers can classify security, error, formatting and code-quality findings independently. Run automatic formatting/fixes once, with exclusive ownership of affected files. Split remaining fixes by disjoint package/file sets or isolated worktrees, then integrate and verify. Fixes overlapping files or symbols: apply sequentially.

## Cross-References

- `samber/cc-skills-golang@golang-code-style` skill: style rules linters enforce
- `samber/cc-skills-golang@golang-security` skill: SAST tools beyond linting (gosec, govulncheck)
- `samber/cc-skills-golang@golang-continuous-integration` skill: AI-driven code review in CI using these guidelines
