---
name: ameba-custom-rules
user-invocable: false
description: Use when writing project-specific Ameba lint rules for Crystal - subclassing Ameba::Rule::Base, matching AST nodes, rule properties, autocorrection, testing with Ameba's spec helpers, and shipping a custom ameba binary. For configuring built-in rules use ameba-configuration; for running Ameba in CI use ameba-integration.
allowed-tools:
  - Bash(crystal spec:*)
  - Bash(crystal build:*)
  - Bash(bin/ameba:*)
  - Bash(ameba:*)
  - Read
---

# Ameba Custom Rules

Examples below compiled and spec-tested against Ameba 1.7.0 on Crystal 1.22 (Ameba 1.7 requires Crystal 1.19 or newer). Rule API same in 1.6.x except where noted. Ameba has no plugin loader: custom rules compile into your own `ameba` binary.

## How a rule works

- Every rule is class inheriting `Ameba::Rule::Base`. Subclasses self-register; no registry to update.
- Rule name is `Group/ClassName`; group is last module in namespace. `Ameba::Rule::Project::NoSleep` is `Project/NoSleep`. That key is used in `.ameba.yml`, `--only` and `# ameba:disable`.
- Default `test(source)` walks AST with `AST::NodeVisitor`. It calls `test(source, node)` for each node whose type has matching overload. Write only node overloads.
- `issue_for(node, message)` reports issue spanning that node. Optional block receives `corrector` for `--fix`.

Default visitor dispatches only these node types: `Alias`, `ArrayLiteral`, `Assign`, `Block`, `Call`, `Case`, `ClassDef`, `ClassVar`, `ControlExpression`, `Def`, `EnumDef`, `ExceptionHandler`, `Expressions`, `HashLiteral`, `If`, `InstanceVar`, `IsA`, `LibDef`, `MacroExpression`, `ModuleDef`, `MultiAssign`, `NilLiteral`, `ProcLiteral`, `Rescue`, `Select`, `StringInterpolation`, `StringLiteral`, `Union`, `Unless`, `Until`, `Var`, `When`, `While`. Overloads for other types (for example `Crystal::And`, `Crystal::Or`, `Crystal::NumberLiteral`) never called; see "Custom traversal" below. `test(source, node)` return value is ignored; it cannot stop traversal into children.

## Project layout

```
my_app/
  shard.yml
  .ameba.yml
  bin/ameba.cr              # custom ameba entry point
  src/ameba_rules.cr        # requires ameba + all rules
  src/ameba_rules/*.cr      # one file per rule
  spec/ameba_rules/*_spec.cr
```

```yaml
# shard.yml
development_dependencies:
  ameba:
    github: crystal-ameba/ameba
    version: ~> 1.7
```

```crystal
# src/ameba_rules.cr
require "ameba"
require "./ameba_rules/*"
```

## A simple rule

```crystal
# src/ameba_rules/no_sleep.cr
module Ameba::Rule::Project
  # Disallows blocking `sleep` calls in application code.
  #
  # YAML configuration example:
  #
  # ```
  # Project/NoSleep:
  #   Enabled: true
  #   MethodNames: [sleep]
  # ```
  class NoSleep < Base
    properties do
      since_version "1.0.0"   # 1.7+: used by Version / --up-to-version; harmless on 1.6
      description "Disallows blocking `sleep` calls"
      method_names %w[sleep]  # becomes the MethodNames config key
    end

    MSG = "Avoid `%s`; use a timeout or channel instead"

    def test(source, node : Crystal::Call)
      return unless node.obj.nil? && node.name.in?(method_names)

      issue_for node, MSG % node.name
    end
  end
end
```

`ameba --describe Project/NoSleep` prints doc comment above class.

## Properties

Each entry in `properties do ... end` defines getter/setter and YAML key (CamelCase of name). Type inferred from default value.

```crystal
properties do
  description "Limits method length"   # required
  enabled false                        # disabled by default (default: true)
  severity :warning                    # default severity (default: group-based, usually Convention)
  max_lines 30                         # Int32 -> MaxLines
  allowed_names %w[call perform]       # Array(String) -> AllowedNames
end
```

```yaml
# .ameba.yml
Project/MethodLength:
  Enabled: true
  Severity: Error
  MaxLines: 40
  Excluded:
    - spec/**
```

`Enabled`, `Severity` and `Excluded` exist on every rule without declaration.

## Autocorrection

Pass block to `issue_for` to make issue `[Correctable]` and fixable with `ameba --fix`:

```crystal
module Ameba::Rule::Project
  # Reports `x.size == 0` and suggests `x.empty?`.
  class SizeZero < Base
    properties do
      description "Prefers `empty?` over `size == 0`"
    end

    MSG = "Use `empty?` instead of `size == 0`"

    def test(source, node : Crystal::Call)
      return unless node.name == "==" && node.args.size == 1
      return unless (arg = node.args.first).is_a?(Crystal::NumberLiteral) && arg.value == "0"
      return unless (recv = node.obj).is_a?(Crystal::Call) && recv.name == "size" && recv.args.empty?
      return unless size_receiver = recv.obj

      issue_for node, MSG do |corrector|
        corrector.replace(node, "#{size_receiver}.empty?")
      end
    end
  end
end
```

`NumberLiteral` not dispatched on its own, but can be inspected as child of dispatched `Call`.

## Custom traversal

For node types default visitor does not dispatch, or when parent/child context needed, override `test(source)` and walk AST yourself:

```crystal
module Ameba::Rule::Project
  # Reports `true`/`false` literals used directly in `&&` / `||`.
  class LiteralInBooleanOp < Base
    properties do
      description "Reports boolean literals inside && and ||"
    end

    MSG = "Boolean literal in logical expression"

    def test(source)
      source.ast.accept(Visitor.new(self, source))
    end

    def check(source, node : Crystal::And | Crystal::Or)
      {node.left, node.right}.each do |operand|
        issue_for operand, MSG if operand.is_a?(Crystal::BoolLiteral)
      end
    end

    private class Visitor < Crystal::Visitor
      def initialize(@rule : LiteralInBooleanOp, @source : Source)
      end

      def visit(node : Crystal::And | Crystal::Or)
        @rule.check(@source, node)
        true # keep visiting children
      end

      def visit(node : Crystal::ASTNode)
        true
      end
    end
  end
end
```

Unlike `test(source, node)`, `visit` returning `false` does stop descent into that node's children. When state must be scoped to subtree (for example "inside a `rescue`"), set it in `visit` and reset it in `end_visit(node)` for same node type. Or check subtree directly from parent node instead of keeping instance-variable flags.

Line-based rules (like `Layout/LineLength`) override `test(source)` and iterate `source.lines` with `issue_for({line, column}, MSG)`.

## Useful AST accessors

| Node | Accessors |
|---|---|
| `Crystal::Call` | `obj` (receiver or `nil`), `name`, `args`, `named_args`, `block` |
| `Crystal::Def` | `name`, `args`, `body`, `return_type`, `visibility` |
| `Crystal::ClassDef` / `ModuleDef` | `name`, `body`, `superclass` (class) |
| `Crystal::Assign` | `target`, `value` |
| `Crystal::If` / `Unless` | `cond`, `then`, `else` |
| `Crystal::ExceptionHandler` | `body`, `rescues`, `else`, `ensure` |
| `Crystal::StringLiteral` | `value` |

`node.location` and `node.end_location` give positions. `node.to_s` prints source form. See Ameba's own rules in `lib/ameba/src/ameba/rule/` for working patterns. Use `include AST::Util` for helpers used there.

## Testing rules

Ameba ships spec helpers. Require them in spec helper:

```crystal
# spec/spec_helper.cr
require "spec"
require "../src/ameba_rules"
require "ameba/spec/support"
```

`expect_issue` takes source annotated with `# ^^^ error: <message>` under reported span. `expect_no_issues` asserts clean source. `expect_correction` checks `--fix` output:

```crystal
require "../spec_helper"

module Ameba::Rule::Project
  describe NoSleep do
    subject = NoSleep.new

    it "reports sleep" do
      expect_issue subject, <<-CRYSTAL
        sleep 1.second
        # ^^^^^^^^^^^^ error: Avoid `sleep`; use a timeout or channel instead
        CRYSTAL
    end

    it "ignores sleep with a receiver" do
      expect_no_issues subject, <<-CRYSTAL
        worker.sleep 1
        CRYSTAL
    end

    it "honours MethodNames" do
      rule = NoSleep.new
      rule.method_names = %w[nap]
      expect_issue rule, <<-CRYSTAL
        nap
        # ^ error: Avoid `nap`; use a timeout or channel instead
        CRYSTAL
    end
  end

  describe SizeZero do
    it "corrects size == 0" do
      source = expect_issue SizeZero.new, <<-CRYSTAL
        items.size == 0
        # ^^^^^^^^^^^^^ error: Use `empty?` instead of `size == 0`
        CRYSTAL

      expect_correction source, <<-CRYSTAL
        items.empty?
        CRYSTAL
    end
  end
end
```

Run with `crystal spec`.

## Building and running a custom binary

```crystal
# bin/ameba.cr
require "../src/ameba_rules"
require "ameba/cli"   # runs the normal Ameba CLI with your rules included
```

```bash
crystal build -o bin/ameba bin/ameba.cr
bin/ameba --only Project      # just your rules
bin/ameba                     # built-in + custom rules
```

Use this `bin/ameba` in hooks and CI (see ameba-integration). Official `crystal-ameba/github-action` runs its own Ameba image; it will not see custom rules.

### Sharing rules across projects

Put rules in separate shard whose `src/<name>.cr` requires `ameba` and its rule files. Add `ameba` as regular dependency of that shard. In each consuming project, add shard as development dependency. Then `require "<name>"` before `require "ameba/cli"` in `bin/ameba.cr`. Keep Ameba version constraint compatible with consuming projects.

## Best practices

1. One rule per concern, with clear `MSG` saying what to do instead.
2. Start from closest built-in rule's source and adapt it.
3. Write `expect_no_issues` cases for near-misses to keep false positives down.
4. Make thresholds and name lists properties instead of constants.
5. Add autocorrection only when rewrite is always behaviour-preserving.

## Common pitfalls

- Keeping per-subtree state in instance variables without resetting it; rules are reused across files.

## Resources

- [Ameba repository](https://github.com/crystal-ameba/ameba) - built-in rules in `src/ameba/rule/`, spec helpers in `src/ameba/spec/`
- [Ameba API documentation](https://crystal-ameba.org/ameba/)
- [Crystal compiler AST node reference](https://crystal-lang.org/api/Crystal/Macros/ASTNode.html)
