# Viper Env Binding and Flag Binding

## Table of Contents

- [The binding interaction model](#the-binding-interaction-model)
- [AutomaticEnv vs BindEnv](#automaticenv-vs-bindenv)
- [SetEnvKeyReplacer in depth](#setenvkeyreplacer-in-depth)
- [AllowEmptyEnv](#allowemptyenv)
- [Flag binding](#flag-binding)
- [How pflag binding interacts with precedence](#how-pflag-binding-interacts-with-precedence)
- [Debugging binding](#debugging-binding)

## The binding interaction model

Three settings map env vars to viper keys. Set them together:

```go
viper.SetEnvPrefix("MYAPP")                           // adds MYAPP_ prefix
viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_")) // database.host → MYAPP_DATABASE_HOST
viper.AutomaticEnv()                                   // activates auto-binding
```

Call before any `ReadInConfig` or `viper.Get*` call, typically in root command's `PersistentPreRunE` or `init()`.

## AutomaticEnv vs BindEnv

| Method | Behavior |
| --- | --- |
| `AutomaticEnv()` | Maps every key to env equivalent (prefix and replacer applied) |
| `BindEnv(key, envVars...)` | Binds only given key, to given env var name(s) |

Use `AutomaticEnv` for common case. Use `BindEnv` for env var names outside your prefix/replacer convention (e.g., third-party env vars like `GOOGLE_APPLICATION_CREDENTIALS`).

```go
// Bind a specific non-prefixed env var
viper.BindEnv("google.credentials", "GOOGLE_APPLICATION_CREDENTIALS")
```

## SetEnvKeyReplacer in depth

Viper keys separate nested values with `.`. Env vars cannot contain dots. Replacer maps between them.

```go
// Config file:
// database:
//   host: localhost
//   max_conn: 25

// Without replacer:
viper.SetEnvPrefix("MYAPP")
viper.AutomaticEnv()
viper.GetString("database.host")  // looks for MYAPP_DATABASE.HOST — no match

// With replacer:
viper.SetEnvPrefix("MYAPP")
viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
viper.AutomaticEnv()
viper.GetString("database.host")  // looks for MYAPP_DATABASE_HOST — matches
```

Replacer runs on viper key **before** prefix is prepended: `database.host` → replace `.` with `_` → `database_host` → prepend prefix → `MYAPP_DATABASE_HOST`.

## AllowEmptyEnv

By default viper ignores empty-string env vars: treats them as "not set" and continues down precedence stack. Override:

```go
viper.AllowEmptyEnv(true)
// now MYAPP_PORT="" → viper.GetInt("port") == 0, not the default
```

## Flag binding

Bind pflag after defining it:

```go
func init() {
    rootCmd.PersistentFlags().Int("port", 8080, "listen port")
    viper.BindPFlag("port", rootCmd.PersistentFlags().Lookup("port"))
}
```

Bind whole flag set:

```go
viper.BindPFlags(rootCmd.PersistentFlags())
```

**Timing rule:** Bind flags in `init()` or `PersistentPreRunE`. Binding must happen before `Execute()` parses flags, specifically before any `viper.Get*` call on flag-backed key. Binding after `Execute()` leaves flag's `Changed` state unknown; viper may then not promote flag value to correct precedence layer.

## How pflag binding interacts with precedence

Viper checks `flag.Changed` (did user pass flag explicitly) to tell "flag default" (low priority) from "flag explicitly set" (high priority):

- `flag.Changed == false` (flag has its default): flag treated as not present; falls through to env/file/default.
- `flag.Changed == true` (flag passed on command line): flag value is highest-priority source.

So `viper.GetInt("port")` returns flag value when `--port 9090` passed, else falls back to env `MYAPP_PORT` or config file `port: 8080`.

## Debugging binding

List keys, then print only the non-secret values being debugged. Never print `viper.AllSettings()` in logs or agent output: it dumps env-bound secrets (passwords, tokens, DSNs).

```go
fmt.Println(viper.AllKeys())                   // key names only: [database.host database.max_conn port]
fmt.Println(viper.GetString("database.host"))  // localhost
```

Check env var resolution:

```go
os.Setenv("MYAPP_PORT", "9090")
viper.AutomaticEnv()
fmt.Println(viper.GetInt("port"))  // 9090
```
