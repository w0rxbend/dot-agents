---
name: obsidian
description: "Read, search, create, and edit notes in the Obsidian vault. Use when the user refers to their Obsidian vault or notes stored in it."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Obsidian, Notes, Markdown, Vault]
    related_skills: []
---

# Obsidian Vault

Use for filesystem-first Obsidian vault work.

## Vault path

Convention: `OBSIDIAN_VAULT_PATH` environment variable, for example from `${HERMES_HOME:-~/.hermes}/.env`. If unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`. Resolve vault path first, pass concrete absolute path. Vault paths may contain spaces: another reason to prefer file tools over shell commands.

If vault path unknown, `terminal` is fine for resolving `OBSIDIAN_VAULT_PATH` or checking fallback path exists. Once path known, switch back to file tools.

## Read a note

`read_file` with resolved absolute path. Prefer over `cat`: gives line numbers and pagination.

## List notes

`search_files` with `target: "files"` and resolved vault path. Prefer over `find` or `ls`.

- All markdown notes: `pattern: "*.md"` under vault path.
- Subfolder: search under its absolute path.

## Search

`search_files` covers filename and content searches. Prefer over `grep`, `find`, or `ls`.

- Filenames: `search_files` with `target: "files"` and filename `pattern`.
- Note contents: `search_files` with `target: "content"` and content regex as `pattern`. Add `file_glob: "*.md"` to restrict matches to markdown notes.

## Create a note

`write_file` with resolved absolute path and full markdown content. Prefer over shell heredocs or `echo`: no shell quoting issues, structured results.

## Append to a note

Prefer native file tools when not awkward:

- Read target note with `read_file`.
- `patch` for anchored append when stable context exists, such as new section after existing heading or before known trailing block.
- `write_file` when rewriting whole note is clearer than fragile patch.

Anchored append with `patch`: replace anchor with anchor plus new content.

Simple append with no stable context: `terminal` acceptable if clearest safe option.

## Targeted edits

`patch` for focused note changes when current content gives stable context. Prefer over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use wikilinks to link related content.
