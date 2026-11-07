# Local documentation MCP setup and diagnostics

Only when user explicitly asks to configure or troubleshoot official OpenAI documentation MCP server in a supported **local Codex client**. Missing docs tool during ordinary docs request is not a setup request: answer with root skill's official-domain web fallback, without installation, sandbox escalation, configuration changes or restart.

## Verify the supported local setup

1. Search and fetch current official Codex MCP setup docs when those tools are callable. Otherwise search and fetch relevant official OpenAI docs directly.
2. Confirm documented endpoint is `https://developers.openai.com/mcp`. Verify supported command or configuration against current docs before recommending it.
3. When current docs support it, local Codex CLI setup:

   ```sh
   codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
   ```

   Equivalent documented configuration:

   ```toml
   [mcp_servers.openaiDeveloperDocs]
   url = "https://developers.openai.com/mcp"
   ```

4. Check supported local client's MCP listing or configuration, enabled state, relevant workspace/admin policy, any documented authentication requirement. Verify success from actual command result, configuration, or callable docs-tool search/fetch. Never claim installation or access without evidence.
5. Recommend local-client restart or new local session only when current official docs or observed client behavior require it. Name which local client must refresh.

Skill dependency declaration, configured server or local-client setup does not make a tool callable in an already running session. Editing hosted container's local configuration cannot install a tool into host or model's current tool inventory. Never claim local command installed server into current hosted session.

Local installation or configuration change only when user explicitly authorizes it. Never request sandbox escalation, edit hosted configuration, install a dependency or ask user to restart hosted session merely to answer ordinary docs question.
