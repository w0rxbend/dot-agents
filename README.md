# 🧠 dot-agents

Personal skills for Claude, Codex, Hermes, OpenCode, Cursor, Grok, and the shared `~/.agents` root.

[![CI](https://github.com/w0rxbend/dot-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/w0rxbend/dot-agents/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/w0rxbend/dot-agents)](https://github.com/w0rxbend/dot-agents/releases)

One clone. [dotbot-go](https://github.com/worxbend/dotbot-go) symlinks each skill into the agents that are already on the machine. This repo stays the source of truth.

## ⚡ Install

Git and Python 3.10+ on Linux or macOS. No extra Python packages and no sudo.

```sh
git clone https://github.com/w0rxbend/dot-agents.git ~/.dot-agents
~/.dot-agents/install
```

That is the whole install. `install` calls `install.sh`, which plans the links and hands them to dotbot-go. If `dotbot` is not on `PATH`, the script downloads the pinned [dotbot-go v0.4.2](https://github.com/worxbend/dotbot-go/releases/tag/v0.4.2) binary into `~/.local/bin/dotbot` and checks its SHA-256. Set `DOTBOT` to use another binary.

Update later:

```sh
cd ~/.dot-agents
git pull --ff-only
./install
```

A real file that sits on a link destination is moved to `~/.local/share/dot-agents/backup/<timestamp>/` first. Override that directory with `DOTAGENTS_BACKUP`. Restart the agents after install.

Check the links, or preview without writing:

```sh
./install check
./install install --dry-run
```

Remove the links this repo created:

```sh
./install uninstall
```

## 🗣️ Voice

Always on. The linked files are a skill router. Every answer, PR description, review comment, code comment, commit message, and other agent output uses three skills together:

| Skill | What it controls |
| --- | --- |
| 🎯 `i-have-adhd` | Shape. Next action first, numbered steps, short lists. |
| 🪨 `caveman` | Words. Answer first, no fluff, no emoji. |
| ✂️ `ponytail` | Size. Smallest complete change, plus what was skipped. |

Their own "wait for the slash command" gates do not apply. Any code edit also loads `code-complete`, `clean-code-guard`, and the review and optimization skills named in the router. `./install` links:

| Agent | File |
| --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` |
| Codex | `~/.codex/AGENTS.md` |
| Hermes | `~/.hermes/SOUL.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` |
| Cursor | `~/.cursor/rules/voice.mdc` |
| Grok | `~/.grok/rules/voice.md` |

Claude is always linked. The others link when that agent's config directory already exists (`~/.codex`, `~/.hermes`, `~/.config/opencode`, `~/.cursor`, `~/.grok`). Codex reads `AGENTS.override.md` instead of `AGENTS.md` when the override file exists. This installer does not write the override. An existing Hermes `SOUL.md` is backed up, then replaced with a symlink.

The shared text is [`instructions/VOICE.md`](instructions/VOICE.md).

## 📚 Skills

348 skills live under [`skills/`](skills). Two more stay off Git and are linked only with `--include-local`. The full table is [`docs/catalog.md`](docs/catalog.md).

| | Group | What is in it |
| --- | --- | --- |
| 🗣️ | [`voice`](skills/voice) | ADHD, caveman, ponytail, and the caveman companions. 14 skills. |
| 🧰 | [`workflow`](skills/workflow) | How to plan, test, review, commit, and write. 43 skills. |
| 🏗️ | [`architecture`](skills/architecture) | System shape, patterns, GRASP, sagas. 9 skills. |
| 🖥️ | [`backend`](skills/backend) | APIs, CLIs, service structure. 9 skills. |
| 🤖 | [`agents`](skills/agents) | Agent memory, traces, and scheduling. 4 skills. |
| 📈 | [`ops`](skills/ops) | Performance, incidents, app observability. 6 skills. |
| 🔐 | [`security`](skills/security) | App and infra hardening, audits, compliance. 12 skills. |
| 🗄️ | [`data`](skills/data) | Databases, pipelines, analytics. 11 skills. |
| ☁️ | [`platforms`](skills/platforms) | AWS, Azure, GCP, Docker, Kubernetes, GitHub Actions. 26 skills. |
| 🎨 | [`frontend`](skills/frontend) | UI, Astro, dashboards, accessibility. 19 skills. |
| 🎮 | [`pixi`](skills/pixi) | PixiJS v8. 9 skills. |
| 🐹 | [`go`](skills/go) | Go modules, layout, CI, libraries. 46 skills. |
| ☕ | [`scala`](skills/scala) | Scala collections, types, functional patterns. 9 skills. |
| 🧱 | [`mill`](skills/mill) | Mill builds, including VirtusLab Scala Stack. 14 skills. |
| 🔤 | [`languages`](skills/languages) | Java, Kotlin, Python, Lua, Nim, Rust, Effect, fp-ts, and more. 44 skills. |
| 🏠 | [`domain`](skills/domain) | worxbend repo context and project-specific skills. 15 skills. |
| 🧑 | [`mattpocock`](skills/mattpocock) | Adapted Matt Pocock skills. 29 skills. |
| 📗 | [`zio`](skills/zio) | ZIO docs skills and the ZIO HTTP / core routers. 28 skills. |
| 🧬 | [`scala-zio`](skills/scala-zio) | Direct ZIO reference pack. 1 skill. |

Matt Pocock's `code-review` shares a name with the workflow skill. It is linked into Claude, Codex, Hermes, Cursor, Gemini, Copilot, and OpenCode. It is not linked into `~/.agents/skills` or Pi, because those hosts drop one of the two.

## 🔌 Where skills land

| Agent | Skills directory |
| --- | --- |
| Shared, also read by Codex and Pi | `~/.agents/skills` |
| Claude Code | `~/.claude/skills` |
| Codex | `~/.codex/skills` |
| Pi | `~/.pi/agent/skills` |
| Hermes | `~/.hermes/skills` |
| Cursor | `~/.cursor/skills` |
| Gemini CLI | `~/.gemini/skills` |
| GitHub Copilot CLI | `~/.copilot/skills` |
| OpenCode | `~/.config/opencode/skills` |

Default install links `~/.agents/skills` and `~/.claude/skills`, plus every other agent whose config directory already exists. Force a set with `./install install --agents all` or `./install install --agents claude,hermes,grok`. `grok` links the voice rule only. Grok reads skills from `~/.agents/skills`.

Codex, Hermes, Claude, and Render system skills are not in this repo. They stay with the agent that ships them.

## 📦 Local-only skills

VirtusLab direct-style Scala, and private repository context, stay off Git.

```sh
python3 scripts/install_vss.py
./install install --include-local
```

`--include-local` only links files that are already on the machine. Details: [`docs/providers.md`](docs/providers.md). Mill setup: [`docs/mill-skills.md`](docs/mill-skills.md).

## 🔧 Maintain

```sh
just check
```

That validates the catalog, runs the installer tests, and checks `install.conf.yaml`.

Add or edit a skill under `skills/<group>/<name>/`. Then:

```sh
python3 scripts/catalog.py
./install.sh render
just check
```

Do not copy another agent's bundled skills into this repo. Adapted skills keep their upstream license. `sources/local-forks.json` records the ones that were changed from the original.
