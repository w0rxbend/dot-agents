---
name: building-ci-pipelines
description: Design CI pipelines across GitHub Actions, GitLab CI and Argo Workflows - stage layout, caching, test sharding, monorepo affected builds, OIDC and SLSA provenance. Use when designing or speeding up a pipeline or choosing a CI platform; use github-actions-advanced for GitHub workflow syntax and hardening, github-actions-debugger for a failing run.
---

# Building CI Pipelines

## When to Use This Skill

Use for:
- CI setup for new projects
- Automated test workflows
- Container images with security provenance
- Slow CI pipelines (especially monorepos)
- SLSA supply chain security
- Multi-platform builds
- GitOps automation
- Migrating from legacy CI systems

## Platform Selection

**GitHub-hosted** → GitHub Actions (SLSA native, 10K+ actions, OIDC)
**GitLab-hosted** → GitLab CI (parent-child pipelines, built-in security)
**Kubernetes** → Argo Workflows (DAG-based, event-driven)
**Legacy** → Jenkins (migrate when possible)

### Platform Comparison

| Feature | GitHub Actions | GitLab CI | Argo | Jenkins |
|---------|---------------|-----------|------|---------|
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| SLSA | Native | Manual | Good | Manual |
| Monorepo | Good | Excellent | Manual | Plugins |

## Quick Start Patterns

Examples use major-version tags for readability. Real workflows: pin every third-party action to full commit SHA of current release, with `# vX.Y.Z` comment, and declare `permissions:` (see `github-actions-advanced` skill).

### Pattern 1: Basic CI (Lint → Test → Build)

```yaml
# GitHub Actions
name: CI
on: [push, pull_request]

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: npm
      - run: npm ci
      - run: npm run lint

  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: npm
      - run: npm ci
      - run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: npm
      - run: npm ci
      - run: npm run build
```

Each job gets fresh runner, so installs own toolchain and dependencies.

### Pattern 2: Matrix Strategy (Multi-Platform)

```yaml
test:
  runs-on: ${{ matrix.os }}
  strategy:
    matrix:
      os: [ubuntu-latest, windows-latest, macos-latest]
      node-version: [22, 24]
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
    - run: npm test
```

6 jobs (3 OS × 2 Node LTS lines) run in parallel; wall-clock time is about slowest job's. Keep matrix on currently supported Node releases (see Node.js release schedule).

### Pattern 3: Monorepo Affected (Turborepo)

```yaml
build:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Required for affected detection

    - uses: actions/setup-node@v4
      with:
        node-version: 24
        cache: npm

    - run: npm ci

    - name: Build affected
      run: npx turbo run build --filter='...[origin/main]'
      env:
        TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
        TURBO_TEAM: ${{ vars.TURBO_TEAM }}
        TURBO_TELEMETRY_DISABLED: 1  # turbo sends anonymous telemetry by default
```

60-80% CI time reduction for monorepos.

### Pattern 4: SLSA Level 3 Provenance

```yaml
name: SLSA Build
on:
  push:
    tags: ['v*']

permissions:
  id-token: write
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build container
        id: build
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

  provenance:
    needs: build
    permissions:
      id-token: write
      actions: read
      packages: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@vX.Y.Z  # use the current release tag; this generator must be referenced by tag, not SHA
    with:
      image: ghcr.io/${{ github.repository }}
      digest: ${{ needs.build.outputs.digest }}
      registry-username: ${{ github.actor }}
    secrets:
      registry-password: ${{ secrets.GITHUB_TOKEN }}
```

Verification (`slsa-verifier` checks trusted builder and source repo; with cosign, never a bare org-prefix identity regexp: it matches lookalike orgs, see `references/slsa-security-framework.md`):
```bash
slsa-verifier verify-image ghcr.io/myorg/myapp@sha256:abcd... \
  --source-uri github.com/myorg/myapp
```

### Pattern 5: OIDC Federation (No Credentials)

```yaml
deploy:
  runs-on: ubuntu-latest
  permissions:
    id-token: write
    contents: read
  steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
        aws-region: us-east-1

    - name: Deploy
      run: aws s3 sync ./dist s3://my-bucket
```

Benefits: no stored credentials, 1-hour lifetime, full audit trail.

### Pattern 6: Security Scanning

```yaml
security:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Gitleaks (secret detection)
      uses: gitleaks/gitleaks-action@v2

    - name: Snyk (vulnerability scan)
      uses: snyk/actions/node@<pinned-sha> # vX.Y.Z
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        SNYK_DISABLE_ANALYTICS: "1"  # snyk CLI sends usage analytics by default

    - name: SBOM generation
      uses: anchore/sbom-action@v0
      with:
        format: spdx-json
        output-file: sbom.spdx.json
```

## Caching

### Automatic Dependency Caching

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: 24
    cache: 'npm'  # Auto-caches ~/.npm
- run: npm ci
```

`cache:` input differs per setup action: `actions/setup-node` supports npm, yarn, pnpm; `actions/setup-python` supports pip, pipenv, poetry; `actions/setup-go` caches Go modules by default (`cache: true`). Rust or anything else: `actions/cache` (below) or dedicated action like `Swatinem/rust-cache`.

### Manual Cache Control

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin
      ~/.cargo/registry
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-
```

### Multi-Layer Caching (Nx)

```yaml
- name: Nx Cloud (build outputs)
  run: npx nx affected -t build
  env:
    NX_CLOUD_ACCESS_TOKEN: ${{ secrets.NX_CLOUD_ACCESS_TOKEN }}

- name: Vite Cache
  uses: actions/cache@v4
  with:
    path: '**/node_modules/.vite'
    key: vite-${{ hashFiles('package-lock.json') }}

- name: TypeScript Cache
  uses: actions/cache@v4
  with:
    path: '**/tsconfig.tsbuildinfo'
    key: tsc-${{ hashFiles('tsconfig.json') }}
```

Result: 70-90% build time reduction.

## Parallelization

### Job-Level Parallelization

```yaml
jobs:
  unit-tests:
    steps:
      - run: npm run test:unit

  integration-tests:
    steps:
      - run: npm run test:integration

  e2e-tests:
    steps:
      - run: npm run test:e2e
```

All three run simultaneously.

### Test Sharding

```yaml
test:
  strategy:
    matrix:
      shard: [1, 2, 3, 4]
  steps:
    - run: npm test -- --shard=${{ matrix.shard }}/4
```

20min test suite → 5min (4x speedup).

## Language Examples

### Python

```yaml
test:
  strategy:
    matrix:
      python-version: ['3.10', '3.11', '3.12']
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - run: pipx install poetry
    - run: poetry install
    - run: poetry run ruff check .
    - run: poetry run mypy .
    - run: poetry run pytest --cov
```

### Rust

```yaml
test:
  strategy:
    matrix:
      os: [ubuntu-latest, windows-latest, macos-latest]
      rust: [stable, nightly]
  steps:
    - uses: dtolnay/rust-toolchain@<pinned-sha> # mutable branch refs like @master/@stable must be pinned
      with:
        toolchain: ${{ matrix.rust }}
        components: rustfmt, clippy
    - uses: Swatinem/rust-cache@v2
    - run: cargo fmt -- --check
    - run: cargo clippy -- -D warnings
    - run: cargo test
```

### Go

```yaml
test:
  steps:
    - uses: actions/setup-go@v5
      with:
        go-version: '1.23'
        cache: true
    - run: go mod verify
    - uses: golangci/golangci-lint-action@<pinned-sha> # current major
    - run: go test -v -race -coverprofile=coverage.txt ./...
```

### TypeScript

```yaml
test:
  strategy:
    matrix:
      node-version: [22, 24]
  steps:
    - uses: pnpm/action-setup@<pinned-sha> # current major
      with:
        version: <pnpm-version>   # or omit to use packageManager from package.json
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'pnpm'
    - run: pnpm install --frozen-lockfile
    - run: pnpm run lint
    - run: pnpm run type-check
    - run: pnpm test
```

## Best Practices

### Security

**DO:**
- Use OIDC, not long-lived credentials
- Pin actions to full commit SHA with version comment: `actions/checkout@<sha> # vX.Y.Z`; pin CI job images by version and digest (`image:vX.Y.Z@sha256:...`), never `:latest`
- Restrict permissions: `permissions: { contents: read }`
- Scan secrets (Gitleaks) on every commit
- Generate SLSA provenance for releases

**DON'T:**
- Expose secrets in logs
- Use `pull_request_target` without validation
- Trust unverified third-party actions

### Performance

**DO:**
- Use affected detection for monorepos
- Fail fast: `strategy.fail-fast: true`
- Use remote caching (Turborepo/Nx Cloud)

**DON'T:**
- Run long tests in PR checks
- Use generic cache keys

### Debugging

Confirm with user before rerun: it can re-run deploy, publish or release jobs. `ACTIONS_STEP_DEBUG`/`ACTIONS_RUNNER_DEBUG` repo variables change every run repo-wide: confirm first, remove after.

```bash
export GH_TELEMETRY=false  # gh sends usage telemetry by default
# Rerun failed jobs with runner and step debug logging
gh run rerun <run-id> --failed --debug
# Or set repository variables ACTIONS_STEP_DEBUG=true / ACTIONS_RUNNER_DEBUG=true
```

Specific failing run: use `github-actions-debugger` skill.

## Advanced Patterns

Read matching reference when task goes past patterns above:

- [references/github-actions-patterns.md](references/github-actions-patterns.md) - reusable workflows, composite actions, matrix strategies, OIDC setup
- [references/slsa-security-framework.md](references/slsa-security-framework.md) - SLSA levels, provenance generation, cosign verification
- [references/monorepo-ci-strategies.md](references/monorepo-ci-strategies.md) - Turborepo/Nx/Bazel affected detection
- [references/caching-strategies.md](references/caching-strategies.md) - multi-layer caching, Docker layer caching, invalidation

## Examples and helpers

- [examples/github-actions-basic/](examples/github-actions-basic/) - starter lint/test/build workflow
- [examples/github-actions-monorepo/](examples/github-actions-monorepo/) - Turborepo with remote caching
- [scripts/validate_workflow.py](scripts/validate_workflow.py) - checks workflow YAML and common best practices; `actionlint` more complete when installed

## Done when

- Stages run in dependency order, independent jobs in parallel. Critical path measured before and after changes.
- Dependency and build caches hit on second run of unchanged commit.
- Credentials from OIDC or scoped secrets. Actions SHA-pinned. Release artifacts carry provenance where required.

## Related Skills

- `github-actions-advanced` - GitHub workflow syntax, hardening and self-hosted runners
- `github-actions-debugger` - diagnosing failing run
- `testing-strategies` - what to run at which pipeline stage
- `implementing-gitops` - continuous delivery to Kubernetes after CI
- `dependency-scanning` - vulnerability and SBOM scanning stages
