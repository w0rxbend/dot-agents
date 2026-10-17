# Historical boundaries and evidence map

## Two independent contracts in one representation change

PR 52 changed `Map[Method, DispatchTrie[Endpoint]]` into a path trie carrying method maps. In its dated head, `DefaultHandler` first resolves the path and then the effective method. The minimal-application fixture checks an unknown path as 404 and DELETE against the existing POST path as 405 (`cask-status-lookup`, `cask-status-test`). This is a default Cask routing contract, not a complete HTTP specification or an authentication policy.

The same revision combines independent route registrations with a premature `toMap` (`cask-routing-before`). PR 70 repairs the resulting validation mismatch. Its eligible patch and dated source retain a sequence, extract method groups for validation, and apply `map(_.toMap)` only after construction (`cask-routing-after`, `cask-validation-groups`). Its test suite distinguishes exact failure messages, legitimate cross-group registration, and same-group collisions (`cask-routing-test`). These algorithmic lessons are **inferences from source and tests**, not words attributed to a reviewer.

In PR 52, lihaoyi asks for an explanation of what changed and why it fixes the problem; megri supplies the commit explanation and acknowledges unrelated cleanup (`cask-description-review`, `cask-description-response`). That exchange supports a causal review explanation. It does not retroactively endorse the validation bug. PR 70's retrieved review, inline-comment, and issue-comment endpoints are complete and empty. Do not invent a substantive review from its merge.

## Test strength and blind spots

The trie tests' cross-group cases under `errors` call `construct` without asserting subsequent lookup. Their negative counterparts check messages, so they are valuable validation oracles but cannot establish reachability for every accepted combination. In particular, construction works with method groups while runtime lookup uses shared child structure and subpath state. Review changed overlap behavior independently; do not extrapolate the narrow GET/POST shared-subpath integration fixture to all mixed wildcard/literal routes.

The production preparation step groups equal paths before trie construction. A new regression for duplicate independent endpoint declarations should therefore pass through that preparation step as well as testing the trie helper. Merely supplying two manually constructed duplicate trie terminals can miss an upstream lossy conversion. This added review/testing requirement is an inference, not a claim that the historical test suite already covers it.

## Build and platform context

The chosen validation snapshot is `d5fa6d47da5ea99d94887fafd555696ba07aa205`, committed 2022-09-04T09:39:11Z. Its root `build.sc` declares `cask` and `example.minimalApplication`/`example.variableRoutes` as cross modules; the examples inherit `AppModule` test definitions from their own build files. Those examples use uTest 0.7.10 and requests 0.6.9, while core tests use uTest 0.8.0 and requests 0.7.1. Do not homogenize their dependency versions.

The wrapper and `.mill-version` select Mill 0.10.5 unless an environment override is supplied. The wrapper downloads a Mill executable on cache miss, making even discovery an execution-permission boundary. The historical test CI selects Temurin Java 8 and invokes `__.testLocal`. This is a declared matrix, not proof that every compiler/JDK combination ran successfully or that Java 8 is the minimum for present Cask.

The server is JVM/Undertow; Scala.js 1.10.1 is used by the Scala-2.13 utility target, not by server routing. Castor is already part of Cask's utility model. No Cats Effect, ZIO, FS2, Ox, or Native integration is established by this evidence.

For orientation, the earlier sampled 2020 build uses Scala 2.13.3/Dotty 0.27.0-RC1; the late-2024 build uses Scala 2.12.20/2.13.15/3.3.4 and `build.mill` with package discovery. These eras cannot share hardcoded build selectors. This skill deliberately validates one pinned post-repair source tree rather than offering a current-version setup tutorial.

## Decision boundaries

- `scala-library-contracts` covers general consumer/compiler and public-API compatibility. This skill adds the concrete loss-of-registration-information mechanism and the construction/lookup oracle split.
- `scala-collections` covers general collection choice. It does not replace tracing whether duplicate route declarations survive until validation.
- Direct-style Scala guidance must not retrofit modern Ox/Tapir or Scala-3-only syntax onto historical Cask.
- JSON replay and executor proposals are distinct findings in the larger research dossier, not extra skills in this package. In particular, unmerged PR 125 is not evidence of a released executor API.

See [evidence.json](evidence.json) for exact excerpts, actual dates, role uncertainty, source paths, and claim boundaries. None of these notes constitutes Scala compilation, benchmark execution, peer acceptance, or catalog publication.
