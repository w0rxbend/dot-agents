# Configure Go Skill Guidance

Use this procedure only when user requests repository agent configuration. Go coding, review, or scaffolding task does not by itself include changing AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules, or Copilot instructions.

1. Inspect requested target and existing guidance. Preserve its frontmatter, invocation policies, unrelated content, established team choices. If multiple harness files exist, update only requested files. Their existence does not imply permission to rewrite all.
2. Detect actual module/tool versions and library imports from go.mod, go.sum, go.work, CI, existing code. Select smallest useful set of installed skills. Prefer task-based selection over always loading eleven generic skills.
3. Reuse skill set or target user already specified. Ask only when unresolved choice materially changes result.
4. Add bounded section; update existing section in place, no duplicates. Verify each named skill resolves in target environment. Portable Markdown example:

```markdown
## Go development

Use the repository's go.mod/go.work versions and commands. For a relevant task, consult installed Go guidance for that concern; do not preload the entire skill library. Preserve existing dependency and module choices.
```

If user explicitly asks for fixed required set, name that set and its actual scope. Do not infer always-load policy from tool or language presence. For `.cursor/rules/*.mdc`, preserve rule frontmatter; choose globs from requested scope.

5. Read diff. Confirm unrelated rules and invocation policies remain intact. Report changed files and chosen skill references. New agent session may be needed for loader to rediscover them.
