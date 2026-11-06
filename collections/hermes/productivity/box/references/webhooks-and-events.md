# Webhooks and events

Webhooks: push notifications for file or folder. Events API polling: catch-up, backfill, durable cursor. Webhook management requires custom OAuth Platform App with **Manage webhooks** scope; official Box CLI OAuth app is not sufficient. Act as normal OAuth identity that owns or can access target; not administrator identity unless operation itself requires it.

## Create and inspect a webhook

```bash
box webhooks:list --json
box webhooks:create folder <FOLDER_ID> \
  --triggers FILE.UPLOADED,FILE.VERSION_UPLOADED \
  --address https://example.com/box/webhook --json
```

Confirm destination URL and event triggers before creating webhook.

## Poll user events with a durable cursor

User catch-up and backfill: User Events API through selected OAuth identity. Do not use CLI's default `box events` command: it defaults to enterprise admin-log streams. Persist returned `next_stream_position` after every successful response; use it on next poll:

```bash
box request /events --query "stream_type=changes&stream_position=now" --json
box request /events --query "stream_type=changes&stream_position=<SAVED_CURSOR>" --json
```

Use `stream_position=now` only to initialize future-events cursor. Backfill: start from approved historical cursor or reconcile target folder first, then persist each returned cursor atomically with processed event IDs.

## Application handler contract

When implementing shipped application:

1. Verify Box signature before parsing or acting on body.
2. Persist idempotency keys; deliveries can repeat.
3. Acknowledge quickly, process work asynchronously.
4. Fetch current file or folder from Box; do not trust event payload as final state.
5. Persist Events API cursor when polling.

Test valid event, duplicate event, invalid signature, restart/catch-up path.

## Sources

- [Box webhooks](https://developer.box.com/guides/webhooks/)
- [Events resource](https://developer.box.com/reference/resources/event/)
- [User Events](https://developer.box.com/guides/events/user-events/for-user/)
