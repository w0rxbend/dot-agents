---
name: ameba-configuration
user-invocable: false
description: Use when writing or fixing a Crystal project's .ameba.yml - choosing which Ameba rules run, rule properties, severities, source globs/exclusions and inline disable comments. For running Ameba in CI, hooks or editors use ameba-integration; for writing new rules use ameba-custom-rules.
allowed-tools:
  - Bash
  - Read
---

# Ameba Configuration

Configure Ameba, the static code analysis tool for Crystal, so it enforces the rules your project actually wants.

Facts below were checked against the Ameba source for v1.6.4 and v1.7.0. Rule names, properties and CLI flags change between releases, so confirm against the installed version before relying on a detail:

```bash
ameba --version
ameba --rules                     # every rule known to this binary, with enabled state
ameba --describe Lint/UselessAssign   # description and configurable properties of one rule
```

## The configuration file

Ameba reads `.ameba.yml` from the project root. If none exists it falls back to `~/.ameba.yml`, then `$XDG_CONFIG_HOME/ameba/config.yml` (default `~/.config/ameba/config.yml`). `--config PATH` selects a file explicitly; `--ignore-config` (1.7+) skips it.

### Generating a starting point

```bash
ameba --gen-config
```

`--gen-config` does not dump every rule. It runs Ameba with the `todo` formatter and writes a `.ameba.yml` that **disables or excludes every rule that currently fails** - a TODO list for an existing codebase. Commit it, then delete entries one by one as you fix them. It overwrites an existing `.ameba.yml`, so back up or diff first.

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

Rule-specific property keys are the CamelCase form of the rule's `properties` (for example `max_length` becomes `MaxLength`). Unknown rule names and unknown property keys in `.ameba.yml` are silently ignored, so a typo does nothing - check names with `ameba --describe Group/Rule`.

## Rule groups

Ameba 1.6/1.7 ship these groups (run `ameba --rules` for the full list):

| Group | Purpose | Examples |
|---|---|---|
| `Lint` | Likely bugs and wrong constructs | `Lint/UselessAssign`, `Lint/UnusedArgument`, `Lint/ShadowingOuterLocalVar`, `Lint/UnreachableCode`, `Lint/DebuggerStatement` (`debugger`), `Lint/DebugCalls` (`p`, `pp`, ...), `Lint/NotNil`, `Lint/SpecFocus`, `Lint/Syntax` |
| `Style` | Idiomatic Crystal | `Style/RedundantReturn`, `Style/RedundantBegin`, `Style/IsANil`, `Style/LargeNumbers`, `Style/UnlessElse`, `Style/VerboseBlock` |
| `Naming` | Identifier conventions | `Naming/ConstantNames`, `Naming/MethodNames`, `Naming/TypeNames`, `Naming/VariableNames`, `Naming/PredicateName`, `Naming/QueryBoolMethods`, `Naming/BlockParameterName`, `Naming/Filename` |
| `Performance` | Avoidable allocations | `Performance/AnyInsteadOfEmpty`, `Performance/SizeAfterFilter`, `Performance/CompactAfterMap`, `Performance/FlattenAfterMap` |
| `Metrics` | Complexity | `Metrics/CyclomaticComplexity` (`MaxComplexity`, default 12) |
| `Layout` | Whitespace and length | `Layout/LineLength` (disabled by default, `MaxLength` 140), `Layout/TrailingWhitespace`, `Layout/TrailingBlankLines` |
| `Documentation` | Doc comments | `Documentation/Documentation` (disabled by default) |
| `Typing` (1.7+) | Type restrictions | `Typing/MethodReturnTypeRestriction`, `Typing/MethodParameterTypeRestriction` (disabled by default) |

Older guides use `Style/ConstantNames`, `Style/MethodNames`, `Style/TypeNames`, `Style/PredicateName` and `Style/VariableNames`; those moved to `Naming/*` in Ameba 1.6. A config key naming a rule that does not exist is silently ignored, so stale names just stop working. (`Lint/NonExistentRule` only checks rule names inside `# ameba:disable` comments, not `.ameba.yml`.)

Some rules are disabled by default (for example `Layout/LineLength`, `Style/LargeNumbers`, `Documentation/Documentation`, the `Typing/*` rules). Turn one on with `Enabled: true`, or run every rule once with `ameba --all` to see what they would report.

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

Use `ameba --describe <Rule>` to list each rule's real properties and defaults before adding any others.

## Severity

There are three severities, from most to least severe: `Error`, `Warning`, `Convention`. Defaults come from the group: `Lint`, `Metrics` and `Performance` rules default to `Warning`; the rest default to `Convention`. Override per rule:

```yaml
Lint/UselessAssign:
  Severity: Error

Style/RedundantReturn:
  Severity: Convention
```

Severity matters at run time through one CLI flag, whose name depends on the version:

- Ameba 1.7+: `--min-severity SEVERITY` - only report issues at or above that severity.
- Ameba 1.6.x and earlier: `--fail-level SEVERITY` - change which severity makes the run fail.

Default is `Convention` (everything counts). For example, `ameba --min-severity warning` (1.7+) or `ameba --fail-level warning` (1.6) ignores convention-level issues. See ameba-integration for using this in CI.

## Inline disabling

```crystal
# ameba:disable Style/LargeNumbers
time = Time.unix(1483859302)

time = Time.unix(1483859302) # ameba:disable Style/LargeNumbers, Lint/UselessAssign
time = Time.unix(1483859302) # ameba:disable Style, Lint
```

Semantics (from `inline_comments.cr`):

- A directive applies to **its own line**, or, when it is a comment line by itself, to **the single line directly below it**. There is no block form: a standalone `# ameba:disable X` does not cover the rest of the method or file, and `# ameba:enable` is not needed to end it.
- A directive on the first line of a multi-line expression (`if cond # ameba:disable X`) does not cover the lines inside it.
- You can name rules (`Lint/UselessAssign`) or whole groups (`Lint`).
- `Lint/UnneededDisableDirective` reports directives that no longer suppress anything, and `Lint/Syntax` cannot be disabled.

To silence a rule for a whole file or directory, use that rule's `Excluded:` list in `.ameba.yml` instead of comments.

## Example configurations

### Adopting Ameba on an existing codebase

```bash
ameba --gen-config      # writes .ameba.yml that silences all current failures
git add .ameba.yml
```

New code is checked by every rule that passes today; work down the generated list over time.

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

Then run with `--all` once to see what the remaining disabled-by-default rules would add.

## Best practices

1. Commit `.ameba.yml` so local runs and CI agree.
2. Prefer a rule-level `Excluded:` list to disabling a rule globally, and both to scattered inline comments.
3. Add a YAML comment next to every disabled rule saying why.
4. After upgrading Ameba, run `ameba --rules` and `ameba` once and fix renamed or new rules; on 1.7+ consider pinning `Version`.
5. Do not enable rules that fight `crystal tool format`; run the formatter first.

## Common pitfalls

1. Using rule names from old guides (`Style/MethodNames`, `Style/VariableNames`) - they are `Naming/*` now and the old keys do nothing.
2. Expecting `# ameba:disable` on its own line to disable a block; it covers one line.
3. Assuming `--gen-config` produces a full reference config; it writes a TODO list of currently failing rules and overwrites the existing file.
4. Inventing property names; check `ameba --describe`.
5. Forgetting `**/*.ecr` when overriding `Globs` in a web app.

## Resources

- [Ameba repository and README](https://github.com/crystal-ameba/ameba)
- [Ameba API documentation (rule reference)](https://crystal-ameba.org/ameba/)
- `ameba --help`, `ameba --rules`, `ameba --describe <Rule>` for the installed version
