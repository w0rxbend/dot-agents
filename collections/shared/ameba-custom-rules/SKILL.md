---
name: ameba-custom-rules
user-invocable: false
description: Use when writing project-specific Ameba lint rules for Crystal - subclassing Ameba::Rule::Base, matching AST nodes, rule properties, autocorrection, testing with Ameba's spec helpers, and shipping a custom ameba binary. For configuring built-in rules use ameba-configuration; for running Ameba in CI use ameba-integration.
allowed-tools:
  - Bash
  - Read
---

# Ameba Custom Rules

Write custom Ameba rules that enforce project-specific conventions in Crystal code.

The examples below were compiled and their specs run against Ameba 1.7.0 on Crystal 1.22 (Ameba 1.7 requires Crystal 1.19 or newer). The rule API is the same in 1.6.x except where noted. Ameba has no plugin loader: custom rules are compiled into your own `ameba` binary.

## How a rule works

- Every rule is a class inheriting `Ameba::Rule::Base`. Subclasses register themselves automatically; there is no registry to update.
- The rule name is `Group/ClassName`, where the group is the last module in the namespace. `Ameba::Rule::Project::NoSleep` is `Project/NoSleep`, and that is the key used in `.ameba.yml`, `--only` and `# ameba:disable`.
- The default `test(source)` walks the AST with `AST::NodeVisitor` and calls `test(source, node)` for each node whose type has a matching overload. You only write the node overloads.
- `issue_for(node, message)` reports an issue spanning that node; an optional block receives a `corrector` for `--fix`.

The default visitor only dispatches these node types: `Alias`, `ArrayLiteral`, `Assign`, `Block`, `Call`, `Case`, `ClassDef`, `ClassVar`, `ControlExpression`, `Def`, `EnumDef`, `ExceptionHandler`, `Expressions`, `HashLiteral`, `If`, `InstanceVar`, `IsA`, `LibDef`, `MacroExpression`, `ModuleDef`, `MultiAssign`, `NilLiteral`, `ProcLiteral`, `Rescue`, `Select`, `StringInterpolation`, `StringLiteral`, `Union`, `Unless`, `Until`, `Var`, `When`, `While`. Overloads for other types (for example `Crystal::And`, `Crystal::Or`, `Crystal::NumberLiteral`) are never called; see "Custom traversal" below. The return value of `test(source, node)` is ignored, so it cannot stop traversal into children.

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

The doc comment above the class is what `ameba --describe Project/NoSleep` prints.

## Properties

Each entry in `properties do ... end` defines a getter/setter and a YAML key (CamelCase of the name). The type is inferred from the default value.

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

`Enabled`, `Severity` and `Excluded` exist on every rule without declaring them.

## Autocorrection

Pass a block to `issue_for` to make the issue `[Correctable]` and fixable with `ameba --fix`:

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

Note that `NumberLiteral` is not dispatched on its own, but it can be inspected as a child of a dispatched `Call`.

## Custom traversal

For node types the default visitor does not dispatch, or when you need parent/child context, override `test(source)` and walk the AST yourself:

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

Here `visit` returning `false` does stop descent into that node's children, unlike `test(source, node)`. When state must be scoped to a subtree (for example "inside a `rescue`"), set it in `visit` and reset it in `end_visit(node)` for the same node type, or check the subtree directly from the parent node instead of keeping instance-variable flags.

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

`node.location` and `node.end_location` give positions; `node.to_s` prints the source form. Look at Ameba's own rules in `lib/ameba/src/ameba/rule/` for many working patterns, and `include AST::Util` for helpers used there.

## Testing rules

Ameba ships spec helpers. Require them in your spec helper:

```crystal
# spec/spec_helper.cr
require "spec"
require "../src/ameba_rules"
require "ameba/spec/support"
```

`expect_issue` takes source annotated with `# ^^^ error: <message>` under the reported span; `expect_no_issues` asserts a clean source; `expect_correction` checks the `--fix` output:

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

Use this `bin/ameba` in hooks and CI (see ameba-integration). The official `crystal-ameba/github-action` runs its own Ameba image and will not see custom rules.

### Sharing rules across projects

Put the rules in a separate shard whose `src/<name>.cr` requires `ameba` and its rule files, add `ameba` as a regular dependency of that shard, and in each consuming project add the shard as a development dependency and `require "<name>"` before `require "ameba/cli"` in `bin/ameba.cr`. Keep the Ameba version constraint compatible with the projects that consume it.

## Best practices

1. One rule per concern, with a clear `MSG` that says what to do instead.
2. Start from the closest built-in rule's source and adapt it.
3. Write `expect_no_issues` cases for near-misses to keep false positives down.
4. Make thresholds and name lists properties instead of constants.
5. Only add autocorrection when the rewrite is always behaviour-preserving.

## Common pitfalls

1. Writing an overload for a node type the default visitor never dispatches (`And`, `Or`, literals) and wondering why it never fires.
2. Expecting a `false` return from `test(source, node)` to skip children; it is ignored.
3. Keeping per-subtree state in instance variables without resetting it; rules are reused across files.
4. Forgetting that the group name comes from the module (`Ameba::Rule::Project` gives `Project/...`).
5. Using the official GitHub Action and expecting it to run custom rules.

## Resources

- [Ameba repository](https://github.com/crystal-ameba/ameba) - built-in rules in `src/ameba/rule/`, spec helpers in `src/ameba/spec/`
- [Ameba API documentation](https://crystal-ameba.org/ameba/)
- [Crystal compiler AST node reference](https://crystal-lang.org/api/Crystal/Macros/ASTNode.html)
