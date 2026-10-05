# dot-agents

[![CI](https://github.com/w0rxbend/dot-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/w0rxbend/dot-agents/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/w0rxbend/dot-agents)](https://github.com/w0rxbend/dot-agents/releases)

My global agent skills, with a portable installer, source inventory, and versioned releases.
Supporting scripts, references, and assets are preserved alongside each skill.
Browse the [full catalog](docs/catalog.md), the [Mill/VSS skills and setup guide](docs/mill-skills.md),
the [repository adaptation and review guide](docs/repository-skills.md),
or the [code quality and design patterns guide](docs/skill-discovery.md).

## Clone and install

Requires **Git, Python 3.10+, and curl** on Linux or macOS. No Python packages, Node.js, or sudo are needed.

```sh
git clone https://github.com/w0rxbend/dot-agents.git ~/.dot-agents
cd ~/.dot-agents
./install.sh
./install.sh check
```

The installer obtains a [dotbot-go](https://github.com/worxbend/dotbot-go) binary if none is on `PATH`
(set `DOTBOT=/path/to/dotbot` to use a specific one), renders `install.conf.yaml` from `catalog.json`,
and applies it with force linking: every included skill becomes a symlink from each supported agent's
global skills directory into this repository, which is the source of truth. Real files or directories
that occupy a link destination are moved to `~/.local/share/dot-agents/backup/<timestamp>/` first;
nothing is silently deleted. Restart your agents after installation.

This installs every included skill into `~/.agents/skills` and `~/.claude/skills`, plus the supported
agents whose configuration directories already exist (Pi, Hermes, Cursor, Gemini, Copilot, OpenCode).
Codex reads `~/.agents/skills` natively.

For the official VirtusLab Scala skill with Mill preferred, restore its pinned upstream source
and link it into the selected agents:

```sh
python3 scripts/install_vss.py
./install.sh install --agents all --include-local
./install.sh check --agents all --include-local
```

See [Mill/VSS setup](docs/mill-skills.md) for the 14 focused skills, examples, and version policy.

To create skills directories for every supported agent on a fresh machine:

```sh
./install.sh install --agents all
./install.sh check --agents all
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

## Bootstrap migration

For a machine whose skills directories currently point at `~/.ubuntu-bootstrap/dotfiles/agents/skills`,
update the dotfiles link configuration first so it does not restore the old root symlinks, then:

```sh
./install.sh install --dry-run
./install.sh install
./install.sh check
```

The previous collection stays at its original path; a conflicting root symlink is moved into the
timestamped backup directory.

## Select agents

```sh
./install.sh install --agents agents,claude,hermes --dry-run
```

Use catalog **install IDs** (`docs/catalog.md`), not upstream display names. Namespaced IDs preserve
different implementations with the same name. Their original frontmatter stays intact, so agents
may display multiple skills with the same name; choose their directory-qualified entry.

Keep the clone in place: installed symlinks point to it. Moving the clone requires rerunning
`install.sh`; it refreshes every link.

## Provider-managed skills

The inventory also records installed hosted and bundled skills that cannot be redistributed or have
no established redistribution permission. Their files are excluded from this public repository.
Use the [provider setup guide](docs/providers.md) to restore them on a new machine.
On a machine where their original files are already present, you can also link them locally:

```sh
./install.sh install --include-local --dry-run
./install.sh install --include-local
./install.sh check --include-local
```

This links existing files; it does not copy, download, enable plugins, or configure accounts.
Plugin-specific connectors, credentials, runtime packages, and tools must be installed separately.
Individual included skills can also require optional tools described in their own `SKILL.md`.

## Update and uninstall

```sh
cd ~/.dot-agents
git pull --ff-only
./install.sh
./install.sh check
./install.sh uninstall --dry-run
./install.sh uninstall
```

Pass the same `--agents` and `--include-local` options used for installation when updating or checking.
Uninstall removes only symlinks that point into this repository and leaves your own files, directories,
and links untouched.

## Install a release

Download `dot-agents-VERSION.tar.gz` and `SHA256SUMS` from [Releases](https://github.com/w0rxbend/dot-agents/releases).
For version 1.2.0, with GitHub CLI installed:

```sh
gh release download v1.2.0 --repo w0rxbend/dot-agents --pattern 'dot-agents-*.tar.gz' --pattern SHA256SUMS
sha256sum -c SHA256SUMS                 # macOS: shasum -a 256 -c SHA256SUMS
tar -xzf dot-agents-1.2.0.tar.gz
cd dot-agents-1.2.0
./install.sh install --agents all
```

An extracted release works without Git. To update it, extract the next release to a permanent
directory and rerun its installer.

## Maintenance

```sh
make check                              # validate snapshot, test installer, verify rendered config
python3 scripts/catalog.py              # regenerate the readable catalog
python3 scripts/import_skills.py --replace # deliberately refresh from recognized global roots
python3 scripts/refresh_review.py           # carry the security review forward
```

The import command uses `~/.agents/skills`, `~/.codex/skills` (including the bundled `.system` and
plugin caches), `~/.pi/agent/skills`, Claude synced/plugin roots, and `~/.hermes/skills`.

[CI](.github/workflows/ci.yml) validates checksums and metadata, tests conflict handling, and installs
the full collection in temporary homes on Linux and macOS. Dependabot updates pinned Actions.
[Tag releases](.github/workflows/release.yml) produce a versioned archive, SHA-256 checksums,
and a GitHub release. See [CONTRIBUTING.md](CONTRIBUTING.md) for the release procedure.

Repository scripts and documentation use MIT. Imported material retains its own terms, including
MIT, Apache-2.0, and FSL-1.1-ALv2. See [THIRD_PARTY.md](THIRD_PARTY.md).
Imported example applications can have flagged dependencies; review [SECURITY.md](SECURITY.md)
before running their helper scripts or installing their packages.
