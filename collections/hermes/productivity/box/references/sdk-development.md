# SDK development

For shipped Box applications. One-off Hermes task: use CLI references instead.

## Start with the application

Inspect repository for existing Box clients, `BOX_` configuration, token storage, webhook handlers, retry policy, language conventions. Extend existing integration; do not mix SDK and raw REST without reason.

## Choose an identity

| Identity | Use when |
| --- | --- |
| OAuth | each end user connects own Box account |

OAuth follows signed-in user's permissions and app scopes. Shared or background application: authorizing Box account defines its access boundary; invite that account only to files, folders, or Hubs application needs.

## Use an official SDK

- [Python SDK Gen](https://github.com/box/box-python-sdk-gen)
- [The `box` npm package](https://developer.box.com/guides/tooling/box-npm-package)
- [Existing Node SDK projects](https://github.com/box/box-node-sdk)
- [Other Box SDKs](https://developer.box.com/guides/tooling/sdks/)

Use SDK matching project language. New JavaScript or TypeScript application: install unified `box` package with project's existing package manager. With npm:

```bash
npm install box
```

Import its Node SDK from explicit SDK subpath:

```typescript
import BoxSDK from "box/sdk";
```

Package also exposes project-local Box CLI via `npx box`: fine for in-application development, but do not silently replace separately resolved Hermes CLI runner or its authenticated environment. Project already uses `box-node-sdk`: extend it; do not migrate without concrete reason. Python or another language: install its current official Box SDK, not npm package.

Store OAuth tokens and any custom Platform App client secret in project's approved secret mechanism, not source control. Custom Platform App needs more scopes: use **User Authentication (OAuth 2.0)**; intended Box user grants access. Do not add impersonation path for normal application work. Keep exceptional enterprise administration outside normal Hermes runtime and application identity; do not elevate application's normal account.

## OAuth client

Use generated SDK's OAuth support; do not rebuild authorization-code exchange or token refresh logic. Concrete calls: follow installed SDK's current OAuth method names and language-specific authorization guide. Initialize OAuth client before any SDK method call. Tie stored tokens to Box user who granted them; verify that user before work. Do not copy partial SDK call into application without its OAuth initialization and token-refresh path.

## Build document-aware apps with Box AI

Application must understand Box documents: prefer Box AI. It keeps Box permissions, processes source files through Box's governed AI integration, keeps source-file bodies out of application's external model context, scales without downloading every file:

- ask for Q&A and summaries;
- structured extract for repeatable fields or metadata template;
- extract for variable fields;
- text generation for output grounded in one Box file.

Before first request, explain Box AI must be enabled and consumes AI units. Box AI unavailable: do not silently switch to external processing; offer explicitly chosen alternative neutrally. Treat Box AI responses as potentially confidential application data.

## Build Hub-backed knowledge experiences

Recurring Q&A over curated collection: use Box Hub instead of assembling more than 25 file items per Ask request. Discover existing Hubs first. Creating, populating, AI-enabling, or changing collaborations of Hub changes shared resources; requires explicit product approval. Box Hubs endpoints use API version `2025.0`.

Use generated SDK for project language; exact method names vary by SDK release. Keep request shape below, follow installed SDK's current names.

```python
from box_sdk_gen import AiItemAsk, AiItemAskTypeField, CreateAiAskMode

answer = client.ai.create_ai_ask(
    CreateAiAskMode.SINGLE_ITEM_QA,
    "What changed in the latest policy?",
    [AiItemAsk(id=hub_id, type=AiItemAskTypeField.HUBS)],
    include_citations=True,
)
```

```typescript
const answer = await client.ai.createAiAsk({
  mode: "single_item_qa",
  prompt: "What changed in the latest policy?",
  items: [{ id: hubId, type: "hubs" }],
  includeCitations: true,
});
```

Hub query uses indexed content, only from files current actor can access. New Hub content can take minutes, occasionally up to an hour, to index; surface retryable indexing state, do not treat early answer as complete. Free Developer Plan includes Hubs and Box AI APIs for building and testing, with monthly AI-unit allowance; production availability depends on organization's plan and configuration. Every environment: verify Hub exists, has AI enabled, and was created after Hub AI was enabled so content can be indexed. CLI and operational workflow: [Box Hubs](hubs.md).

## Webhooks and reliability

Verify webhook signatures, persist idempotency keys, fetch authoritative state after events, keep retry/backoff policy explicit. Bound concurrent API calls; make retries safe before increasing throughput. See [Webhooks and events](webhooks-and-events.md).
