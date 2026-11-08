# Project Documentation

→ See `samber/cc-skills-golang@golang-continuous-integration` skill for automating changelog generation and release workflows.

## Table of Contents

- [README.md](#readmemd)
  - [Section Order](#section-order)
- [CONTRIBUTING.md](#contributingmd)
  - [The 10-Minute Rule](#the-10-minute-rule)
- [Changelog](#changelog)
  - [Format](#format)
  - [Change Categories](#change-categories)
  - [GitHub Releases as Alternative](#github-releases-as-alternative)
- [Distribution](#distribution)
  - [Dockerfile Best Practices](#dockerfile-best-practices)

## README.md

LICENSE file MUST exist in every project. README is project's front page: keep it simple, clear, scannable. Copy-paste template with empty sections: [templates/README.md](../assets/templates/README.md).

### Section Order

Follow this exact order (all sections are in template):

1. **Title** — project name as `# heading`
2. **Badges** — shields.io pictograms (Go version, license, CI, coverage, Go Report Card)
3. **Summary** — 1-2 sentences on what project does
4. **Demo** — code snippet (libraries), GIF/video (CLIs), or screenshot (web UIs)
5. **Getting Started** — installation + minimal working example
6. **Features / Specification** — longest section, organized by feature area
7. **Contributing** — link to CONTRIBUTING.md or inline if very short
8. **License** — license name + link

Template includes commented-out sections for applications (binary download table, Docker, Homebrew). Uncomment as needed.

---

## CONTRIBUTING.md

Goal: new contributor should be able to clone repo, make change, run tests **in under 10 minutes**.

Copy template from [templates/CONTRIBUTING.md](../assets/templates/CONTRIBUTING.md).

### The 10-Minute Rule

If setup takes more than 10 minutes, add:

| Problem | Solution |
| --- | --- |
| Complex build steps | Add `Makefile` with `make build`, `make test`, `make lint` |
| External service dependencies | Add `docker-compose.yml` for local dev |
| Inconsistent dev environments | Add `.devcontainer/` for VS Code devcontainers |
| Slow test suite | Separate unit tests (fast) from integration tests (build tags) |
| Missing documentation | Add `make help` listing available targets |

---

## Changelog

CHANGELOG MUST be updated for every release, tracking its notable changes. Use [Keep a Changelog](https://keepachangelog.com/) format. Copy template from [templates/CHANGELOG.md](../assets/templates/CHANGELOG.md).

### Format

```markdown
## [1.2.0] - 2026-03-08

### Added

- New `WithTimeout` option for client configuration

### Changed

- Improved retry logic to use exponential backoff

### Fixed

- Race condition in connection pool under heavy load

### Deprecated

- `SetTimeout()` method — use `WithTimeout()` option instead

[1.2.0]: https://github.com/{owner}/{repo}/compare/v1.1.0...v1.2.0
```

### Change Categories

- **Added** — new features
- **Changed** — changes in existing functionality
- **Deprecated** — features that will be removed
- **Removed** — removed features
- **Fixed** — bug fixes
- **Security** — vulnerability fixes

### GitHub Releases as Alternative

For simpler projects, GitHub Releases can replace CHANGELOG file. GoReleaser auto-generates release notes from git commits.

---

## Distribution

**YOU MUST offer multiple installation paths** (binaries, containers, APT/Homebrew/... package managers, source).

### Dockerfile Best Practices

Use multi-stage builds with minimal final image:

```dockerfile
# Build stage
FROM golang:1.27-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /app/binary ./cmd/server

# Final stage
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/binary /binary
ENTRYPOINT ["/binary"]
```
