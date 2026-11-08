---
name: docs-reduce-redundancy
description: Remove redundant content from ZIO-ecosystem library documentation (Docusaurus + mdoc). Use, in such a repo, when sections repeat information unnecessarily, type definitions appear multiple times, concepts are introduced more than once, or transition words clutter meaning. Reduces cognitive load through deduplication and strategic cross-referencing.
argument-hint: "[path/to/doc.md]"
allowed-tools: Read, Edit, Grep, Bash(sbt "docs/mdoc --in:*)
---

# Reduce Redundancy from Documentation

## Agent Workflow

**Phase 1 — Scanning (no edits)**

1. Read full document
2. Find violations with Redundancy Detection Guide below
3. Create one task per redundancy found:
   - `"Remove redundancy – section:`<name>` (Type: `<lexical|structural|semantic>`): `<description>`"`
4. List all tasks for user confirmation before editing

**Phase 2 — Execution**

1. Apply matching fix strategy per task (see Fixing Strategies table)
2. Mark each task `completed` when finished

**Phase 3 — Verification**

After all tasks complete, compile documentation:
```
sbt "docs/mdoc --in <file.md> --out website/<file.md>"
```

Verify:
- No compilation errors
- Cross-references valid (no broken links)
- Sections flow naturally after cuts
- Concept clarity preserved

Report what you cut AND what you left, one line each with section name. Leaving something is a finding, not an omission: it shows a borderline case was considered and the bound held.

## Redundancy Detection Guide

| Type | How to Identify | Signal | Example |
|------|-----------------|--------|---------|
| **Lexical** | Word appears 2+ times in same/adjacent sentences; one suffices | Synonym nearby; removing word keeps meaning | "return back", "free gift", "unexpected surprise" |
| **Lexical** | Same phrase repeats in consecutive paragraphs | Copy-paste patterns; identical 3+ word phrases | Same code snippet introduced identically twice |
| **Structural** | Transitions not clarifying sequence or relationship | Removing "furthermore", "also", "in particular" leaves meaning clear | "Furthermore, also," (both signal addition); "In this regard," when context obvious |
| **Structural** | Signposting phrase restating what was just said | "as mentioned above", "as we discussed" | "We showed earlier that X works. As mentioned above, X is useful." |
| **Semantic** | Type defined or explained in 2+ places | Same definition or type signature in several sections | "`Chunk` is an immutable sequence" in Overview, Use Cases, and API section |
| **Semantic** | Example pattern repeats across sections | Same use case, similar code/narrative structure | Multiple "hello world" examples in consecutive sections |
| **Semantic** | Motivation explained more than once | Concept justified in intro, then again later | "We need deduplication for performance" in both Overview and Benefits |

## Fixing Strategies

| Redundancy | Strategy | Example |
|-----------|----------|---------|
| **Lexical: synonym nearby** | Remove redundant word; keep one | Change "return back" → "return" |
| **Lexical: phrase repeats** | Extract to section intro or one location; cross-reference it | Define once at top; link from repeats |
| **Structural: unnecessary transition** | Delete transition word; verify sentence still flows | Delete "Furthermore,"; sentence still reads naturally |
| **Structural: restated signposting** | Remove phrase; rely on document flow | Delete "As mentioned above," — reader infers from prior section |
| **Semantic: repeated definition** | Keep definition in primary location (earliest, or most prominent); replace repeats with `[See X](#link)` | First definition in Overview; later sections link to it |
| **Semantic: repeated example** | **Leave it — do not remove a code block, ever.** See "Never edit a code block" below. | Two similar examples stay two examples |
| **Semantic: repeated motivation** | Keep motivation once (usually intro); cut from later sections | Explain "why" once; don't repeat in each section |

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Removing transitions that clarify logic | Some transitions guide meaning ("first", "then", "because", "instead", "unless") | Only remove decorative transitions ("furthermore", "also") |
| Cutting without re-reading | Section left ungrammatical | Always read edited section aloud after cutting |
| Cutting a fact because it *looks* like repetition | Text carrying information found nowhere else on page (parameter, default, caveat, version) is not redundancy | Cut removes words, never facts |
| Deleting the last of anything | Last example, last definition, last mention of a member: section reduced to heading and link is worse than repetitive one | Keep at least one occurrence of every fact and every example, always |

## Never Edit a Code Block

Prose is this skill's only target. mdoc blocks share one scope down whole page. Removing a "duplicate" example can break every later block. Compiler then blames a line you never looked at, far from the deleted block. Being wrong costs a broken page. Cutting a look-alike example saves a few skippable lines. Never worth the trade:

- ✅ cut sentence introducing second of two similar examples ❌ cut example itself
- ✅ leave two look-alike code blocks ❌ merge them into one

Headings, frontmatter, and links are not this skill's to restructure either: do not merge sections, renumber headings, or retitle anything to reduce repetition.

## Detection Hints

- **Grep for repeated phrases**: Grep tool, count mode, on `<file.md>` — require three or more occurrences before it counts; two distant mentions is reader finding their place, not repetition
- **Read for transitions**: Scan for "also", "furthermore", "moreover", "in addition", "as mentioned", "as we discussed", "in this regard"
- **Scan for patterns**: Find identical code structures or narrative patterns in consecutive examples. Note them for the receipt, never for deletion

## Integration

After this skill, document is ready for:
- **Stylistic review**: Use `/docs-writing-style` to check prose rules
- **Compliance check**: Use `/docs-check-compliance` to audit against all rules
- **Integration**: Use `/docs-integrate` if adding document to site
