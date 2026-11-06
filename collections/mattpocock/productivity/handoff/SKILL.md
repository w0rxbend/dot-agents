---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Summarise current conversation into handoff document so fresh agent can continue work. Save to user's OS temp directory (`$TMPDIR`, else `/tmp`; `%TEMP%` on Windows), not current workspace. Create file with `mktemp` (unique name, mode 0600), never fixed name in shared `/tmp`.

Include "suggested skills" section naming skills next agent should invoke with Skill tool.

Do not duplicate content already in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL.

Redact sensitive information such as API keys, passwords, personally identifiable information.

If user passed arguments, treat them as next session's focus and tailor doc to it.
