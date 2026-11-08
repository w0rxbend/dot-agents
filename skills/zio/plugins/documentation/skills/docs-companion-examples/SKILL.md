---
name: docs-companion-examples
description: How to commission and verify a page's companion example files — the standalone runnable Scala a page pulls in with mdoc:embed or SourceFile.print. Use when a documentation page embeds example files rather than relying only on inline mdoc blocks, to delegate the build and check what came back.
allowed-tools: Read, Grep, Glob, Bash(sbt compile), Bash(sbt "runMain:*), Task, Skill
---

# Companion Examples

Runnable examples come in two forms. **Inline** mdoc blocks compile with page; nothing needed here.
**Embedded** files are real `.scala` files in own sbt build, pulled in by `mdoc:embed:<path>` or
`SourceFile.print` (tutorial's "Putting It Together", reference page's "Running the Examples"). Must
exist on disk before mdoc runs.

## Subagents Used by This Skill

[`docs-examples-builder`](references/agents/docs-examples-builder.md) is not installed as Claude Code
agent; role brief lives in `references/agents/`. To delegate with `Task`, start fresh general-purpose
subagent (`subagent_type: "general-purpose"`) whose prompt is full brief text, then task prompt shown.
If you cannot start subagents, do step yourself as separate pass,
following brief exactly. Separation rules hold: fix pass applies only reviewer's verbatim findings;
review pass grades page as written.

## Commissioning the Build

Delegate build to **`docs-examples-builder`** via `Task`. It must NOT share your conversation; it knows
only what you tell it. It already knows decoupled sbt build topology, file templates, and
compile/lint/self-check procedure. Pass only page-specific parameters:

```
Task(
  description: "Build companion examples for <page-id>",
  subagent_type: "general-purpose",  // prompt = full text of references/agents/docs-examples-builder.md, then the text below
  prompt: "Page: <path to the page being documented>
           Embeds this page declares: <every mdoc:embed:<path> or SourceFile.print path it names,
             each of which must end up at exactly that path>
           Requirement: every example must print meaningful output when run, not just compile."
)
```

## Ordering

Commission examples **before** mdoc verification. `mdoc:embed:<path>` fails outright on missing file.

Module reference: prefer ONE module-level example set exercising several types together, not one set
per type. Cross-type workflow is module page's point.

## Verifying what came back

Done when:

- each `mdoc:embed:<path>` or `SourceFile.print` call resolves to real file,
- example code traces to page's blocks, nothing invented beyond glue,
- leaf built and each example ran, not only compiled.

Unresolved embed in later mdoc run: file missing or at wrong path. Fix path or re-commission. Do not
delete embed to make page compile.
