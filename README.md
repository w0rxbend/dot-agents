# dot-agents

[![CI](https://github.com/w0rxbend/dot-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/w0rxbend/dot-agents/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/w0rxbend/dot-agents)](https://github.com/w0rxbend/dot-agents/releases)

My global agent skills, with a portable installer, source inventory, and versioned releases.
Supporting scripts, references, and assets are preserved alongside each skill.
Browse the [full catalog](docs/catalog.md), the [Mill/VSS skills and setup guide](docs/mill-skills.md),
or the [code quality and design patterns guide](docs/skill-discovery.md).

## Clone and install

Requires **Git and Python 3.10+** on Linux or macOS. No Python packages, Node.js, or sudo are needed for installation.

```sh
git clone https://github.com/w0rxbend/dot-agents.git ~/.dot-agents
cd ~/.dot-agents
./install.sh
./install.sh --check
```

This installs every included skill into `~/.agents/skills` and `~/.claude/skills`, plus the supported
agents whose configuration directories already exist. Codex reads `~/.agents/skills` natively.
Restart your agents after installation.

For the official VirtusLab Scala skill with Mill preferred, restore its pinned upstream source
and link it into the selected agents:

```sh
python3 scripts/install_vss.py
./install.sh --agents all --include-local
./install.sh --agents all --include-local --check
```

See [Mill/VSS setup](docs/mill-skills.md) for the 14 focused skills, examples, and version policy.

To create skills directories for every supported agent on a fresh machine:

```sh
./install.sh --agents all
./install.sh --agents all --check
```

| Agent | Global skills directory |
| --- | --- |
| Shared / Codex | `~/.agents/skills` |
| Claude Code | `~/.claude/skills` |
| Codex compatibility directory, with `--agents codex` or `all` | `~/.codex/skills` |
| Cursor | `~/.cursor/skills` |
| Gemini CLI | `~/.gemini/skills` |
| GitHub Copilot CLI | `~/.copilot/skills` |
| OpenCode | `~/.config/opencode/skills` |
| Hermes | `~/.hermes/skills` |

The Codex and Claude Code locations follow their [Codex](https://learn.chatgpt.com/docs/build-skills)
and [Claude Code](https://code.claude.com/docs/en/skills) documentation. Other targets provide conventional
skills directories; discovery and required tools depend on each agent's version and configuration.
Cowork and hosted sessions use their provider's skill settings rather than these local directories.

## Existing skills and bootstrap migration

The installer adds one symlink per catalog entry. It keeps unrelated files and backs up conflicts only
when you explicitly pass `--replace`. It refuses to write through an existing skills-directory symlink.

For a machine whose skills directories currently point at `~/.ubuntu-bootstrap/dotfiles/agents/skills`:

```sh
./install.sh --replace --dry-run
./install.sh --replace
./install.sh --check
```

Backups remain next to the original entry as `NAME.dot-agents-backup-TIMESTAMP`.
The old bootstrap collection remains available at its original path. If you rerun a dotfiles manager,
update its link configuration first so it does not restore the old root symlinks.

## Select agents or skills

```sh
./install.sh --agents agents,claude,hermes --dry-run
./install.sh --agents agents,claude --skills clean-code,refactoring-guru,gof-patterns,design-patterns
./install.sh --target ~/.config/my-agent/skills
```

Use catalog **install IDs**, not upstream display names, with `--skills`. Namespaced IDs preserve
different implementations with the same name. Their original frontmatter stays intact, so agents
may display multiple skills with the same name; choose their directory-qualified entry.

Keep the clone in place: installed symlinks point to it. Moving the clone requires rerunning
`install.sh`; it retargets links it previously managed.

## Provider-managed skills

The inventory also records installed hosted and bundled skills that cannot be redistributed or have
no established redistribution permission. Their files are excluded from this public repository.
Use the [provider setup guide](docs/providers.md) to restore them on a new machine.
On a machine where their original files are already present, you can also link them locally:

```sh
./install.sh --include-local --replace --dry-run
./install.sh --include-local --replace
./install.sh --include-local --check
```

This links existing files; it does not copy, download, enable plugins, or configure accounts.
Plugin-specific connectors, credentials, runtime packages, and tools must be installed separately.
Individual included skills can also require optional tools described in their own `SKILL.md`.

## Update and uninstall

```sh
cd ~/.dot-agents
./update.sh
./install.sh --check
./uninstall.sh --dry-run
./uninstall.sh
```

Pass the same `--agents`, `--target`, and `--include-local` options used for installation when updating
or checking. Uninstall accepts `--agents` or `--target`; it removes only unchanged symlinks recorded
in `.dot-agents-install.json`. It keeps backups, original skills, and entries you changed yourself.
To restore a backed-up root symlink, uninstall first, move any remaining new-directory content aside,
and rename the backup to its original name.

## Install a release

Download `dot-agents-VERSION.tar.gz` and `SHA256SUMS` from [Releases](https://github.com/w0rxbend/dot-agents/releases).
For version 1.0.1, with GitHub CLI installed:

```sh
gh release download v1.0.1 --repo w0rxbend/dot-agents --pattern 'dot-agents-*.tar.gz' --pattern SHA256SUMS
sha256sum -c SHA256SUMS                 # macOS: shasum -a 256 -c SHA256SUMS
tar -xzf dot-agents-1.0.1.tar.gz
cd dot-agents-1.0.1
./install.sh --agents all
```

An extracted release works without Git. To update it, extract the next release to a permanent
directory and rerun its installer. `update.sh` is for Git clones.

## Maintenance

```sh
make check                              # validate snapshot and test installer
python3 scripts/catalog.py              # regenerate the readable catalog
python3 scripts/import_skills.py --replace # deliberately refresh from recognized global roots
```

The import command uses `~/.agents/skills`, Codex system/plugin roots, Claude synced/plugin roots,
and `~/.hermes/skills`. It excludes deleted skills, uninstalled marketplace catalogs, project-local
skills, dependency examples, and duplicate development mirrors. Check source licenses before
adding a new collection; update `licenses/upstream/index.json` and retain upstream notices.

[CI](.github/workflows/ci.yml) validates checksums and metadata, tests conflict handling, and installs
the full collection in temporary homes on Linux and macOS. Dependabot updates pinned Actions.
[Tag releases](.github/workflows/release.yml) produce a versioned archive, SHA-256 checksums,
and a GitHub release. See [CONTRIBUTING.md](CONTRIBUTING.md) for the release procedure.

Repository scripts and documentation use MIT. Imported material retains its own terms, including
MIT, Apache-2.0, and FSL-1.1-ALv2. See [THIRD_PARTY.md](THIRD_PARTY.md).
Imported example applications can have flagged dependencies; review [SECURITY.md](SECURITY.md)
before running their helper scripts or installing their packages.
