# Artifact trust and filesystem ownership

## Verify before execution or installation

Keep artifact selection, version resolution, verification, extraction, placement, and state commit as identifiable stages. A lockfile pins the resolved inputs; a checksum must match the intended artifact from the same release/version. A digest downloaded from the same compromised location is integrity evidence, not automatically independent authenticity. Preserve signature policy where implemented; do not call unsigned artifacts signed or turn optional signature validation into a silently required new dependency. See [binary lock, verification, installer knobs, and signature scope](https://github.com/worxbend/binstaller/blob/5dec30c5d4d25b3d41fc4774bddf3256712cec56/README.md).

The reviewed Go Nerd Fonts implementation permits a warning-only fallback when its checksum manifest cannot be fetched. Distinguish this existing best-effort behavior from a strict verification guarantee; retain or strengthen it only within the requested change, and make docs/tests agree. See [checksum-fetch policy](https://github.com/worxbend/nerd-fonts-installer/blob/bb8c29811dca2d7e945bfc84c177683717eb3956/internal/fonts/installer.go).

Reject checksum mismatch before replacing an existing executable. Stage into an isolated directory on the intended filesystem, validate staged files, and commit only known outputs. Preserve the old installation or the tool's documented rollback behavior when the final operation fails; do not claim a multi-file transaction is atomic if only individual renames are.

## Extraction is a bounded parser

Follow each format's supported entry policy. Validate normalized member paths and link targets against the extraction root; reject absolute paths, parent traversal, unsafe symlink/hardlink chains, duplicate/conflicting entries, and unsupported special files according to the current extractor contract. A lexical path prefix is not enough when an existing ancestor is a symlink. Do not preserve archive modes that make installed files unexpectedly writable or privileged.

Keep independent limits for compressed download bytes, inflated bytes, extracted bytes, member count, individual files, and elapsed work where the implementation uses them. Truncated headers or short reads are errors, not a clean archive end. Check progress inside decompression/copy loops instead of only before opening the file. See [archive path, size, link, and deadline enforcement](https://github.com/worxbend/binstaller/blob/5dec30c5d4d25b3d41fc4774bddf3256712cec56/core/src/binstaller/core/ArchiveExtractor.scala) and [font extraction boundary](https://github.com/worxbend/nerd-fonts-installer-scala/blob/c77ccca5c5ab0cb63630b6b83d6a13f69d25438e/core/src/io/worxbend/nerdfonts/install/ArchiveExtractor.scala).

## Dotfiles and privilege

Distinguish a managed symlink from a regular user file, a directory, and a broken symlink. Cleanup should remove only entries covered by the selected directive's documented ownership rules. Preserve conflict/relink/force semantics rather than making force the default. Test traversal, parent symlinks, existing targets, and reruns in a fake home.

Keep privileged destinations and password handling explicit in the operation model. Never place a password in an argument list or log; preserve the current protected stdin/credential-provider seam. Do not broaden a user-local install into a root install because `/usr/local/bin` looks conventional.

Shell startup mutation is product-specific: some reviewed installers edit PATH, others print instructions, and binstaller makes it an opt-in environment switch. Preserve that contract instead of applying a universal profile-edit rule.

## Useful adversarial tests

Test a checksum mismatch leaving the previous binary untouched; archive traversal and symlink escape; bounded expansion failure; interrupted placement/state update; deterministic plan versus executor arguments; repeated apply against the same isolated inputs; and changed effective inputs invalidating resume. Use fakes/fixtures where possible. A dry-run text assertion alone cannot prove the real executor avoided side effects.
