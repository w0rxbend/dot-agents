---
name: golang-stay-updated
description: "Research current Go releases and ecosystem changes for an upgrade or explicit update request. Use primary sources and check go.mod/toolchain compatibility before recommending changes."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.3.1"
  openclaw:
    emoji: "📰"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(go:*) Bash(golangci-lint:*) Bash(git:*) Agent WebFetch WebSearch
---

# Stay Updated with Go

Answer "what changed in Go / should we upgrade / is this still current?" from primary sources, checked against the project's actual `go.mod`. Do not answer release questions from memory.

## Procedure

1. **Read the project's constraints.**
   ```bash
   go version                       # local toolchain
   go env GOTOOLCHAIN
   grep -E '^(go|toolchain) ' go.mod  # language version and pinned toolchain
   ```
   Also check CI images and Dockerfiles (`golang:` tags) — they often pin a different version than `go.mod`.

2. **Find the current releases from primary sources.**
   - Release history and point releases: <https://go.dev/doc/devel/release>
   - Machine-readable list: <https://go.dev/dl/?mode=json> (current supported releases; add `&include=all` for every release)
   - Per-version release notes: `https://go.dev/doc/go1.N`
   - Security fixes: <https://pkg.go.dev/vuln/> and the golang-announce list
   Go supports the two most recent major releases; anything older gets no security fixes.

3. **Check dependencies.**
   ```bash
   go list -m -u all            # modules with newer versions available
   go run golang.org/x/vuln/cmd/govulncheck@latest ./...   # known vulnerabilities reachable from your code
   ```
   → See `samber/cc-skills-golang@golang-dependency-management` skill for upgrading modules safely, and `samber/cc-skills-golang@golang-pkg-go-dev` skill to query a module's versions, docs and vulnerabilities.

4. **Plan the change.** Bumping the `go` line in `go.mod` raises the minimum for every consumer of a library; for applications it is usually safe after tests pass. Change `go`/`toolchain` only when the user asked to upgrade, then run `go mod tidy`, `go build ./...`, `go vet ./...` and `go test ./...`.

5. **Adopt new language/library features.** → See `samber/cc-skills-golang@golang-modernize` skill for the per-version list of modern idioms and safe rewrites.

6. **Report** the versions found, the source URL for each claim, and what you did or did not change.

## Secondary sources (news, not authority)

| Source | URL |
| --- | --- |
| The Go Blog | <https://go.dev/blog> |
| Go playground | <https://go.dev/play> |
| Go tour | <https://go.dev/tour> |
| Golang Weekly newsletter | <https://golangweekly.com/> |
| r/golang | <https://www.reddit.com/r/golang> |
| Go Forum | <https://forum.golangbridge.org> |
| golang-nuts mailing list | <https://groups.google.com/g/golang-nuts> |

Use these to discover changes, then confirm against the primary sources above before recommending anything.
