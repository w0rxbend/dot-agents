# Local-only skills

This repository does not vendor Codex, Hermes, Claude, or Render system skills. Agents that
ship those skills keep their own copies. Two catalog entries stay external because their
files are not redistributed here.

## VirtusLab Scala Stack

The official [direct-style-scala skill](https://github.com/VirtusLab/scala-skill) has no
verified redistribution grant. Restore it directly with `python3 scripts/install_vss.py`,
then `./install.sh --include-local` (add `--agents all` to target every agent).
The source lives outside managed agent directories to avoid replacing it with a self-link.
The pinned installer adds [the user's Mill preference](../overlays/direct-style-scala/preferences.md);
see [the full setup and research guide](mill-skills.md).

## Local private repository context

`worxbend-private-repository-context` stays on the machine that created it. A clone does not
contain private repository names or observations. When that directory is already present,
`./install.sh --agents all --include-local` links it. See
[the privacy boundaries](repository-skills.md#private-context-on-another-machine).
