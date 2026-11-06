<!-- markdownlint-disable ol-prefix -->

# Go Workspaces for Multi-Package Repositories

## Table of Contents

- [When to Use Workspaces](#when-to-use-workspaces)
- [Workspace Structure](#workspace-structure)
- [Creating a Workspace](#creating-a-workspace)
- [Workspace Commands](#workspace-commands)

## When to Use Workspaces

Use Go workspaces (`go.work`) when:

- Developing multiple related modules that import each other
- Building monorepo with separate Go modules
- Testing local changes across module boundaries
- Avoiding `replace` directives in every module

**Don't use workspaces for:**

- Single-module projects
- Projects using only external dependencies
- Simple applications

## Workspace Structure

Monorepo with multiple modules:

```
my-monorepo/
├── go.work                    # Workspace file (see below)
├── pkg/
│   ├── auth/                 # Module 1: github.com/user/my-monorepo/pkg/auth
│   │   ├── go.mod
│   │   ├── cmd/
│   │   │   └── auth-server/
│   │   │       └── main.go
│   │   └── internal/
│   │       └── handler/
│   │           └── auth.go
│   └── user/                 # Module 2: github.com/user/my-monorepo/pkg/user
│       ├── go.mod
│       ├── cmd/
│       │   └── user-server/
│       │       └── main.go
│       └── internal/
│           └── handler/
│               └── user.go
├── cmd/
│   └── api/                 # Module 3: github.com/user/my-monorepo/cmd/api
│       ├── go.mod
│       └── main.go
└── tools/
    └── cli/                  # Module 4: github.com/user/my-monorepo/tools/cli
        ├── go.mod
        └── cmd/
            └── mycli/
                └── main.go
```

## Creating a Workspace

1. **Initialize workspace:**

```bash
go work init
```

Creates `go.work`:

```go
go 1.21

use (
    ./services/auth
    ./services/user
    ./shared/libs
    ./tools/cli
)
```

2. **Add modules to workspace:**

```bash
go work use ./services/auth
go work use ./services/user
go work use ./shared/libs
```

3. **Use modules without replace directives:**

In `services/user/go.mod`:

```go
module github.com/user/my-monorepo/services/user

go 1.21

require github.com/user/my-monorepo/shared/libs v0.0.0
```

Workspace resolves `shared/libs` to local directory automatically.

## Workspace Commands

```bash
go work init              # Initialize new workspace
go work use ./path/to/mod # Add module to workspace
go work use -rm ./path    # Remove module from workspace
go work sync              # Sync workspace with module changes
```
