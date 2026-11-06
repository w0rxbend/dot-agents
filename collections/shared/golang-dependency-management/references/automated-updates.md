# Automated Dependency Updates

Automate minor/patch dependency updates to cut maintenance and stay current with security fixes. Requires solid CI: tests and linting must pass before any auto-merge.

## Dependabot vs Renovate

| Feature | Dependabot | Renovate |
| --- | --- | --- |
| Platform | GitHub only | GitHub, GitLab, Bitbucket, self-hosted |
| `go mod tidy` | Automatic | Opt-in (`gomodTidy`) |
| Automerge | Separate workflow | Native |
| Grouping | Pattern-based | More flexible rules |
| Monorepo support | Basic | Go workspaces aware |
| Regex managers | No | Yes (Dockerfiles, Makefiles, etc) |

**Renovate is generally more mature and configurable.** Dependabot: simpler setup for GitHub-only projects.

## Auto-Merge Strategy

- **Minor and patch updates**: Auto-merge only after CI passes (tests + lint + govulncheck) and package is low-risk for project
- **Major updates**: Create PR for manual review (may contain breaking changes)
- **Security updates**: Fast-track review; auto-merge patch/minor only after CI passes. Major bumps always get human review

Workflow configuration files (dependabot.yml, renovate.json, auto-merge workflows): see `samber/cc-skills-golang@golang-continuous-integration` skill.

## Update Verification

Before committing dependency update:

1. Run `go test ./...` and `go build ./...`
2. Scan with `govulncheck ./...` or `go tool govulncheck ./...`
3. Release notes/changelogs for libraries touching persistence, serialization, networking, authentication, authorization, cryptography, or public APIs may document breaking changes
4. Major version upgrades may contain breaking changes; package changelog documents them
5. Changelogs and new APIs or patterns in updated version may suggest improvements worth applying to project
