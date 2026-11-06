# Render MCP Troubleshooting

## Connection Errors

### "MCP server not found" or tool not available

**Cause:** MCP server not configured in AI tool.

**Fix:** Follow setup instructions in main SKILL.md. On Render plugin: reinstall or update it, then reload tool so it loads plugin's MCP server. On manual clients: add config, then restart tool.

### "Connection refused" or timeout

**Cause:** Network issue or incorrect URL.

**Fix:**
- Verify URL is exactly `https://mcp.render.com/mcp`
- Some corporate firewalls block MCP connections — try different network

### "Transport error" or "SSE not supported"

**Cause:** Wrong transport or URL.

**Fix:**
- Use HTTP transport (streamable HTTP), not SSE
- URL should be `https://mcp.render.com/mcp`, not `https://mcp.render.com/sse`
- Claude Code: use `--transport http` flag

## Authentication Errors

### "Unauthorized" or 401

**Cause:** Missing or expired OAuth authorization (plugin setup), or missing, invalid, or expired API key (manual setup).

**Fix:**
1. Plugin setup: reinstall or update Render plugin, reload tool, then complete Render OAuth prompt.
2. Manual setup: generate new API key (`https://dashboard.render.com/u/*/settings#api-keys`) and update it in tool's MCP config.
3. Restart tool.
4. Verify with `list_services()`.

### "Forbidden" or 403

**Cause:** OAuth authorization or API key lacks access to requested resource, or wrong workspace.

**Fix:**
- Check active workspace with `get_selected_workspace()`
- Switch workspaces if needed with `list_workspaces()`
- Ensure API key belongs to account with workspace access

## Tool-Specific Issues

> Installed Render plugin? It provides MCP server over OAuth. Manual notes below apply to hand-configured MCP clients.

### Cursor

- Config file: `~/.cursor/mcp.json`
- Must be valid JSON (no trailing commas)
- Fully restart Cursor after config changes (not just reload window)
- If multiple MCP servers configured, ensure `render` key is unique

### Claude Code

- Added via CLI: `claude mcp add --transport http render https://mcp.render.com/mcp --header "Authorization: Bearer $RENDER_API_KEY"` (key exported via `read -rs`, never typed inline)
- To update: `claude mcp remove render` then re-add
- To list: `claude mcp list`

### Codex

- Requires `RENDER_API_KEY` env var set in shell where Codex runs
- Added via: `codex mcp add render --url https://mcp.render.com/mcp --bearer-token-env-var RENDER_API_KEY`
- If env var not set when Codex starts, MCP auth fails

## Workspace Issues

### "No workspace selected"

**Fix:** Run `list_workspaces()` to see available workspaces, then ask user to select one.

### Operations return empty results

**Cause:** Active workspace has no services, or wrong workspace selected.

**Fix:** Verify with `get_selected_workspace()`, switch if needed.

## MCP vs CLI Fallback

If MCP cannot be configured (network restrictions, unsupported tool), fall back to Render CLI. See **render-cli** for setup and usage. Render CLI sends usage analytics by default; `export RENDER_CLI_DISABLE_ANALYTICS=1` before any `render` command. Same gates as MCP: confirm deploys and write SQL with user first.

| Capability | MCP | CLI |
|-----------|-----|-----|
| List services | `list_services()` | `render services -o json` |
| View logs | `list_logs(...)` | `render logs -r SVC` |
| Deploy | `trigger_deploy(serviceId)` | `render deploys create SVC --wait` |
| Metrics | `get_metrics(...)` | Not available |
| SQL queries | `query_render_postgres(...)` | `render psql DB -c "SQL"` |
| SSH | Not available | `render ssh SVC` |
