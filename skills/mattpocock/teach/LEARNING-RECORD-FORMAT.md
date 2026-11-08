# Learning Record Format

Learning records live in `./learning-records/`, numbered sequentially: `0001-slug.md`, `0002-slug.md`, etc. Create the directory lazily: only when writing the first record.

Teaching equivalent of ADRs: they capture non-obvious lessons, key insights, and stated prior knowledge that steer future sessions. Used to calculate zone of proximal development.

## Template

```md
# {Short title of what was learned or established}

{1-3 sentences: what was learned (or what prior knowledge was established), and why it matters for future sessions.}
```

That is the whole format. One paragraph can suffice. Value lies in recording _that_ this is now known and _why_ it changes what to teach next, not in filling out sections.

## Optional sections

Include only when they add genuine value. Most records won't need them.

- **Status** frontmatter (`active | superseded by LR-NNNN`): when an earlier understanding proves wrong and gets replaced.
- **Evidence**: how user demonstrated understanding (question answered, exercise completed, prior experience cited). Use when the claim might be revisited.
- **Implications**: what this unlocks or rules out for future sessions. Record when non-obvious.

## Numbering

Scan `./learning-records/` for highest existing number, increment by one.

## When to write a learning record

Write one when any of these is true:

1. **The user demonstrated genuine understanding of something non-trivial**: not just exposure, but evidence they can use the concept correctly. Sets new floor for what to teach next.
2. **The user disclosed prior knowledge**: "I already know X." Record it so future sessions don't re-teach it. Also record _depth_ claimed.
3. **A misconception was corrected**: user believed something wrong, now sees why. High-value: predicts future stumbling blocks on related topics.
4. **The mission shifted in response to learning**: user discovered they care about something different than they thought. Cross-link to [[MISSION.md]] and update it.

### What does _not_ qualify

- Material merely covered. Coverage is not learning. Wait for evidence.
- Anything already captured tersely in [[GLOSSARY.md]] as a term definition. Don't duplicate.
- Session-by-session activity logs. Learning records are not a journal: they are decision-grade insights.

## Supersession

When a later record contradicts an earlier one (understanding deepened or was corrected), mark the old record `Status: superseded by LR-NNNN` rather than deleting it.
