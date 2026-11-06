# Nous Portal — authenticating third-party apps against the subscription

Recurring user question: "Can app X (Karakeep, OpenWebUI, LibreChat, OpenViking,
LangChain pipeline, n8n flow, etc.) use my Nous Portal subscription without me
copy-pasting an API key — ideally via the Portal login I already have?"

Three architectural layers, often conflated. Walk them in order before
proposing solutions.

---

## Layer 1 — Is this thing a Hermes plugin, or a separate app?

Answer FIRST. "OpenViking" case trips agents up.

| Surface | What it actually is | Auth path |
|---|---|---|
| **OpenViking memory plugin** (`plugins/memory/openviking/`) | Runs **inside the Hermes process**. LLM calls use Hermes's configured provider. | Uses Portal if Hermes does. Nothing extra. `OPENVIKING_API_KEY` is OpenViking *server's* auth, not LLM auth. |
| **OpenViking the standalone server** (separate container) | Separate context-DB service. Any LLM call it makes is a separate HTTP client. | Like any external app: Layer 2/3 below. |
| **Karakeep, n8n, LibreChat, OpenWebUI, any self-hosted app** | Separate process, often separate machine. Own HTTPS calls to `inference-api.nousresearch.com`. | Layer 2/3 below. |

**Pitfall to avoid**: never pitch "OAuth into Portal" for plugin inside
Hermes. Its LLM call already authenticates via Hermes's provider config.
Plugin's own server auth (e.g. `OPENVIKING_API_KEY` for OpenViking REST API)
is unrelated to Portal.

---

## Layer 2 — For genuinely external apps, what does Portal actually expose?

Portal at `https://inference-api.nousresearch.com/v1`: OpenAI-compatible
inference endpoint, **bearer-token authentication only**:

1. **A static API key** from `portal.nousresearch.com → API Keys`, or
2. **An x402-protocol payment header** (Solana USDC, beta, anonymous, per-request).

**No general OAuth 2.0 authorization server.** No "Sign in with Nous Portal"
SSO for third-party clients. No shared cookie/session carrying browser Portal
login to other apps on same machine.

`hermes login --provider nous` (browser sign-in, token lands in
`~/.hermes/auth.json`) only *feels* like OAuth. It is a **Hermes-specific
browser flow** yielding a credential Hermes uses as bearer. Externally no
OAuth provider, so Karakeep et al. cannot build a client for it.

---

## Layer 3 — Can we bridge the gap without Portal changing anything?

Yes: **local credential-broker proxy**. Without public OAuth, local app can:

1. Read Hermes's existing Portal credential out of `~/.hermes/auth.json`.
2. Expose a local OpenAI-compatible endpoint at `http://localhost:NNNN/v1`.
3. Forward incoming requests to `inference-api.nousresearch.com/v1` with that
   bearer attached.

Karakeep/OpenWebUI/etc. point at `http://localhost:NNNN/v1` with any
placeholder key. Portal key never copied; proxy reuses Hermes's credential.
`hermes proxy start` ships this, bound to `127.0.0.1`. Keep it there: proxy
accepts any bearer, so anyone reaching it spends the subscription. No
`--host 0.0.0.0` without user's OK plus firewall/VPN/auth in front.

Where it could live in Hermes:

- Precedent: `gateway/platforms/api_server.py`, local OpenAI-compatible
  endpoint, but runs full agent loop (tool calls included). Proxy is **pure
  inference pass-through**: no agent loop, no tools, only forwards
  `/chat/completions` upstream with stored Portal bearer.
- ~150 lines: new gateway adapter or plugin under `plugins/`.
- Token refresh: credential pool refresh logic exists if browser-OAuth flow
  yields refreshable token. Long-lived static bearer: simpler.

---

## Real OAuth provider on Portal — when is it worth pitching?

Only when consumer is *another first-party Nous thing* (future SDK,
Nous-branded extension, Discord-bot integration needing per-user delegation,
etc.). Wrong answer for "use my Portal sub with Karakeep": even with Portal
OAuth tomorrow, Karakeep's LLM-provider config UI is `base_url +
bearer_token` with no OAuth client, no callback handler, no token refresh.
OpenAI ecosystem standardized on static bearers; downstream apps won't
rebuild config UX for new auth flow.

Helpful today, shippable by Portal without third-party app changes:

- **Scoped, named, revocable API keys** with last-used timestamps. UX people
  want from OAuth (revoke compromised key, see what uses sub, scope key to
  specific models) in shape every existing app supports.
- **Per-key rate limits**: cap noisy app without eating Hermes's headroom.

---

## Talking-points cheatsheet (for next time)

User asks "can $APP use my Portal subscription":

1. Decide first: Hermes plugin (runs inside Hermes) or separate app? Plugin
   already uses Portal via Hermes's provider config. Done.
2. Separate app, today: paste static API key from Portal → API Keys.
   Base URL `https://inference-api.nousresearch.com/v1`. Rate limits
   subscription-tier based, applied per-key.
3. User pushes back with "but I don't want to paste a key"? Local-broker-proxy
   answer (Layer 3). Worth building. Not Portal-side OAuth roadmap problem.
4. Mixed setup ("Portal for some things, OpenRouter/Ollama Cloud for the
   Hermes agent itself") fully supported. Agent provider/model and tool-side
   LLM calls are independent config; point each at different endpoint.

**Note on the Tool Gateway**: announcement's "no separate accounts, no API key
juggling" pitch covers only Hermes Agent's *tools* (web search, browser, image
gen, TTS) using Portal subscription when Hermes uses Portal as provider.
**Not** a claim that arbitrary third-party apps inherit Portal auth.
