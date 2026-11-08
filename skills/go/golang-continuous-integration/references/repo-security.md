# Repository Security Settings

After creating workflow files, configure repository security settings. Not optional: they make CI pipeline trustworthy.

Get GitHub URL from git remote (e.g., `git remote -v`). For `https://github.com/{owner}/{repo}`, settings links:

- Branch protection: `https://github.com/{owner}/{repo}/settings/branches`
- Actions permissions: `https://github.com/{owner}/{repo}/settings/actions`
- Secrets: `https://github.com/{owner}/{repo}/settings/secrets/actions`
- Environments: `https://github.com/{owner}/{repo}/settings/environments`

## Branch Protection Rules

Configure branch protection rule for `main` (or default branch):

1. **Require a pull request before merging** — no direct pushes to main
2. **Require approvals** (at least 1) — no self-merging without review
3. **Dismiss stale pull request approvals when new commits are pushed** — prevents approving then sneaking in changes
4. **Require status checks to pass before merging** — add all CI workflow job names as required checks (e.g., `Test (Go 1.24)`, `Test (Go stable)`, `Lint`)
5. **Require branches to be up to date before merging** — blocks merging stale PRs untested against latest main
6. **Do not allow bypassing the above settings** — rules apply to admins too

## Workflow Permissions

Set default `GITHUB_TOKEN` to **read-only** at repository level:

1. Go to **Actions permissions** (link above)
2. Workflow permissions MUST follow least privilege. Under **Workflow permissions**, select **"Read repository contents and packages permissions"**
3. Uncheck **"Allow GitHub Actions to create and approve pull requests"** (unless auto-merge needs it; then check it only for that purpose)

Workflows then start without write access. Workflows needing elevated permissions must declare them in `permissions:` block. Defense-in-depth: compromised workflow cannot write to repository unless explicitly granted.

## Fork Pull Request Restrictions

For public/open-source repositories:

1. In **Actions permissions** (link above), set **"Fork pull request workflows from outside collaborators"** to **"Require approval for all outside collaborators"**
2. Stops untrusted forks running workflows that burn your Actions minutes or access secrets
3. NEVER use `pull_request_target` with untrusted code: it has write access to base repo

## Secrets and Environments

- Never put secrets in workflow files. Use **Secrets** settings (link above)
- For release workflows, create **"release" environment** with required reviewers in **Environments** (link above): manual approval gate before publishing
- Rotate `CODECOV_TOKEN` and other third-party tokens periodically

## Permissions Cheat Sheet

| Permission | Workflows that need it | Risk |
| --- | --- | --- |
| `contents: read` | All workflows | **Low** — read-only, default safe |
| `contents: write` | Release, auto-merge | **High** — can modify repo contents, create releases |
| `packages: write` | Docker | **High** — can push container images to GHCR |
| `pull-requests: write` | Auto-merge | **High** — can merge PRs, approve changes |
| `attestations: write` | Docker | **Medium** — can create provenance/SBOM attestations |
| `id-token: write` | Docker | **Medium** — OIDC token for signing attestations |
| `security-events: write` | Security/SAST, Docker | **Medium** — can upload SARIF to Security tab |

Prefer narrowest scope. If workflow only needs `contents: read`, do not grant `contents: write`.
