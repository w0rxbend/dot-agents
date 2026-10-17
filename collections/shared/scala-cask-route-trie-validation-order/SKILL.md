---
name: scala-cask-route-trie-validation-order
description: Use when refactoring Cask route-trie construction, method maps, duplicate-route validation, or default 404/405 dispatch. Preserve registration multiplicity until method-scoped validation and verify lookup behavior separately.
license: MIT
---

# Preserve Cask route validation through representation changes

Review the path from annotated endpoint metadata to a compiled dispatch trie, not just the final collection type. The historical change from method-first tries to one path-first trie fixed status selection but lost validation information. Keep both contracts intact.

## When to Use

Use for Cask `Main.prepareDispatchTrie`, `DispatchTrie.construct`/`validateGroup`/`map`, or `DefaultHandler` changes that combine routes, normalize method maps, change ambiguity checks, or alter missing-path/missing-method responses. Use during development, code review, and bounded refactoring; reproduce the affected registration or request before proposing a repair.

## When Not to Use

Do not use as a general HTTP conformance audit, a routing algorithm for another framework, or an application-wide effect migration. JSON body caching, executor ownership, compiler upgrades, URI normalization, and authentication concealment need their own evidence. Merely declaring GET and POST at the same path is not a defect. Do not infer an internal validation bug from two endpoint annotations on a single function: that is a separate macro-validation boundary.

## Prerequisites

Read the target checkout's instructions, build, launcher, endpoint metadata, and tests. Record the exact Cask commit/version, Scala cross versions, JDK, Undertow version, and Mill version. Do not assume the present checkout still has these APIs.

Historical anchors are PR 52's `d7f7d55a5b468f02c02298fe05b4401b4580153e` (2021) and PR 70's `e01c972ca3492c05f2329202bed7cc4ffeb42ad3` (2022). Validation commands below target the later inspected snapshot `d5fa6d47da5ea99d94887fafd555696ba07aa205`: Scala 2.12.16/2.13.8/3.1.3, Mill 0.10.5, Undertow 2.2.18.Final, with Temurin Java 8 declared by CI. These are historical coordinates, not upgrade recommendations or proof of successful CI execution. Core tests use uTest 0.8.0; the selected example builds use uTest 0.7.10.

Preserve synchronous Cask `Result`/`Response` and Undertow dispatch. Castor 0.2.1 is a utility dependency, not a reason to introduce Cats Effect, ZIO, FS2, or Ox. The Scala.js utility target does not make this JVM server algorithm a JS server contract. See [historical boundaries](references/history.md).

## Workflow

1. **Trace registration through lookup.** Follow `Routes` metadata, endpoint methods/path/subpath, `Util.splitPath`, `Main.prepareDispatchTrie`, trie construction, then `DefaultHandler.handleRequest`. Identify where path grouping changes the representation and where information is discarded.
2. **Write the invariant before editing.** Two independently registered endpoints with the same normalized path and method must remain visible to ambiguity checking. Distinct HTTP methods are distinct validation groups. A map keyed only by method cannot retain two such registrations.
3. **Find the first lossy operation.** In PR 52, `values.map(_._2).flatten.toMap` discarded collisions across registrations before the trie could reject them. Retain a sequence of method/endpoint pairs across that boundary; pass method keys to group validation; map validated trie payloads to method maps afterward. Do not replace last-wins with first-wins or `distinct`: either conceals the conflicting registration.
4. **Keep validation method-scoped.** Apply terminal, wildcard, and subpath ambiguity checks to entries in each method group, not to the union of all methods. Recurse with the same grouping function. Preserve method/path context in diagnostics. Do not widen the registration policy incidentally while reorganizing helpers.
5. **Preserve path-first status selection.** Resolve the request path first. No path match uses `handleNotFound`; a matched path without the effective method uses `handleMethodNotAllowed`. Keep successful endpoint selection, wildcard bindings, and remaining path segments unchanged. Inspect existing WebSocket method handling if that branch is touched; this skill does not establish its protocol correctness.
6. **Test construction and dispatch separately.** Add registration-level cases through `Main.prepareDispatchTrie`, not only hand-built tries. Then exercise the HTTP fixtures. For changed wildcard or subpath combinations, explicitly assert which endpoint, bindings, and remaining segments are returned; construction success alone is not a lookup oracle.
7. **Explain the causal change.** Show what information the old representation lost, where the new representation retains it, and which assertion distinguishes them. PR 52 contains lihaoyi's request for an explanation of the change and fix, followed by megri's response. It is not evidence that a reviewer endorsed every detail of the algorithm.

## Review and Refactoring Checks

- Preserve the **multiplicity invariant** across independent registrations until method-scoped validation finishes; then preserve the public method-map payload expected by dispatch.
- Preserve 404 for a missing path and 405 for an unsupported method on an existing path under Cask's default policy. A deliberately concealed protected resource is a false-positive risk: establish its policy before changing a response.
- Preserve diagnostic meaning. Require the intended duplicate/wildcard/subpath reason with offending method/path information, not merely `intercept[Exception]`. Historical tests assert exact strings; use that checkout's stable diagnostic contract rather than hardcoding another revision's wording.
- Avoid false positives on every `.toMap`: the defect concerns collapsing independent route registrations before validation. A per-endpoint set of method labels and a conversion after successful validation are different boundaries. Investigate multiplicity requirements instead of banning maps.
- Do not promise that method-scoped acceptance makes every mixed-method wildcard/literal/subpath lookup correct. The historical trie has shared children and a shared subpath flag; its permissive construction tests are not exhaustive dispatch tests. Keep unresolved combinations visible rather than changing the algorithm without a reproduction.

## Validation

This research did **not** execute upstream Scala or Mill. In a separately authorized checkout, review the launcher before running even `resolve`: it can download executable Mill, and loading the build executes code. Obtain approval for dependencies, writable caches, JDK setup, and local sockets. Do not run release, upload, or publishing targets.

At the pinned 2022 snapshot, discover these source-derived selectors first:

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

Run the relevant compiler cross variants after confirming their selectors. The example fixtures both bind `localhost:8081` and stop Undertow in `finally`; serialize them or deliberately isolate their ports. CI declared `./mill -i --disable-ticker __.testLocal`, but that broad command is not a substitute for checking each changed oracle. On another checkout rediscover names and versions rather than transplanting these commands or inventing sbt targets.

Required oracles: same-method duplicate registration rejected with the correct reason; same path with GET/POST accepted and both handlers reachable; unknown path 404; unsupported method at a known path 405; existing successful response unchanged. For affected route shapes also assert bindings and remaining segments. Report unexecuted tests explicitly.

## Examples

### Good

At the 2022 snapshot, `prepareDispatchTrie` keeps the combined method entries as a sequence and uses `DispatchTrie.construct(0, dispatchInputs)(_.map(_._1)).map(_.toMap)`. A refactor preserving that ordering can still use maps for dispatch. Pair a duplicate-GET registration test with GET/POST reachability tests. The historical `variableRoutes` fixture checks GET and POST on `/path/one/two/three`, including their different response text; it does not validate every possible overlap.

### Broken and Correction

Two independently declared GET handlers use `/hello/world`. A cleanup adds `.toMap` immediately after flattening their method entries. Only one handler reaches validation, so a startup that should reject ambiguous registration can succeed. Correction: remove that early conversion, validate the retained entries per method, and convert trie payloads only afterward. Assert the intended duplicate diagnostic and add the legitimate GET/POST counterpart. Also retain the missing-path HTTP assertion: returning to method-first dispatch just to fix duplicate detection can reintroduce the earlier 404/405 problem.

### Negative

A registration contains GET `/hello/world` and POST `/hello/world`, with both handlers reachable and no duplicate within either method. Reject a review finding that compares path strings alone. Likewise, a one-pass `postJson` body parser is outside this skill even if its handler lives on a route under review. Do not prescribe caching, an effect runtime, or global routing changes for it.

## Output Contract

For each finding provide **file:line**, **severity**, the lost or preserved invariant, exact registration/request inputs, **evidence** IDs or pinned source links, and the regression **test** that distinguishes broken from corrected behavior. Explain the smallest correction and one legitimate counterexample. Separate source observation, historical discussion, current-version inference, and actual execution. If no defect is established, state which path was traced and which lookup shapes remain untested; do not manufacture a finding from history alone.

## Limitations

These are source-derived lessons from a representation change and its later repair, not a universal maintainer style preference. PR 70 has no retrieved discussion; its merge is not a design review. Neither historical assertions nor structural skill validation prove runtime behavior, full HTTP compliance, complexity bounds, cancellation safety, or current-version compatibility. Keep the existing effect model and avoid unrelated syntax or build migrations. Independent peer evaluation and any upstream execution remain separate gates.

## Sources

Use the exact records and claims in [evidence.json](references/evidence.json), with [history and validation boundaries](references/history.md). Central sources are [PR 52's explanation request](https://github.com/com-lihaoyi/cask/pull/52#issuecomment-968502972), [pre-validation map conversion](https://github.com/com-lihaoyi/cask/blob/d7f7d55a5b468f02c02298fe05b4401b4580153e/cask/src/cask/main/Main.scala#L158), [method-scoped validation](https://github.com/com-lihaoyi/cask/blob/e01c972ca3492c05f2329202bed7cc4ffeb42ad3/cask/src/cask/internal/DispatchTrie.scala#L21-L38), [conversion after validation](https://github.com/com-lihaoyi/cask/blob/d5fa6d47da5ea99d94887fafd555696ba07aa205/cask/src/cask/main/Main.scala#L156-L162), and [diagnostic regression tests](https://github.com/com-lihaoyi/cask/blob/d5fa6d47da5ea99d94887fafd555696ba07aa205/cask/test/src/test/cask/DispatchTrieTests.scala#L149-L168).
