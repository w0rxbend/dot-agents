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

If no [dotbot-go](https://github.com/worxbend/dotbot-go) binary is on `PATH` (set `DOTBOT=/path/to/dotbot`
to use a specific one), the installer downloads the pinned release (v0.4.2) into `~/.local/bin/dotbot`
and verifies its SHA-256 before using it. It then plans the links for the selected agents from
`catalog.json`, renders exactly those links into a temporary dotbot-go configuration, and applies it
with force linking: each included skill becomes a symlink from an agent's global skills directory into
this repository, which is the source of truth. Real files, directories, and symlinks you made yourself
that occupy a link destination are moved to `<home>/.local/share/dot-agents/backup/<timestamp>/` first
(override with `DOTAGENTS_BACKUP`); nothing is silently deleted. Links into this repository that fall
outside the current install scope (for example after a scope change) are removed. Restart your agents
after installation.

By default the installer links `~/.agents/skills` and `~/.claude/skills`, plus every supported agent
whose configuration directory already exists (Codex, Pi, Hermes, Cursor, Gemini, Copilot, OpenCode).
Not every collection goes to every agent; see [Install scope](#install-scope).

The committed [`install.conf.yaml`](install.conf.yaml) is a reference rendering that does not depend on
the machine: it lists every agent, links `~/.agents/skills` and `~/.claude/skills` unconditionally, and
gates every other agent with `if: test -d "$HOME/<agent dir>"`. `./install.sh render` regenerates it
after a catalog change and `./install.sh render --check` verifies it; installing never rewrites it.

For the official VirtusLab Scala skill with Mill preferred, restore its pinned upstream source
and link it into the selected agents:

```sh
python3 scripts/install_vss.py
./install.sh install --agents all --include-local
./install.sh check --agents all --include-local
```

See [Mill/VSS setup](docs/mill-skills.md) for the 14 focused skills, examples, and version policy.

`--agents` (a comma-separated list, or `all`) installs exactly those agents and creates their
directories even when the agent is not installed yet. To do that for every supported agent:

```sh
./install.sh install --agents all
./install.sh check --agents all
```

| Agent | Global skills directory |
| --- | --- |
| Shared (`agents`; read by Codex and Pi) | `~/.agents/skills` |
| Claude Code (`claude`) | `~/.claude/skills` |
| Codex (`codex`) | `~/.codex/skills` |
| Pi (`pi`) | `~/.pi/agent/skills` |
| Cursor | `~/.cursor/skills` |
| Gemini CLI | `~/.gemini/skills` |
| GitHub Copilot CLI | `~/.copilot/skills` |
| OpenCode | `~/.config/opencode/skills` |
| Hermes | `~/.hermes/skills` |

The Codex and Claude Code locations follow their [Codex](https://learn.chatgpt.com/docs/build-skills)
and [Claude Code](https://code.claude.com/docs/en/skills) documentation. Other targets provide conventional
skills directories; discovery and required tools depend on each agent's version and configuration.
Cowork and hosted sessions use their provider's skill settings rather than these local directories.
Agents other than Shared and Claude Code are linked by default only when their directory exists
(`~/.codex`, `~/.pi/agent`, `~/.hermes`, `~/.cursor`, `~/.gemini`, `~/.copilot`, `~/.config/opencode`).

### Install scope

`install.sh` (`COLLECTION_AGENTS` and `PI_SCOPED_COLLECTIONS`) limits some collections to some agents:

| Collection | Installed into |
| --- | --- |
| `hermes` | Hermes only (`~/.hermes/skills`) |
| `codex-system` | Codex only (`~/.codex/skills`) |
| `claude-design`, `claude-engineering`, `claude-productivity` | every agent except Claude Code, which already loads them as plugins |
| any collection other than `shared`, `agent-squad`, `zio-skills`, `scala-zio-skills` | not `~/.agents/skills` or `~/.pi/agent/skills`: Pi reads both and drops same-named skills |
| everything else | every selected agent |

The rules combine: the Claude plugin collections, for example, go to Codex, Hermes, Cursor, Gemini,
Copilot, and OpenCode. Codex therefore sees the shared collections through `~/.agents/skills` and the
rest through `~/.codex/skills` only when `~/.codex` exists or `--agents` includes `codex`.

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
Uninstall removes every symlink in the selected agents' skills directories that points into this
repository (including dangling ones), plus, with `--include-local`, the links to the local
provider-managed sources. It leaves your own files, directories, and other links untouched.

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
python3 scripts/refresh_review.py       # record skills whose tree changed since review
python3 scripts/refresh_review.py --list   # list the skills that still need review
python3 scripts/refresh_review.py --mark-reviewed all-changed --note "what was read and why it is fine"
./install.sh render                     # regenerate install.conf.yaml
```

Each row in `docs/skill-review.json` records the tree `sha256` it was reviewed at. `refresh_review.py`
carries matching rows forward and marks changed and new skills `reviewed: false` with a `needs_review`
reason; `validate.py` (and so `make check`) fails until a maintainer has read them and run
`--mark-reviewed` with comma-separated install IDs or `all-changed` plus a `--note`, which is kept in
the row's `review_log`.

The import builds the new snapshot in `.collections.import/` and swaps it in only when it is complete.
Global roots that are links into this repository (as after `./install.sh`) are skipped, an import that
finds no vendorable skills keeps the existing snapshot, and one that would drop more than half of the
vendored skills is refused unless `--allow-shrink` is passed.

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
