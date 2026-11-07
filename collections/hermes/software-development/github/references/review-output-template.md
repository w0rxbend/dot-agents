# Review Output Template

Structure for PR review summary comments. Copy and fill in sections.

## For PR Summary Comment

```markdown
## Code Review Summary

**Verdict: [Approved ✅ | Changes Requested 🔴 | Reviewed 💬]** ([N] issues, [N] suggestions)

**PR:** #[number] — [title]
**Author:** @[username]
**Files changed:** [N] (+[additions] -[deletions])

### 🔴 Critical
<!-- Issues that MUST be fixed before merge -->
- **file.py:line** — [description]. Suggestion: [fix].

### ⚠️ Warnings
<!-- Issues that SHOULD be fixed, but not strictly blocking -->
- **file.py:line** — [description].

### 💡 Suggestions
<!-- Non-blocking improvements, style preferences, future considerations -->
- **file.py:line** — [description].

### ✅ Looks Good
<!-- Call out things done well — positive reinforcement -->
- [aspect that was done well]

---
*Reviewed by Hermes Agent*
```

## Severity Guide

| Level | Icon | When to use | Blocks merge? |
|-------|------|-------------|---------------|
| Critical | 🔴 | Security vulnerabilities, data loss risk, crashes, broken core features | Yes |
| Warning | ⚠️ | Bugs in non-critical paths, missing error handling, missing tests for new code | Usually yes |
| Suggestion | 💡 | Style, refactoring ideas, performance hints, documentation gaps | No |
| Looks Good | ✅ | Clean patterns, good test coverage, clear naming, smart design | N/A |

## Verdict Decision

- **Approved ✅** — Zero critical/warning items. Only suggestions, or all clear.
- **Changes Requested 🔴** — Any critical or warning item.
- **Reviewed 💬** — Observations only (draft PRs, uncertain findings, informational).

## For Inline Comments

Prefix inline comments with severity icon so they scan fast:

```
🔴 **Critical:** User input passed directly to SQL query — use parameterized queries to prevent injection.
```

```
⚠️ **Warning:** This error is silently swallowed. At minimum, log it.
```

```
💡 **Suggestion:** This could be simplified with a dict comprehension:
`{k: v for k, v in items if v is not None}`
```

```
✅ **Nice:** Good use of context manager here — ensures cleanup on exceptions.
```

## For Local (Pre-Push) Review

When reviewing locally before push, use same structure. Present it as message to user, not PR comment. Skip PR metadata header; start with severity sections.
