---
name: setup-matt-pocock-skills
description: "Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills."
disable-model-invocation: true
---

# Setup Matt Pocock's Skills

Prompt-driven skill, not deterministic script. Explore, present findings, confirm with user, then write.

## Process

### 1. Explore

Learn repo's starting state. Read what exists; don't assume:

- `git remote -v` and `.git/config`: GitHub repo? Which one?
- `AGENTS.md` and `CLAUDE.md` at repo root: either exists? Either already has `## Agent skills` section?
- `GLOSSARY.md` and `GLOSSARY-MAP.md` at repo root
- `docs/adr/` and any `src/*/docs/adr/` directories
- `docs/agents/`: prior output of this skill?
- `.scratch/`: sign of local-markdown issue tracker convention already in use
- `triage` skill installed? Look for `triage` or `mattpocock--triage` folder beside this one, or either name in available skills. `triage` is user-invoked only, so model's skill list may omit it even when installed: check sibling folders. Decides whether Section B runs at all.
- Monorepo signals: `pnpm-workspace.yaml`, `workspaces` field in `package.json`, or populated `packages/*` with own `src/`. Only large multi-package repos have these. No signals means single-context, which is almost every repo.

### 2. Present findings and ask

Summarise what's present and missing. Then take sections in order: one section, one answer, then next.

Lead each section with recommended answer, so user can accept in one word. Give one-line explainer only when choice truly branches. Skip section entirely when exploration already settled it (Section B when `triage` isn't installed, Section C when there's no monorepo).

**Section A: Issue tracker.**

> Explainer: The "issue tracker" is where issues live for this repo. Skills like `to-tickets`, `triage`, and `to-spec` read from and write to it. They need to know whether to call `gh issue create`, write a markdown file under `.scratch/`, or follow some other workflow you describe. Pick the place you actually track work for this repo.

Skills were designed for GitHub. If `git remote` points at GitHub, propose GitHub. If it points at GitLab (`gitlab.com` or self-hosted host), propose GitLab. Otherwise (or if user prefers), offer:

- **GitHub**: issues in repo's GitHub Issues (uses `gh` CLI)
- **GitLab**: issues in repo's GitLab Issues (uses [`glab`](https://gitlab.com/gitlab-org/cli) CLI)
- **Local markdown**: issues as files under `.scratch/<feature>/` in this repo (good for solo projects or repos without remote)
- **Other** (Jira, Linear, etc.): ask user to describe workflow in one paragraph; skill records it as freeform prose

Record choice in `docs/agents/issue-tracker.md`. GitHub and GitLab templates carry "PRs as a request surface" flag, default **off**. Leave it off; don't raise it.

**Section B: Triage label vocabulary.** Skip entirely if `triage` skill isn't installed (per exploration): uninstalled skill needs no labels.

If installed, ask exactly one question:

> Do you want to keep the default triage labels? (recommended: **yes**)

Defaults: five canonical roles, each label string equal to its name: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. On **yes**, write them as-is. Only if user says no (usually because tracker already uses other names, e.g. `bug:triage` for `needs-triage`), collect overrides so `triage` applies existing labels instead of creating duplicates.

**Section C: Domain docs.** Default to **single-context** (one `GLOSSARY.md` + `docs/adr/` at repo root). Fits almost every repo; write it without asking.

Offer **multi-context** (root `GLOSSARY-MAP.md` pointing to per-context `GLOSSARY.md` files) only when exploration found monorepo signals. Then confirm which layout user wants.

### 3. Confirm and edit

Show user draft of:

- `## Agent skills` block for whichever of `CLAUDE.md` / `AGENTS.md` gets edited (selection rules in step 4)
- Contents of `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, and `docs/agents/triage-labels.md` (last only when `triage` is installed)

Let user edit before writing.

### 4. Write

**Pick the file to edit:**

- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask user which to create; don't pick for them.

Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa); always edit the existing one.

If chosen file already has `## Agent skills` block, update its contents in-place; don't append duplicate. Don't overwrite user edits to surrounding sections.

The block:

```markdown
## Agent skills

### Issue tracker

[one-line summary of where issues are tracked]. See `docs/agents/issue-tracker.md`.

### Triage labels

[one-line summary of the label vocabulary]. See `docs/agents/triage-labels.md`.

### Domain docs

[one-line summary of layout: "single-context" or "multi-context"]. See `docs/agents/domain.md`.
```

Include `### Triage labels` sub-block and write `docs/agents/triage-labels.md` only when `triage` is installed and Section B ran. Otherwise omit both.

If Section B ran on GitHub or GitLab, create each configured label the tracker lacks (`GH_TELEMETRY=false gh label create` / `GLAB_SEND_TELEMETRY=false glab label create`; both CLIs send usage telemetry by default).

Then write docs files, starting from seed templates in this skill folder:

- [issue-tracker-github.md](./issue-tracker-github.md): GitHub issue tracker
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md): GitLab issue tracker
- [issue-tracker-local.md](./issue-tracker-local.md): local-markdown issue tracker
- [triage-labels.md](./triage-labels.md): label mapping (only if `triage` is installed)
- [domain.md](./domain.md): domain doc consumer rules + layout

For "other" issue trackers, write `docs/agents/issue-tracker.md` from scratch from user's description.

### 5. Done

Tell user setup is complete and which engineering skills now read these files. Mention they can edit `docs/agents/*.md` directly later. Re-running this skill is only needed to switch issue trackers or restart from scratch.
