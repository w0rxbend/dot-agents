# Artifact trust and filesystem ownership

## Verify before execution or installation

Keep artifact selection, version resolution, verification, extraction, placement and state commit as identifiable stages. Lockfile pins resolved inputs. Checksum must match intended artifact from same release/version. Digest from same compromised location is integrity evidence, not automatically independent authenticity. Preserve signature policy where implemented. Never call unsigned artifacts signed or make optional signature validation a silently required new dependency. See [binary lock, verification, installer knobs, and signature scope](https://github.com/worxbend/binstaller/blob/5dec30c5d4d25b3d41fc4774bddf3256712cec56/README.md).

Reviewed Go Nerd Fonts implementation permits warning-only fallback when checksum manifest fetch fails. Treat that as existing best-effort behavior, not strict verification guarantee. Retain or strengthen it only within requested change; make docs/tests agree. See [checksum-fetch policy](https://github.com/worxbend/nerd-fonts-installer/blob/bb8c29811dca2d7e945bfc84c177683717eb3956/internal/fonts/installer.go).

Reject checksum mismatch before replacing existing executable. Stage in isolated directory on intended filesystem, validate staged files, commit only known outputs. If final operation fails, keep old installation or tool's documented rollback behavior. Do not call multi-file transaction atomic if only individual renames are.

## Extraction is a bounded parser

Follow each format's supported entry policy. Validate normalized member paths and link targets against extraction root. Per current extractor contract, reject absolute paths, parent traversal, unsafe symlink/hardlink chains, duplicate/conflicting entries and unsupported special files. Lexical path prefix is not enough when existing ancestor is symlink. Do not keep archive modes that make installed files unexpectedly writable or privileged.

Where implementation uses them, keep independent limits on compressed download bytes, inflated bytes, extracted bytes, member count, individual files and elapsed work. Truncated headers or short reads are errors, not clean archive end. Check progress inside decompression/copy loops, not only before opening file. See [archive path, size, link, and deadline enforcement](https://github.com/worxbend/binstaller/blob/5dec30c5d4d25b3d41fc4774bddf3256712cec56/core/src/binstaller/core/ArchiveExtractor.scala) and [font extraction boundary](https://github.com/worxbend/nerd-fonts-installer-scala/blob/c77ccca5c5ab0cb63630b6b83d6a13f69d25438e/core/src/io/worxbend/nerdfonts/install/ArchiveExtractor.scala).

## Dotfiles and privilege

Distinguish managed symlink from regular user file, directory and broken symlink. Clean up only entries covered by selected directive's documented ownership rules. Preserve conflict/relink/force semantics; do not make force default. Test traversal, parent symlinks, existing targets and reruns in fake home.

Keep privileged destinations and password handling explicit in operation model. Never put password in argument list or log; keep current protected stdin/credential-provider seam. Do not widen user-local install into root install because `/usr/local/bin` looks conventional.

Shell startup mutation is product-specific: some reviewed installers edit PATH, others print instructions, binstaller uses opt-in environment switch. Preserve that contract instead of applying universal profile-edit rule.

## Useful adversarial tests

Test: checksum mismatch leaving previous binary untouched; archive traversal and symlink escape; bounded expansion failure; interrupted placement/state update; deterministic plan versus executor arguments; repeated apply against same isolated inputs; changed effective inputs invalidating resume. Use fakes/fixtures where possible. Dry-run text assertion alone cannot prove real executor avoided side effects.
