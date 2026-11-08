# Go Workspaces (go.work)

## go.work vs go.mod

| Scenario                                       | Use       |
| ---------------------------------------------- | --------- |
| Single module project                          | `go.mod`  |
| Developing multiple related local modules      | `go.work` |
| Monorepo with separate Go modules              | `go.work` |
| Testing local changes across module boundaries | `go.work` |
| Published library consumed by others           | `go.mod`  |

## Workspace Commands

```bash
go work init                    # Initialize workspace
go work use ./services/auth     # Add module to workspace
go work use -rm ./old-module    # Remove module from workspace
go work sync                    # Sync workspace with module changes
```

## Key Points

- Workspaces remove need for `replace` directives in local development; workspace resolves local modules automatically
- **Do not commit `go.work.sum`** (add to `.gitignore`)
- `go.work` is development-only; it does not change how consumers of your published modules resolve dependencies
- Workspace directory structure examples: see `samber/cc-skills-golang@golang-project-layout` skill
