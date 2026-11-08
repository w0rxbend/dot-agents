---
name: ameba-configuration
user-invocable: false
description: Use when writing or fixing a Crystal project's .ameba.yml - choosing which Ameba rules run, rule properties, severities, source globs/exclusions and inline disable comments. For running Ameba in CI, hooks or editors use ameba-integration; for writing new rules use ameba-custom-rules.
allowed-tools:
  - Bash(ameba:*)
  - Bash(bin/ameba:*)
  - Read
---

# Ameba Configuration

Facts checked against Ameba source v1.6.4 and v1.7.0. Rule names, properties and CLI flags change between releases. Confirm against installed version before relying on detail:

```bash
ameba --version
ameba --rules                     # every rule known to this binary, with enabled state
ameba --describe Lint/UselessAssign   # description and configurable properties of one rule
```

## The configuration file

Ameba reads `.ameba.yml` from project root. Fallbacks: `~/.ameba.yml`, then `$XDG_CONFIG_HOME/ameba/config.yml` (default `~/.config/ameba/config.yml`). `--config PATH` picks a file; `--ignore-config` (1.7+) skips config.

### Generating a starting point

```bash
ameba --gen-config
```

`--gen-config` does not dump every rule. It runs Ameba with `todo` formatter, writing `.ameba.yml` that **disables or excludes every rule that currently fails** - TODO list for existing codebase. Rules passing today still check new code. Commit it, then delete entries as you fix them. Overwrites existing `.ameba.yml`; back up or diff first.

### Structure

```yaml
# Optional (1.7+): only run rules that existed in this Ameba version,
# so upgrading Ameba does not silently add new failing rules.
Version: "1.7.0"

# Files to inspect. Default: **/*.cr and **/*.ecr
Globs:
  - "**/*.cr"
  - "**/*.ecr"
  - "!spec/fixtures/**"     # a leading ! rejects matches

# Paths removed from the globbed set. Default: lib
Excluded:
  - lib
  - src/generated/**

# Default output formatter when --format is not given
Formatter:
  Name: progress

# Per-rule settings: Enabled, Severity, Excluded, plus rule-specific properties
Lint/UnusedArgument:
  Enabled: true
  IgnoreDefs: true

Layout/LineLength:
  Enabled: true
  MaxLength: 120
  Excluded:
    - spec/**
```

Rule-specific property keys are CamelCase form of rule's `properties` (`max_length` becomes `MaxLength`). Ameba silently ignores unknown rule names and property keys in `.ameba.yml`, so typo does nothing. Check names with `ameba --describe Group/Rule`.

## Rule groups

Ameba 1.6/1.7 groups (full list: `ameba --rules`):

| Group | Purpose | Examples |
|---|---|---|
| `Lint` | Likely bugs, wrong constructs | `Lint/UselessAssign`, `Lint/UnusedArgument`, `Lint/ShadowingOuterLocalVar`, `Lint/UnreachableCode`, `Lint/DebuggerStatement` (`debugger`), `Lint/DebugCalls` (`p`, `pp`, ...), `Lint/NotNil`, `Lint/SpecFocus`, `Lint/Syntax` |
| `Style` | Idiomatic Crystal | `Style/RedundantReturn`, `Style/RedundantBegin`, `Style/IsANil`, `Style/LargeNumbers`, `Style/UnlessElse`, `Style/VerboseBlock` |
| `Naming` | Identifier conventions | `Naming/ConstantNames`, `Naming/MethodNames`, `Naming/TypeNames`, `Naming/VariableNames`, `Naming/PredicateName`, `Naming/QueryBoolMethods`, `Naming/BlockParameterName`, `Naming/Filename` |
| `Performance` | Avoidable allocations | `Performance/AnyInsteadOfEmpty`, `Performance/SizeAfterFilter`, `Performance/CompactAfterMap`, `Performance/FlattenAfterMap` |
| `Metrics` | Complexity | `Metrics/CyclomaticComplexity` (`MaxComplexity`, default 12) |
| `Layout` | Whitespace and length | `Layout/LineLength` (disabled by default, `MaxLength` 140), `Layout/TrailingWhitespace`, `Layout/TrailingBlankLines` |
| `Documentation` | Doc comments | `Documentation/Documentation` (disabled by default) |
| `Typing` (1.7+) | Type restrictions | `Typing/MethodReturnTypeRestriction`, `Typing/MethodParameterTypeRestriction` (disabled by default) |

Older guides use `Style/ConstantNames`, `Style/MethodNames`, `Style/TypeNames`, `Style/PredicateName` and `Style/VariableNames`; Ameba 1.6 moved them to `Naming/*`. Config key for a rule that does not exist is silently ignored, so stale names stop working. (`Lint/NonExistentRule` checks only rule names in `# ameba:disable` comments, not `.ameba.yml`.)

Some rules disabled by default, for example `Layout/LineLength`, `Style/LargeNumbers`, `Documentation/Documentation`, `Typing/*` rules. Enable one with `Enabled: true`, or run all rules once with `ameba --all` to preview reports.

### Commonly tuned properties

```yaml
Metrics/CyclomaticComplexity:
  MaxComplexity: 10

Lint/DebugCalls:
  MethodNames: [p, p!, pp, pp!]

Lint/UnusedArgument:
  IgnoreDefs: true        # default true
  IgnoreBlocks: false
  IgnoreProcs: false

Style/RedundantReturn:
  AllowMultiReturn: true  # allow `return a, b`
  AllowEmptyReturn: true  # allow bare `return`

Naming/BlockParameterName:
  MinNameLength: 3
  AllowedNames: [a, b, e, i, j, k, v, x, y, id, io]

Documentation/Documentation:
  Enabled: true
  IgnoreModules: true
  IgnoreDefs: true
```

Run `ameba --describe <Rule>` for each rule's real properties and defaults before adding others.

## Severity

Three severities, most to least severe: `Error`, `Warning`, `Convention`. Group sets default: `Lint`, `Metrics` and `Performance` default to `Warning`; rest to `Convention`. Override per rule:

```yaml
Lint/UselessAssign:
  Severity: Error

Style/RedundantReturn:
  Severity: Convention
```

One CLI flag applies severity at run time; name depends on version:

- Ameba 1.7+: `--min-severity SEVERITY` - report only issues at or above that severity.
- Ameba 1.6.x and earlier: `--fail-level SEVERITY` - set which severity fails the run.

Default `Convention` (everything counts). `ameba --min-severity warning` (1.7+) or `ameba --fail-level warning` (1.6) ignores convention-level issues. CI use: see ameba-integration.

## Inline disabling

```crystal
# ameba:disable Style/LargeNumbers
time = Time.unix(1483859302)

time = Time.unix(1483859302) # ameba:disable Style/LargeNumbers, Lint/UselessAssign
time = Time.unix(1483859302) # ameba:disable Style, Lint
```

Semantics (from `inline_comments.cr`):

- Directive covers **its own line**, or, as standalone comment line, **the single line directly below it**. No block form: standalone `# ameba:disable X` does not cover rest of method or file; `# ameba:enable` not needed to end it.
- Directive on first line of multi-line expression (`if cond # ameba:disable X`) does not cover lines inside.
- Name rules (`Lint/UselessAssign`) or whole groups (`Lint`).
- `Lint/UnneededDisableDirective` reports directives that no longer suppress anything. `Lint/Syntax` cannot be disabled.

Silence a rule for whole file or directory with its `Excluded:` list in `.ameba.yml`, not comments.

## Example configurations

### Balanced configuration for a new project

```yaml
Excluded:
  - lib
  - spec/fixtures/**

Layout/LineLength:
  Enabled: true
  MaxLength: 120

Metrics/CyclomaticComplexity:
  MaxComplexity: 10

Lint/UselessAssign:
  Severity: Error

Lint/DebugCalls:
  Severity: Error
  Excluded:
    - spec/**

Lint/SpecFocus:
  Severity: Error
```

### Strict configuration

```yaml
Version: "1.7.0"   # 1.7+: pin the rule set; bump deliberately

Documentation/Documentation:
  Enabled: true

Style/LargeNumbers:
  Enabled: true

Typing/MethodReturnTypeRestriction:   # 1.7+
  Enabled: true
```

## Best practices

1. Commit `.ameba.yml` so local runs and CI agree.
2. Prefer rule-level `Excluded:` over global disable, and both over scattered inline comments.
3. Give every disabled rule a YAML comment with reason.
4. After upgrading Ameba, run `ameba --rules` and `ameba` once; fix renamed or new rules. On 1.7+ consider pinning `Version`.
5. Do not enable rules that fight `crystal tool format`; run formatter first.

## Common pitfalls

- Forgetting `**/*.ecr` when overriding `Globs` in web app.

## Resources

- [Ameba repository and README](https://github.com/crystal-ameba/ameba)
- [Ameba API documentation (rule reference)](https://crystal-ameba.org/ameba/)
- `ameba --help`, `ameba --rules`, `ameba --describe <Rule>` for installed version
