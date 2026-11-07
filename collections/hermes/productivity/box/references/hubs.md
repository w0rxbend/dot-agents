# Box Hubs

Box Hub: recurring Q&A over curated knowledge base. Direct Box AI Ask takes up to 25 selected files; Hub request sends one `hubs` item and searches Hub's indexed content. Do not use Hub for metadata extraction or text generation.

## Check availability and discover an existing Hub

Box Free Developer Plan includes Hubs API, Box AI APIs, monthly AI-unit allowance for building and testing. Do not read Box web-app plan wording as blanket API restriction. CLI calls same APIs and does not bypass account entitlements; production availability depends on organization's plan and Box configuration.

Before first Hub AI request, state: Box AI must be enabled, consumes AI units, answers only use indexed files actor can access. Do not wait for acknowledgement. Hubs are not files or folders: never use `folders:items 0` to discover or reject Hub invitation. Confirm actor, list accessible Hubs before proposing new one:

```bash
box users:get me --json --fields id,name,login
box hubs --scope all --max-items 1000 --json
box hubs --query "Product" --scope all --sort relevance --json
box hubs:get <HUB_ID> --json
box hubs:items <HUB_ID> --max-items 100 --json
```

Known Hub URL or ID: run `box hubs:get <HUB_ID>` directly, even with empty list. Report Hub as `https://app.box.com/hubs/<HUB_ID>`. Check `is_ai_enabled`, then one bounded Hub Ask request to verify real API availability. Box AI for Hubs must be enabled before Hub creation so Box can index content. Hub AI unavailable: distinguish disabled feature, Hub created before AI enablement, indexing delay, missing Hub collaboration, missing underlying-file access, exhausted AI units. Do not silently download source files into Hermes' model context.

## Ask questions across a Hub

One Hub item, `single_item_qa`, citations requested so Hermes can report source files. Use `box request` (or SDK), not `box ai:ask`; installed CLI versions may not accept Hub item types. This hits Box AI Ask endpoint; `box-version: 2025.0` header is required for `/hubs` management endpoints, not this request.

```bash
box request /ai/ask -X POST \
  --body '{"mode":"single_item_qa","items":[{"id":"<HUB_ID>","type":"hubs"}],"prompt":"Summarize the approved renewal terms and cite each source.","include_citations":true}' \
  --json
```

Give Hub ID and navigation link with answer; list cited file IDs, names, links when Box returns citations. Answer is bounded by indexed, accessible Hub content; do not claim it searched unindexed files or files actor cannot access.

## Create and populate a Hub

Do not create Hub automatically. Q&A over more than 25 files or reusable curated collection: find existing accessible Hub first. None fits: offer curated Hub; get explicit approval before creating or populating it. User declines: narrow one-off scope with search or metadata.

After approval, create, report link, verify:

```bash
box hubs:create "Policy knowledge base" --description "Approved policy reference" --json
box hubs:get <HUB_ID> --json
```

Adding item curates reference; it does not move underlying file or folder. Clearly requested small addition needs no redundant prompt. Confirm bulk additions or removals; verify every returned result; read back Hub items. Multi-item changes can partially succeed: successful request alone does not prove every item was added.

```bash
box hubs:items:manage <HUB_ID> \
  --add id=<FILE_ID>,type=file --json
box hubs:items:manage <HUB_ID> \
  --add id=<FOLDER_ID>,type=folder --json
box hubs:items <HUB_ID> --max-items 100 --json
```

Without `parent-id`, CLI adds item to first Item List block. Specific Item List block: list pages with `box hubs:document:pages <HUB_ID> --json`, get blocks with `box hubs:document:blocks <HUB_ID> <PAGE_ID> --json`, pass returned Item List block ID as `parent-id`.

Confirm before enabling or disabling Hub AI, deleting or copying Hub, or changing shared access. Verify each change with `box hubs:get`, `box hubs:items`, or `box hubs:collaborations`:

```bash
box hubs:update <HUB_ID> --ai-enabled --json
box hubs:collaborations <HUB_ID> --max-items 100 --json
box hubs:collaborations:create <HUB_ID> --role viewer --user-id <USER_ID> --json
```

## Handle indexing, permissions, and limits

New content usually indexes within minutes, but can take up to an hour. Verify addition, wait or retry bounded number of times, report retryable indexing state; do not declare source absent. Diagnose permissions separately: successful `box hubs` or `box hubs:get` proves Hub access, not access to every underlying file.

Box AI for Hubs has service limits per Hub and across enterprise. Box's Hubs guidance currently documents 20,000 files per Hub; near that limit, verify current account or product documentation. Do not present that number as immutable guarantee. Only first 4 MB of supported document's text representation is indexed. Confirm material batch or broad Hub population.

## Sources

- [Box Hubs API overview](https://developer.box.com/guides/hubs-api/)
- [Box Free Developer Plan](https://developer.box.com/guides/getting-started/free-developer-plan/)
- [Box AI Ask API](https://developer.box.com/reference/post-ai-ask/)
- [Ask questions about a Hub](https://developer.box.com/guides/box-ai/ai-tutorials/ask-questions/)
- [Box AI for Hubs](https://support.box.com/hc/en-us/articles/29347206309395-Box-AI-for-Hubs)
- [Box Hubs limits](https://support.box.com/hc/en-us/articles/28323495455123-Box-Hubs-Known-Issues-and-Limitations)
