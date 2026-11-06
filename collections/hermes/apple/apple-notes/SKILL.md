---
name: apple-notes
description: "Manage Apple Notes via memo CLI: create, search, edit."
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, note-taking]
    related_skills: [obsidian]
prerequisites:
  commands: [memo]
---

# Apple Notes

Use `memo` to manage Apple Notes from terminal. Notes sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Notes.app
- Install: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app when prompted (System Settings → Privacy → Automation)

## When to Use

- User asks to create, view or search Apple Notes
- User wants cross-device sync (iPhone/iPad/Mac): prefer Apple Notes
- Organize notes into folders
- Export notes to Markdown/HTML

## When NOT to Use

- Obsidian vault or Markdown-native knowledge management → use `obsidian` skill
- Bear Notes → separate app (not supported here)
- Quick agent-only notes that don't need sync → use `memory` tool instead

## Quick Reference

### View Notes

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Create Notes

```bash
memo notes -a                     # Add a note (opens your $EDITOR)
memo notes -a -f "Folder Name"    # Add a note into a specific folder
```

`-a`/`--add` is a bare flag: opens `$EDITOR` to compose note. Does not take a title argument.
Use `-f/--folder` to target a folder. Set `$EDITOR` first (e.g. `export EDITOR=vim`).

### Edit Notes

```bash
memo notes -e                     # Interactive selection to edit
```

### Delete Notes

```bash
memo notes -d                     # Interactive selection to delete
```

### Move Notes

```bash
memo notes -m                     # Move note to folder (interactive)
```

Before `-e`, `-d` or `-m`: show user the exact note title and folder, get explicit confirmation, then select only that note in the prompt. Changes sync to every iCloud device.

### Export Notes

```bash
memo notes -ex                    # Export to HTML/Markdown
```

## Limitations

- Cannot edit notes containing images or attachments
- Interactive prompts need terminal access (use pty=true if needed)
