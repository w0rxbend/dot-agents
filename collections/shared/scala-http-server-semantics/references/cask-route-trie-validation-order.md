# Preserve Cask route validation through representation changes

> Library: Cask (route trie, `DefaultHandler`). Formerly `scala-cask-route-trie-validation-order` skill, merged into `scala-http-server-semantics`. Evidence: [evidence/scala-cask-route-trie-validation-order.json](evidence/scala-cask-route-trie-validation-order.json).

Review path from endpoint annotations to compiled dispatch trie, not just final collection type. Method-first to path-first trie switch fixed status selection but lost validation information. Keep both contracts.

## When to Use

Cask `Main.prepareDispatchTrie`, `DispatchTrie.construct`/`validateGroup`/`map` or `DefaultHandler` changes that combine routes, normalize method maps, change ambiguity checks or alter missing-path/missing-method responses. Development, review, bounded refactoring. Reproduce affected registration or request before proposing repair.

## When Not to Use

Not for general HTTP conformance audit, other-framework routing or app-wide effect migration. JSON body caching, executor ownership, compiler upgrades, URI normalization and authentication concealment need own evidence. GET plus POST on one path alone is no defect. Two endpoint annotations on one function: separate macro-validation boundary; do not infer internal validation bug.

## Prerequisites

Read target checkout's instructions, build, launcher, endpoint metadata, tests. Record exact Cask commit/version, Scala cross versions, JDK, Undertow and Mill versions. Do not assume present checkout still has these APIs.

Anchors: PR 52 `d7f7d55a5b468f02c02298fe05b4401b4580153e` (2021), PR 70 `e01c972ca3492c05f2329202bed7cc4ffeb42ad3` (2022). Commands below target later snapshot `d5fa6d47da5ea99d94887fafd555696ba07aa205`: Scala 2.12.16/2.13.8/3.1.3, Mill 0.10.5, Undertow 2.2.18.Final, CI-declared Temurin Java 8. Historical coordinates, not upgrade advice or proof CI passed.

Keep synchronous Cask `Result`/`Response` and Undertow dispatch. Castor 0.2.1 is utility dependency, no reason to add Cats Effect, ZIO, FS2 or Ox. Scala.js utility target does not make this JVM server algorithm a JS server contract. See [historical boundaries](#historical-boundaries-and-evidence-map).

## Workflow

1. **Trace registration through lookup.** `Routes` metadata, endpoint methods/path/subpath, `Util.splitPath`, `Main.prepareDispatchTrie`, trie construction, then `DefaultHandler.handleRequest`. Note where path grouping changes representation and drops information.
2. **Write the invariant before editing.** Two independent registrations with same normalized path and method must stay visible to ambiguity checking. Each HTTP method is own validation group. Map keyed only by method cannot hold both.
3. **Find the first lossy operation.** PR 52's `values.map(_._2).flatten.toMap` dropped cross-registration collisions before trie could reject them. Keep method/endpoint pair sequence across that boundary, pass method keys to group validation, map validated payloads to method maps after. Do not swap last-wins for first-wins or `distinct`: both hide conflicting registration.
4. **Keep validation method-scoped.** Terminal, wildcard and subpath ambiguity checks run per method group, not on union of methods. Recurse with same grouping function. Keep method/path context in diagnostics. Do not widen registration policy while reorganizing helpers.
5. **Preserve path-first status selection.** Resolve path first. No path match: `handleNotFound`. Path matched, effective method missing: `handleMethodNotAllowed`. Keep successful endpoint selection, wildcard bindings, remaining segments unchanged. If WebSocket method branch is touched, inspect it; this case does not establish its protocol correctness.
6. **Test construction and dispatch separately.** Registration-level cases through `Main.prepareDispatchTrie`, not only hand-built tries. Then HTTP fixtures. Changed wildcard/subpath combinations: assert returned endpoint, bindings, remaining segments. Construction success alone is no lookup oracle.
7. **Explain the causal change.** What old representation lost, where new one keeps it, which assertion tells them apart.

## Review and Refactoring Checks

- Keep **multiplicity invariant** across independent registrations until method-scoped validation finishes; then keep public method-map payload dispatch expects.
- Keep 404 for missing path, 405 for unsupported method on existing path (Cask default policy). Deliberately concealed protected resource is false-positive risk: establish its policy before changing response.
- Keep diagnostic meaning: intended duplicate/wildcard/subpath reason with offending method/path, not merely `intercept[Exception]`. Historical tests assert exact strings; use that checkout's stable diagnostic contract, not another revision's wording.
- Not every `.toMap` is a defect. Defect: collapsing independent registrations before validation. Per-endpoint method-label set and post-validation conversion are different boundaries. Investigate multiplicity needs; do not ban maps.
- Do not promise method-scoped acceptance makes every mixed-method wildcard/literal/subpath lookup correct. Historical trie shares children and subpath flag; permissive construction tests are not exhaustive dispatch tests. Keep unresolved combinations visible; no algorithm change without reproduction.

## Validation

Research did **not** execute upstream Scala or Mill. In separately authorized checkout, review launcher before even `resolve`: it can download executable Mill; loading build runs code. Get approval for dependencies, writable caches, JDK setup, local sockets. Do not run release, upload or publishing targets.

At pinned 2022 snapshot, discover these source-derived selectors first:

```sh
./mill resolve 'cask[2.13.8].test'
./mill resolve 'example.minimalApplication[2.13.8].test'
./mill resolve 'example.variableRoutes[2.13.8].test'
```

Only after discovery and execution permission, run each separately:

```sh
./mill 'cask[2.13.8].test'
./mill 'example.minimalApplication[2.13.8].test'
./mill 'example.variableRoutes[2.13.8].test'
```

Run relevant compiler cross variants once selectors confirmed. Both example fixtures bind `localhost:8081` and stop Undertow in `finally`: serialize them or isolate ports. CI declared `./mill -i --disable-ticker __.testLocal`; broad command does not replace checking each changed oracle. Other checkout: rediscover names and versions; do not transplant these commands or invent sbt targets.

Required oracles: same-method duplicate rejected with correct reason; same-path GET/POST accepted, both handlers reachable; unknown path 404; unsupported method on known path 405; existing successful response unchanged. Affected route shapes: also assert bindings and remaining segments. Report unexecuted tests explicitly.

## Examples

### Good

At 2022 snapshot, `prepareDispatchTrie` keeps combined method entries as sequence and uses `DispatchTrie.construct(0, dispatchInputs)(_.map(_._1)).map(_.toMap)`. Refactor keeping that order can still use maps for dispatch. Pair duplicate-GET registration test with GET/POST reachability tests. Historical `variableRoutes` fixture checks GET and POST on `/path/one/two/three` with different response text; does not validate every overlap.

### Broken and Correction

Two independent GET handlers on `/hello/world`. Cleanup adds `.toMap` right after flattening method entries. Only one reaches validation, so startup that should reject ambiguous registration can succeed. Correction: remove early conversion, validate retained entries per method, convert trie payloads only after. Assert intended duplicate diagnostic; add legitimate GET/POST counterpart. Keep missing-path HTTP assertion: reverting to method-first dispatch only to fix duplicate detection can bring back earlier 404/405 problem.

### Negative

GET `/hello/world` plus POST `/hello/world`, both reachable, no duplicate within either method. Reject review finding comparing path strings alone. One-pass `postJson` body parser is outside this case, even if its handler is on a reviewed route. Do not prescribe caching, effect runtime or global routing changes for it.

## Output Contract

Per finding: **file:line**, **severity**, lost or preserved invariant, exact registration/request inputs, **evidence** IDs or pinned source links, regression **test** separating broken from corrected behavior. Explain smallest correction plus one legitimate counterexample. Separate source observation, historical discussion, current-version inference, actual execution. If no defect is established, state traced path and untested lookup shapes. Do not manufacture finding from history alone.

## Limitations

Source-derived lessons from one representation change and its repair, not universal maintainer style. Neither historical assertions nor structural validation prove runtime behavior, full HTTP compliance, complexity bounds, cancellation safety or current-version compatibility. Keep existing effect model; avoid unrelated syntax or build migrations. Independent peer evaluation and any upstream execution stay separate gates.

## Historical boundaries and evidence map

### Two independent contracts in one representation change

PR 52 turned `Map[Method, DispatchTrie[Endpoint]]` into path trie carrying method maps. At its dated head, `DefaultHandler` resolves path, then effective method. Minimal-application fixture checks unknown path as 404, DELETE on existing POST path as 405 (`cask-status-lookup`, `cask-status-test`). Default Cask routing contract, not full HTTP spec or authentication policy.

Same revision merges independent registrations with premature `toMap` (`cask-routing-before`). PR 70 repairs resulting validation mismatch: eligible patch and dated source keep sequence, extract method groups for validation, apply `map(_.toMap)` only after construction (`cask-routing-after`, `cask-validation-groups`). Tests separate exact failure messages, legitimate cross-group registration, same-group collisions (`cask-routing-test`). Algorithmic lessons are **inferences from source and tests**, not reviewer words.

In PR 52, lihaoyi asks what changed and why it fixes the problem; megri gives commit explanation, admits unrelated cleanup (`cask-description-review`, `cask-description-response`). Supports causal review explanation; does not retroactively endorse validation bug. PR 70's retrieved review, inline-comment and issue-comment endpoints are complete and empty. Do not invent substantive review from its merge.

### Test strength and blind spots

Trie tests' cross-group cases under `errors` call `construct` without asserting later lookup. Negative counterparts check messages: good validation oracles, but cannot prove reachability for every accepted combination. Construction uses method groups; runtime lookup uses shared child structure and subpath state. Review changed overlap behavior independently. Do not extrapolate narrow GET/POST shared-subpath integration fixture to all mixed wildcard/literal routes.

Production preparation groups equal paths before trie construction. New duplicate-declaration regression should therefore pass through that step, plus trie helper test. Two hand-built duplicate trie terminals alone can miss upstream lossy conversion. Added requirement is inference, not claim historical suite covers it.

### Build and platform context

Validation snapshot `d5fa6d47da5ea99d94887fafd555696ba07aa205`, committed 2022-09-04T09:39:11Z. Root `build.sc` declares `cask` and `example.minimalApplication`/`example.variableRoutes` as cross modules; examples inherit `AppModule` test definitions from own build files. Examples use uTest 0.7.10 and requests 0.6.9, core tests uTest 0.8.0 and requests 0.7.1; do not homogenize these versions.

Wrapper and `.mill-version` select Mill 0.10.5 unless environment override given. Wrapper downloads Mill executable on cache miss, so even discovery needs execution permission. Historical test CI selects Temurin Java 8, runs `__.testLocal`. Declared matrix, not proof every compiler/JDK combination passed or that Java 8 is minimum for present Cask.

Server is JVM/Undertow; Scala.js 1.10.1 serves Scala-2.13 utility target, not server routing. Castor already belongs to Cask's utility model. Evidence establishes no Cats Effect, ZIO, FS2, Ox or Native integration.

Orientation: sampled 2020 build uses Scala 2.13.3/Dotty 0.27.0-RC1; late-2024 build uses Scala 2.12.20/2.13.15/3.3.4 and `build.mill` with package discovery. Eras cannot share hardcoded build selectors. Case validates one pinned post-repair tree, not current-version setup tutorial.

### Decision boundaries

- `scala-library-contracts` skill covers general consumer/compiler and public-API compatibility. This case adds concrete loss-of-registration-information mechanism and construction/lookup oracle split.
- `scala-collections` skill covers general collection choice; no substitute for tracing whether duplicate route declarations survive until validation.
- Direct-style Scala guidance must not retrofit modern Ox/Tapir or Scala-3-only syntax onto historical Cask.
- JSON replay and executor proposals: separate findings in larger research dossier, not cases here. Unmerged PR 125 is no evidence of released executor API.

See [evidence/scala-cask-route-trie-validation-order.json](evidence/scala-cask-route-trie-validation-order.json) for exact excerpts, dates, role uncertainty, source paths, claim boundaries. None of these notes is Scala compilation, benchmark execution, peer acceptance or catalog publication.

## Sources

Central sources: [PR 52's explanation request](https://github.com/com-lihaoyi/cask/pull/52#issuecomment-968502972), [pre-validation map conversion](https://github.com/com-lihaoyi/cask/blob/d7f7d55a5b468f02c02298fe05b4401b4580153e/cask/src/cask/main/Main.scala#L158), [method-scoped validation](https://github.com/com-lihaoyi/cask/blob/e01c972ca3492c05f2329202bed7cc4ffeb42ad3/cask/src/cask/internal/DispatchTrie.scala#L21-L38), [conversion after validation](https://github.com/com-lihaoyi/cask/blob/d5fa6d47da5ea99d94887fafd555696ba07aa205/cask/src/cask/main/Main.scala#L156-L162), and [diagnostic regression tests](https://github.com/com-lihaoyi/cask/blob/d5fa6d47da5ea99d94887fafd555696ba07aa205/cask/test/src/test/cask/DispatchTrieTests.scala#L149-L168).
