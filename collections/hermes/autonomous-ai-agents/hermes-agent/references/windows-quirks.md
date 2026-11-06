# Windows-Specific Quirks

Hermes runs natively on Windows (PowerShell, cmd, Windows Terminal, git-bash
mintty, VS Code integrated terminal). Most just works; a handful of Win32 vs
POSIX differences bite. Document new ones here as you hit them.

### Input / Keybindings

**Alt+Enter doesn't insert a newline**: Windows Terminal (and mintty) grab it
for fullscreen before prompt_toolkit sees it. Use **Ctrl+Enter** (CLI binds it
to newline on Windows; raw Ctrl+J also works, harmlessly). See how terminal
reports a keystroke: `python scripts/keystroke_diagnostic.py` from repo root.

### Config / Files

**HTTP 400 "No models provided" on first run**: `config.yaml` saved with UTF-8
BOM (Notepad does this). Re-save as UTF-8 without BOM; `hermes config edit`
writes correctly.

### `execute_code` / Sandbox

**WinError 10106** from sandbox child: can't create `AF_INET` socket. Usual
root cause: Hermes's env scrubber dropping `SYSTEMROOT`/`WINDIR`/`COMSPEC`
(Python's `socket` needs `SYSTEMROOT` to find `mswsock.dll`), not broken
Winsock LSP. `_WINDOWS_ESSENTIAL_ENV_VARS` allowlist in
`tools/code_execution_env.py` covers it. Still hit it? Print `os.environ.get("SYSTEMROOT")`
inside `execute_code` block (not whole `os.environ`: may hold secrets), confirm it is set.

### Testing on Windows

Prepare checkout through PM first. With its Python 3.14, build independent
test environment at fresh path:

```powershell
python -m pm.build_env --source . --out .venv --group dev --group test
```

Output must not exist. Before regeneration, stop its processes, explicitly
remove only that disposable environment. Do not install into application
payload or modify a selected dependency generation.

Run canonical runner through Git Bash:

```bash
scripts/run_tests.sh tests/foo/test_bar.py -v --tb=short
```

Runner discovers `.venv/Scripts/python.exe`, clears credentials and
`PYTHONPATH`, isolates each test file. External test environment: set
`HERMES_PYTHON` to its Python executable. PM shell activation alone does not
supply pytest once runner clears `PYTHONPATH`.

### Path / Filesystem

**Line endings.** Git may warn `LF will be replaced by CRLF`. Cosmetic; repo's
`.gitattributes` normalizes. Don't let editors auto-convert committed
POSIX-newline files to CRLF.

**Forward slashes work almost everywhere.** Every Hermes tool and most Windows
APIs accept `C:/Users/...`. Prefer forward slashes in code and logs: avoids
shell-escaping backslashes in bash.
