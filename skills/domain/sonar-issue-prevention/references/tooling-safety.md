# CI and build-tool boundaries

## Shell input: GitHub Actions S7630

Put user-controlled workflow strings in `env`; expand as quoted arguments. GitHub expression substitution runs before shell parsing, so shell quotes around `${{ inputs.version }}` do not make it safe. Validate expected shape. Keep existing tag/environment/permission gates. Avoid `eval`, `sh -c` reconstruction, or passing data back into another interpreter.

```yaml
env:
  RELEASE_VERSION: ${{ inputs.version }}
run: |
  [[ "$RELEASE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
  gh release create "v$RELEASE_VERSION" --verify-tag --generate-notes
```

Pattern for already authorized release workflow, not permission to run a release. Use explicit repository context when job has no checkout. Test shell construction with inert metacharacter inputs, without invoking a real publication command. [GitHub explanation](https://docs.github.com/en/actions/concepts/security/script-injections).

## Write destinations: S8707

Define path contract before implementation. Internal generator confined to build directory: resolve root and candidate, verify ancestry before `mkdir` or writes, reject symlinked final file escaping root. Check both complete final destination and directory. No string-prefix checks (`out-elsewhere` is not inside `out`). Do not normalize only after creating directories.

Test in temporary directories: valid children, sibling-prefix paths, parent traversal, absolute paths outside allowed root, existing escaping symlinks. Leave outside sentinel files untouched. Resolver ancestry check is not sufficient against actively hostile concurrent filesystem. Use OS isolation or descriptor-based operations if that threat applies. Do not silently remove legitimate user-selected output capabilities from general-purpose CLI.

## Temporary state: S5443

Shared host: use secure temporary-directory APIs and task-owned cleanup, not predictable writable filenames. Disposable container: use private owned directory for configuration/logs; inspect actual mounts and port bindings. External services may require fixed rendezvous paths. Document and verify their isolation instead of hiding path from scanner. Do not launch live service only to test static cleanup.

## Regex correctness and cost: S5843, S6353, S8786

Simplify regex alternatives; keep capture-group meaning, escaping, accepted syntax. When pattern is effectively a parser, named patterns or small tokenizer can be clearer. Do not concatenate fragments solely to disguise measured complexity.

Python `\w`/`\d` are Unicode-aware by default. Replacing ASCII ranges: keep ASCII intent with scoped flags or explicit ranges. Global `re.ASCII` also narrows existing `\s` whitespace and word-boundary behavior. Scope that flag to identifier when surrounding Unicode behavior must stay unchanged. Test accepted ASCII, rejected non-ASCII identifiers, previously accepted Unicode whitespace. Unanchored searches: consider retries from every start position, plus backtracking within one match. Use bounded grammar, fitting anchoring/tokenization, or other demonstrated linear approach. Possessive quantifiers alone do not prevent all unanchored repeated-start costs. If narrow structured log grammar still triggers analyzer after proven boundary guard, prefer small delimiter-based parser with disjoint scans over another regex workaround; preserve prefixes, Unicode digit semantics, multiple candidates, malformed-input behavior.

Test success, malformed suffixes, absent matches, long near misses, with bounded input sizes. Avoid timing-only flaky tests; assert behavior, measure scaling separately when useful. Check supported Python version before picking regex features. [Python regex reference](https://docs.python.org/3/library/re.html), [temporary-file reference](https://docs.python.org/3/library/tempfile.html).
