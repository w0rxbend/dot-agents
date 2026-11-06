# MCP Server Setup for Heroku to Render Migration

Render MCP server: recommended for direct service creation and automated verification; not required for Blueprint path.

## Render MCP Server (Recommended)

Hosted at `https://mcp.render.com/mcp` (recommended, auto-updates). Render plugin (Cursor, Codex, Claude Code) connects over OAuth with a pre-registered client id; no API key needed. Manual MCP clients can use a Render API key from [Account Settings](https://dashboard.render.com/u/*/settings#api-keys). Prefer plugin OAuth; with a manual key, user runs the steps below themselves and never pastes the key into chat.

Alternative: run locally via Docker or binary (see [Render MCP docs](https://render.com/docs/mcp-server)).
Source: [render-mcp-server](https://github.com/render-oss/render-mcp-server)

**Detecting the user's tool:** Infer AI tool from this skill's install path (`~/.cursor/skills/` = Cursor, `~/.claude/skills/` = Claude Code, `~/.codex/skills/` = Codex). Unknown path: ask user which tool they use, then follow matching section below.

### Render plugin (recommended)

If Render plugin is installed, it already declares this MCP server with a pre-registered OAuth client id. Reload tool (restart Cursor or Claude Code, or start a new Codex thread), complete Render OAuth prompt, then retry `list_services()`. Manual API-key setups below are for tools without the plugin.

### Cursor

1. Get a Render API key:
```
https://dashboard.render.com/u/*/settings#api-keys
```

2. Add this to `~/.cursor/mcp.json` (replace `<YOUR_API_KEY>`):
```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_API_KEY>"
      }
    }
  }
}
```

3. Restart Cursor, then retry `list_services()`.

### Claude Code

1. Get a Render API key:
```
https://dashboard.render.com/u/*/settings#api-keys
```

2. Load key without echo, then add MCP server with Claude Code:
```bash
read -rs RENDER_API_KEY && export RENDER_API_KEY
claude mcp add --transport http render https://mcp.render.com/mcp --header "Authorization: Bearer $RENDER_API_KEY"
```

3. Restart Claude Code, then retry `list_services()`.

### Codex

1. Get a Render API key:
```
https://dashboard.render.com/u/*/settings#api-keys
```

2. Set it in shell (no echo, not in history):
```bash
read -rs RENDER_API_KEY && export RENDER_API_KEY
```

3. Add MCP server with Codex CLI:
```bash
codex mcp add render --url https://mcp.render.com/mcp --bearer-token-env-var RENDER_API_KEY
```

4. Restart Codex, then retry `list_services()`.

### Other Tools

Other AI tool: point user to [Render MCP docs](https://render.com/docs/mcp-server) for its setup steps and install method.

## Heroku MCP Server (Optional)

Heroku MCP server auto-discovers config vars, add-on plans, dyno sizes. Without it, skill still works: reads local project files, asks user for config var names manually.

- Requires Heroku CLI v10.8.1+ installed globally
- `heroku mcp:start` uses existing CLI auth (no API key needed)
- Alternative: `npx -y @heroku/mcp-server@1.2.13` (pinned; review before bumping) with `HEROKU_API_KEY` env var
- Heroku CLI sends telemetry by default; `DISABLE_TELEMETRY=true` in server `env` turns it off (either launch method)
- Source: [heroku-mcp-server](https://github.com/heroku/heroku-mcp-server)

Add to MCP config alongside Render server:

```json
{
  "mcpServers": {
    "heroku": {
      "command": "heroku",
      "args": ["mcp:start"],
      "env": {"DISABLE_TELEMETRY": "true"}
    }
  }
}
```

## Verification

After configuring, test connections:
- Ask: "List my Render services" — should return services via Render MCP (required)
- Ask: "List my Heroku apps" — should return apps via Heroku MCP (optional)

If Render MCP fails, reinstall or update Render plugin and reload tool (plugin setup), or check API key and restart MCP client (manual setup).
