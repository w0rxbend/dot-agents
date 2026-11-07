# Codex network approvals / sandbox notes

Fallback CLI mode only. Read when user explicitly asks for `scripts/image_gen.py` / CLI / API / model controls, or explicitly confirms transparent-output request should use `gpt-image-1.5` true-transparency fallback path.

This guidance varies by environment and may go stale. When in doubt, prefer your environment's defaults.

## Why am I asked to approve image generation calls?
Fallback CLI uses OpenAI Image API, so needs outbound network access. Many Codex setups disable network by default and/or approval policy requires confirmation before networked commands run.

## Important note about approvals vs network
- `--ask-for-approval never` suppresses approval prompts.
- It does **not** by itself enable network access.
- In `workspace-write`, network access still depends on Codex configuration (for example `[sandbox_workspace_write] network_access = true`).

## How do I reduce repeated approval prompts?
If you trust repo and want fewer prompts, use configuration or profile that both:
- enables network for sandbox mode you plan to use
- sets approval policy matching your risk tolerance

Example `~/.codex/config.toml` pattern:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true
```

For quieter automation once network is enabled, stricter approval policy is an option. Choose it deliberately, with care.

## Safety note
Enabling network and reducing approvals lowers friction but raises risk when running untrusted code or working in untrusted repository.
