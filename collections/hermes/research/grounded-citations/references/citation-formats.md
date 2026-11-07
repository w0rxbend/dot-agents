# Citation formats per output target

Ledger is format-agnostic: `sources.py render --style ...` emits block; this
file covers placement and inline marker.

## Markdown / chat answers

Inline `[n]` right after sentence. Block at end:

```
## Sources

[1] https://example.com/a — Page title
[2] https://example.com/b
```

`--style plain` gives bare `Sources:` header for chat replies, where markdown
heading is noise.

## PDF via LaTeX (`latex-pdf-report` skill)

`--style footnotes`: map each id to `\footnote{}` at first use, or keep numeric
markers and emit endnotes section. Bibliography-shaped report: `--style bibtex`
writes `@misc` entries keyed `source<N>`; cite with `\cite{source3}`, BibTeX
renders list.

Do not mix: either numeric `[n]` + Sources section, or `\cite{}` + BibTeX.

## Word (.docx, `docx` skill)

Prose documents for human editing: real footnotes over inline brackets;
reviewers expect Word footnotes. Keep ledger ids as footnote numbers so
`verify` still works on markdown source-of-truth; generate .docx from that
markdown.

## Slides (.pptx, `powerpoint` skill)

Inline `[n]` in bullet; one "Sources" slide at end via `--style plain`. Never
put URL in body bullet: wrecks layout, can't be clicked in projected deck.

## Spreadsheets (.xlsx)

Add `source` column holding id, plus `Sources` sheet from
`render --style plain`. Do not paste URLs into data cells.

## Wiki / multi-page output (`llm-wiki`, Obsidian)

Per-page Sources block; ids shared across pages from one ledger. Ids are
ledger identities, so `[7]` means same page across whole wiki. Do not reset
ledger between pages of one build.

## Research papers

Hand off to `grounded-citations` skill. Export `--style bibtex` into
`references.bib`, then follow that skill's citation verification (greps
`\cite{...}` against the .bib). Ledger's job ends at verified URL entries;
venue formatting belongs to that skill.

## Code and config artifacts

No citations inside generated code. Provenance that matters goes in commit
message, PR body or doc header, not in comments scattered through source.
