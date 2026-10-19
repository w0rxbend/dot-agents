# Configure Go Skill Guidance

Use this procedure only when the user requests repository agent configuration. A Go coding, review, or scaffolding task does not by itself include changing AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules, or Copilot instructions.

1. Inspect the requested target and existing guidance. Preserve its frontmatter, invocation policies, unrelated content, and established team choices. If multiple harness files exist, update only the requested files; their existence does not imply permission to rewrite all of them.
2. Detect actual module/tool versions and library imports from go.mod, go.sum, go.work, CI, and existing code. Select the smallest useful set of installed skills. Prefer task-based selection over always loading eleven generic skills.
3. Reuse a skill set or target already specified by the user. Ask only when an unresolved choice materially changes the result.
4. Add a bounded section, updating an existing section in place instead of creating duplicates. Verify that each named skill resolves in the target environment. A portable Markdown example is:

```markdown
## Go development

Use the repository's go.mod/go.work versions and commands. For a relevant task, consult installed Go guidance for that concern; do not preload the entire skill library. Preserve existing dependency and module choices.
```

If the user explicitly asks for a fixed required set, name that set and its actual scope. Do not infer an always-load policy from a tool or language being present. For `.cursor/rules/*.mdc`, preserve the rule frontmatter and choose globs from the requested scope.

5. Read the diff and confirm that unrelated rules and invocation policies remain intact. Report the files changed and the chosen skill references. A new agent session may be needed for its loader to rediscover them.
