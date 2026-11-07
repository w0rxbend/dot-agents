---
name: docs-ascii-diagram
description: How to produce an ASCII diagram that is actually aligned — generate it from a Python script with a width assertion, never by hand. Use when a page needs a box-and-arrow diagram, such as a module reference's "How They Work Together" section or a tutorial's data-flow picture.
allowed-tools: Read, Write
---

# ASCII Diagrams

## Method — do not hand-draw

Hand-drawn ASCII art is off by one or two columns almost every time, and neither you nor a reviewer
spots it by reading. Alignment is arithmetic; let arithmetic do it:

1. Write small Python script that builds diagram from data: fixed inner width `W`, helpers padding
   every line to it.
2. End script asserting every box line is exactly `W + 2` characters. Print
   `WIDTH CHECK: all aligned` or offending `(index, length)` pairs.
3. Run it. On failure, fix the **script** and rerun.
4. Paste only verified output into page.

**Never repair a diagram by editing the rendered text.** Fixing one spot shifts a line you are not
watching.

`W = 64` is good default: fits two annotated columns. Raise only when page renders in wide
container. Keep total under **76 columns** to survive narrow panes and diffs.

## Character rules

- Box drawing: `┌ ┐ └ ┘ ─ │ ├ ┤ ┬ ┴ ┼`. Arrows: `▼ ▲ ◀ ▶`, or `->` and `<-`.
- Every character must be single-width. Ambiguous-width characters shift columns in some
  terminals, invisible where authored and broken where read:
  ✅ `1.` `2.` `3.` ❌ `①②③`, emoji, CJK
- Hold one style throughout: ✅ `─` everywhere ❌ `─` in one box and `-` in the next, `▼` beside `v`

## Content rules

- Diagram uses prose's structure and words: if text says "four
  phases", diagram labels four phases with those names.
- Label edges, not just nodes: what flows, which direction. Arrow pointing against flow is worse
  than no arrow.
- Annotate consequences, not mechanism:
  ✅ `nothing has run yet` ❌ `(lazy description)` · ✅ `wait right here` ❌ `(park thread)`
- Put the one fact readers most often get wrong on diagram's spine, where it cannot be skipped.
- Every element earns its place. Cut anything repeating prose without adding shape.

## Output

Put diagram in plain fence with **no language tag**, so no tooling tries to compile it:

````
```
┌──────────────┐
│   Ledger     │
└──────┬───────┘
       │ record(name, by)
       ▼
````

Keep script out of page: it is scaffolding, not reader content. Report its `WIDTH CHECK` line in
your result to show diagram was verified, not eyeballed.

## Worked shape

```python
W = 64  # inner width; every box line ends up W + 2 with the borders


def box(label, note=""):
    body = f" {label}".ljust(W) if not note else f" {label}".ljust(W - len(note) - 1) + note + " "
    return [f"┌{'─' * W}┐", f"│{body}│", f"└{'─' * W}┘"]


lines = box("Ledger", "counts only grow") + ["    │ record(name, by)", "    ▼"] + box("Window")

bad = [(i, len(l)) for i, l in enumerate(lines) if l.startswith(("┌", "│", "└")) and len(l) != W + 2]
print("WIDTH CHECK: all aligned" if not bad else f"WIDTH CHECK FAILED: {bad}")
print("\n".join(lines))
```

Tune per diagram: `W`, and whether 76-column cap applies to target.
