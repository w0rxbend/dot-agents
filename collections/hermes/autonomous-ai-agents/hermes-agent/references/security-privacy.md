# Security & Privacy Toggles

Common "why is Hermes doing X to my output / tool calls / commands?" toggles, with exact commands. Most read once at startup, so need fresh session (`/reset` in chat, or new `hermes` invocation).

### Secret redaction in tool output

**On by default.** Tool output (terminal stdout, `read_file`, web content, subagent summaries, etc.) gets scanned for API-key, token, and secret lookalikes before entering context and logs. Keep enabled normally:

```bash
hermes config set security.redact_secrets true       # keep enabled globally
```

**Restart required.** `security.redact_secrets` is snapshotted at import time. Toggling mid-session (e.g. `export HERMES_REDACT_SECRETS=false` from tool call) will NOT affect running process. Tell user to change config from terminal, then start new session. Deliberate: stops LLM flipping toggle on itself mid-task.

Disable only to deliberately see raw credential-like strings (debugging, redactor development):
```bash
hermes config set security.redact_secrets false
```

### PII redaction in gateway messages

Separate from secret redaction. Enabled: gateway hashes user IDs, strips phone numbers from session context before model sees it:

```bash
hermes config set privacy.redact_pii true    # enable
hermes config set privacy.redact_pii false   # disable (default)
```

### Command approval prompts

Default `approvals.mode: smart`: auxiliary LLM assesses shell commands flagged destructive (`rm -rf`, `git reset --hard`, etc.). Modes:

- `smart` — auto-approve low-risk command once, deny high-risk, prompt when uncertain (default)
- `manual` — always prompt
- `off` — skip all approval prompts (equivalent to `--yolo`)

```bash
hermes config set approvals.mode smart       # recommended middle ground
hermes config set approvals.mode off         # bypass everything (not recommended)
```

Per-invocation bypass without changing config (same risk as `off`; only on explicit user request, ideally with sandboxed terminal backend):
- `hermes --yolo …`
- `export HERMES_YOLO_MODE=1`

Note: YOLO / `approvals.mode: off` does NOT turn off secret redaction. Independent.

### "Reset permissions" / "make Hermes ask again"

User usually means: wipe accumulated "Always allow" state. NOT yolo mode.
NOT per-edit diff prompt: none exists, file writes never hit approval prompt,
only shell commands do. Two stores hold it:

1. Shell-command allowlist: `hermes config set command_allowlist '[]'`
2. Shell-hook consent (only if present): `rm -f ~/.hermes/shell-hooks-allowlist.json`

Then sanity-check `hermes config get approvals.mode` (should not be `off`).
Confirm `--yolo` isn't baked into launch alias or systemd unit.

### Shell hooks allowlist

Some shell-hook integrations need explicit allowlisting before firing. Managed via `~/.hermes/shell-hooks-allowlist.json`; prompted interactively first time a hook runs.

### Disabling the web/browser/image-gen tools

Keep model off network or media tools: open `hermes tools`, toggle per-platform. Takes effect next session (`/reset`). Toolset list: `references/configuration.md`.

