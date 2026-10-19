---
name: wiki-changelog
description: "Turn a git commit range into a user-facing changelog or recent-activity summary (Keep a Changelog sections, Conventional Commit parsing, PR/issue links, breaking changes first). Use when asked what changed recently, to summarize commits, or to draft release notes or a CHANGELOG entry; for versioning and tagging policy use git-workflow-and-versioning."
risk: safe
source: community
date_added: "2026-02-27"
---

# Changelog from Git History

Summarize a commit range into a changelog that readers can act on. Every entry must trace back to real commits.

## 1. Pick the range

| Request | Range |
|---|---|
| "Changes since the last release" / next release notes | `$(git describe --tags --abbrev=0)..HEAD` |
| Between two releases | `v1.3.0..v1.4.0` |
| "What changed recently" | `--since="2 weeks ago"` (state the window you chose) |
| A branch or PR | `origin/main..HEAD` |

If there are no tags, use a time window, or ask. State the range in the output.

## 2. Collect commits

```bash
RANGE="$(git describe --tags --abbrev=0)..HEAD"
git log --no-merges --format='%h%x09%ad%x09%an%x09%s' --date=short "$RANGE"
git log --no-merges --format='%h%n%B%n---' "$RANGE"   # bodies: BREAKING CHANGE, Closes #
git log --merges --format='%h %s' "$RANGE"            # "Merge pull request #123 ..."
```

Also check for an existing `CHANGELOG.md` and match its format, headings and link style. Use the README's terminology for features.

## 3. Classify

Parse Conventional Commits first:

| Commit | Section |
|---|---|
| `feat` | Added (or Changed, if it alters existing behavior) |
| `fix` | Fixed |
| `perf` | Changed (performance) |
| `feat!`, `fix!`, or a `BREAKING CHANGE:` footer | Breaking, listed first with migration notes |
| `revert` | Removed or Fixed, depending on what was reverted |
| Security-related fix | Security |
| `refactor`, `test`, `ci`, `build`, `chore`, `style`, `docs` | Omit from user-facing notes, unless they change behavior, requirements or published docs |

Fallback for non-conventional messages: classify by intent ("add/support" = Added, "fix/handle/correct" = Fixed, "remove/drop" = Removed, "deprecate" = Deprecated). If you can't tell, read the diff (`git show --stat <sha>`). Never guess from the subject alone when the impact is unclear.

Dependency bumps get one line ("Updated dependencies"), unless they change requirements (runtime version, peer dependency) or fix a security issue.

## 4. Write

- Group related commits into one entry per user-visible change. Many commits can make one bullet.
- Phrase each entry by user impact ("Exports now include timezone offsets"), not mechanics ("refactor serializer").
- Link the evidence: PR numbers from merge commits or squash subjects (`... (#123)`), issue numbers from `Closes #N` footers, otherwise the short hash.
- Every breaking change gets a migration note: what to change and how.
- No emoji, no marketing tone.
- **Do not invent**: no entries, impacts, numbers or issue links without a commit to back them. If something is unclear, list it under "Needs confirmation" instead of guessing.

## Output format (Keep a Changelog)

```markdown
## [Unreleased] - range v1.4.0..HEAD (23 commits)

### Breaking
- `GET /v1/tasks/all` was removed; use the paginated `GET /v1/tasks` (#412). Migration: follow `next_cursor` until it is null.

### Added
- CSV import for tasks (#398, #405)

### Changed
- Task list loads 50 items per page instead of 20 (#401)

### Fixed
- Recurring due dates no longer drift across DST changes (#407, closes #377)

### Security
- Session cookies are now `SameSite=Lax` by default (a1b2c3d)

### Needs confirmation
- e4f5a6b "tweak retry" - behavior change unclear from the diff
```

For "what changed recently" in chat, use the same sections. You may group by week instead, but keep the links.

## Done When

- The range and commit count are stated, and every bullet links a PR, issue or commit.
- Breaking changes come first and have migration notes, and internal-only commits are omitted or summarized.
- Output matches the existing `CHANGELOG.md` style. Write to the file only if asked; otherwise return it in chat.
