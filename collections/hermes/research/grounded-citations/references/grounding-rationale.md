# Why numbered ledger ids (grounding research basis)

Design notes for anyone changing citation instructions or ledger mechanics.
SKILL.md wording is not arbitrary.

## The structural trick

Hallucinated citations come from model reconstructing URL from memory. If
model only emits small integer handed over at retrieval, nothing is left to
reconstruct. Wrong id is detectable (not in ledger); wrong URL is impossible
(model never types one, `render` does). Perplexity's product relies on this
property; hence ledger, not prose, owns URL.

Consequence: **register at retrieval, render mechanically.** Any workflow
letting model type URL into Sources block loses the guarantee.

## Cite while writing, not after

ALCE (arXiv:2305.14627) evaluates attribution for LLM answers: citing during
composition, from numbered retrieved snippets, gives materially better
attribution than post-hoc insertion. Post-hoc attribution invites model to
find a source plausibly matching an already-written sentence. That is exactly
how citations end up supporting what the page doesn't say.

Hence: cite per supported sentence, in-line, while writing. Never a citation
dump at end of paragraph or document.

## Verbatim quotes ground claims

WebGPT (arXiv:2112.09332) collects verbatim quotes at browse time and composes
answers from them. Rule here: figures, dates, names, quantities come from
source's own words, not paraphrase of a summary of a summary. Each
summarization hop lets a number drift.

## Formatting conventions

From Perplexity's leaked system prompts (jujumilk3/leaked-system-prompts).
Worth copying: users are trained to read these conventions.

- Marker directly after terminal punctuation, no space: `water.[1]`
- Each id in own brackets: `[1][2]`, not `[1, 2]`
- At most 3 ids per sentence; beyond that, citation stops identifying which
  source carries the claim
- Never cite a source not actually consulted
- Query classes that shouldn't be cited (translation, creative writing, casual
  chat) are exempted by instruction, not by separate classifier

Perplexity forbids raw URLs in answers because its UI renders source cards.
Hermes has no such UI layer in chat or written files, so this skill renders
id → URL list explicitly.

## Related in-tree implementation

`tools/web_tools.py` grew an in-process version of this idea in PR #44833:
`url -> [n]` registry plus citation guidance attached to tool results. Once
landed, that path grounds ad-hoc web answers automatically. This skill is the
portable half: works with any retrieval source (browser, curl, CLIs, local
PDFs) and persists ledger to disk, so multi-turn, multi-file and
multi-subagent work keeps stable ids. Both can coexist; ledger is source of
truth for anything written to a file.
