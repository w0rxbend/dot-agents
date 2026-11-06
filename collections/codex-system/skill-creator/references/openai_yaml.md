# openai.yaml fields (full example + descriptions)

`agents/openai.yaml` is extended, product-specific config read by machine/harness, not agent. Other product-specific config can also live in `agents/`.

## Full example

```yaml
interface:
  display_name: "Optional user-facing name"
  short_description: "Optional user-facing description"
  icon_small: "./assets/small-400px.png"
  icon_large: "./assets/large-logo.svg"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt to use the skill with"

dependencies:
  tools:
    - type: "mcp"
      value: "github"
      description: "GitHub MCP server"
      transport: "streamable_http"
      url: "https://api.githubcopilot.com/mcp/"

policy:
  allow_implicit_invocation: true
```

## Field descriptions and constraints

Top-level constraints:

- Quote all string values.
- Keep keys unquoted.
- For `interface.default_prompt`: generate short, helpful (typically 1 sentence) example starting prompt from skill. It must explicitly mention skill as `$skill-name` (e.g., "Use $skill-name-here to draft a concise weekly status update.").

- `interface.display_name`: Human-facing title shown in UI skill lists and chips.
- `interface.short_description`: Short human-facing UI blurb (25–64 chars) for quick scanning.
- `interface.icon_small`: Small icon asset path (relative to skill dir). Default to `./assets/`; put icons in skill's `assets/` folder.
- `interface.icon_large`: Larger logo asset path (relative to skill dir). Default to `./assets/`; put icons in skill's `assets/` folder.
- `interface.brand_color`: Hex color for UI accents (e.g., badges).
- `interface.default_prompt`: Default prompt snippet inserted when invoking skill.
- `dependencies.tools[].type`: Dependency category. Only `mcp` supported for now.
- `dependencies.tools[].value`: Tool or dependency identifier.
- `dependencies.tools[].description`: Human-readable dependency explanation.
- `dependencies.tools[].transport`: Connection type when `type` is `mcp`.
- `dependencies.tools[].url`: MCP server URL when `type` is `mcp`.
- `policy.allow_implicit_invocation`: When false, skill is not injected into
  model context by default but can still be invoked explicitly via `$skill`.
  Defaults to true.
