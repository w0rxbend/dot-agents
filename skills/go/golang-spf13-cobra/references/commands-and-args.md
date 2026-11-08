# Cobra Commands, Hooks, and Args Validators

## Table of Contents

- [The Run\* lifecycle](#the-run-lifecycle)
  - [Which hook to use](#which-hook-to-use)
  - [Inheritance rules](#inheritance-rules)
  - [Execution stops on first error](#execution-stops-on-first-error)
- [Args validators](#args-validators)
  - [Built-in validators](#built-in-validators)
  - [Composing validators with MatchAll](#composing-validators-with-matchall)
  - [Custom validators](#custom-validators)
- [Command registration and ordering](#command-registration-and-ordering)
- [Annotations](#annotations)
- [Hidden and deprecated commands](#hidden-and-deprecated-commands)
- [cobra.CheckErr](#cobracheckerr)

## The Run\* lifecycle

Five run hooks, fixed order:

```
PersistentPreRunE → PreRunE → RunE → PostRunE → PersistentPostRunE
```

Each `*E` hook returns `error`. Non-`*E` variants (`PersistentPreRun`, `PreRun`, `Run`, `PostRun`, `PersistentPostRun`) have signature `func(cmd *cobra.Command, args []string)` — cannot signal failure without `os.Exit` or panic. **Always use `*E` variants.**

### Which hook to use

| Hook | Scope | When to use |
| --- | --- | --- |
| `PersistentPreRunE` | Parent + all descendants | Config init, auth check, telemetry setup — must run before every subcommand |
| `PreRunE` | This command only | Validation for this command only, before `RunE` |
| `RunE` | This command only | Main handler — primary business logic |
| `PostRunE` | This command only | Cleanup, runs only if `RunE` succeeded |
| `PersistentPostRunE` | Parent + all descendants | Global cleanup (close connections, flush buffers) |

### Inheritance rules

`PersistentPreRunE` defined on root command runs before every subcommand. If child command defines **its own** `PersistentPreRunE`, it **replaces** (does not chain) parent's hook. Call parent explicitly if both needed:

```go
var childCmd = &cobra.Command{
    PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
        // call parent's hook first
        if err := rootCmd.PersistentPreRunE(cmd, args); err != nil {
            return err
        }
        // child-specific logic
        return nil
    },
}
```

### Execution stops on first error

If `PersistentPreRunE` returns error, cobra stops — `RunE` and later hooks never run. Use for fail-fast auth checks.

## Args validators

Args validators run before `RunE`. On failure, cobra prints clear error message and exits without calling `RunE`.

### Built-in validators

```go
cobra.NoArgs                        // fails if any positional args provided
cobra.ArbitraryArgs                 // accepts any number of args (default)
cobra.ExactArgs(n int)              // requires exactly n args
cobra.MinimumNArgs(n int)           // requires at least n args
cobra.MaximumNArgs(n int)           // requires at most n args
cobra.RangeArgs(min, max int)       // requires between min and max args
cobra.OnlyValidArgs                 // all args must be in ValidArgs list
cobra.ExactValidArgs(n int)         // exactly n args, all in ValidArgs
```

### Composing validators with MatchAll

```go
var deleteCmd = &cobra.Command{
    Use:       "delete <resource>",
    Args:      cobra.MatchAll(cobra.ExactArgs(1), cobra.OnlyValidArgs),
    ValidArgs: []string{"pod", "service", "deployment"},
    RunE: func(cmd *cobra.Command, args []string) error {
        return doDelete(args[0])
    },
}
```

### Custom validators

Signature: `func(cmd *cobra.Command, args []string) error`

```go
func validatePositiveInt(cmd *cobra.Command, args []string) error {
    if len(args) != 1 {
        return fmt.Errorf("requires exactly 1 arg, got %d", len(args))
    }
    n, err := strconv.Atoi(args[0])
    if err != nil || n <= 0 {
        return fmt.Errorf("argument must be a positive integer, got %q", args[0])
    }
    return nil
}

var cmd = &cobra.Command{
    Args: validatePositiveInt,
    RunE: func(cmd *cobra.Command, args []string) error { /* ... */ },
}
```

Combine custom validators with built-ins using `MatchAll`:

```go
Args: cobra.MatchAll(cobra.MinimumNArgs(1), validateAllPositive),
```

## Command registration and ordering

```go
func init() {
    // groups must be registered before AddCommand
    rootCmd.AddGroup(&cobra.Group{ID: "core", Title: "Core Commands:"})
    rootCmd.AddGroup(&cobra.Group{ID: "management", Title: "Management Commands:"})

    serveCmd.GroupID = "core"
    migrateCmd.GroupID = "management"

    rootCmd.AddCommand(serveCmd, migrateCmd, versionCmd)
}
```

`versionCmd` has no `GroupID` — appears in default section.

## Annotations

Cobra supports arbitrary command annotations for framework-level metadata:

```go
var serveCmd = &cobra.Command{
    Annotations: map[string]string{
        "category": "network",
        "requires-auth": "true",
    },
}

// read in a middleware hook:
if serveCmd.Annotations["requires-auth"] == "true" {
    // enforce auth
}
```

## Hidden and deprecated commands

```go
var internalCmd = &cobra.Command{
    Hidden: true,      // not shown in help, still executable
}

var oldCmd = &cobra.Command{
    Deprecated: "use `newcmd` instead",  // shown in help, prints warning on use
}
```

## cobra.CheckErr

`cobra.CheckErr(err)` convenience helper: if `err != nil`, prints error to `cmd.ErrOrStderr()` and calls `os.Exit(1)`. Use only in `main()` for hard exit — not inside `RunE`, where returning error is preferred.

```go
func main() {
    cobra.CheckErr(rootCmd.Execute())
}
```
