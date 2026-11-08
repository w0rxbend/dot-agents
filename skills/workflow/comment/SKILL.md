---
name: comment
description: "Post a comment on a ClickUp task through a connected ClickUp MCP server or tool, after resolving the task and getting the user's confirmation. Use when the user asks to comment on, reply to or add a note to a ClickUp task (for example `/comment ABC123 text`); not for GitHub, Jira or Linear comments."
---

# ClickUp: Comment on a Task

Usage: `/comment <task-id> [comment text]`. Task ID: `#ABC123` or `ABC123`.

## Preconditions

- ClickUp MCP server or tool must be connected this session. Check available tools for ClickUp task-lookup and add-comment operations.
- If none connected, stop. Say ClickUp is not connected and how to connect it (e.g. authenticate ClickUp plugin or MCP server in client). Offer to draft comment text instead. Never call ClickUp API with guessed credentials or URLs.
- Take parameter names from connected tool's schema. Do not assume them.

## Procedure

1. **Parse** task ID (strip leading `#`) and comment text. If no text given, ask. Multi-line fine.
2. **Resolve the task** with tool's task lookup. Teams may use ClickUp custom task IDs (such as `ABC-123`) besides internal IDs. Use tool's custom-ID lookup option if it has one. Confirm exactly one match. None or several: report, ask for correct ID or task URL.
3. **Confirm before writing.** Posting is visible to others and can notify them. Show:

   ```
   Task:    <task name> (<id>), <status>, <list>
   Comment:
   <comment text>
   Notify:  <only assignees/default | all followers, if requested>
   Post this comment? (yes/no)
   ```

   Post only after explicit yes. Exception: comment the user dictated word for word this turn, with clear instruction to post, counts as confirmed. Still show resolved task name.
4. **Post** with tool's add-comment operation. Pass notify-all option only if user asked to notify all followers.
5. **Report** "Comment posted to <task name>" with task URL from tool's response. Include comment ID if returned.

## Formatting

ClickUp comments generally render Markdown (bold, italic, inline code, code blocks, lists, links). For long comment, offer to structure it with short summary line first. Keep task mentions and links as user wrote them.

## Errors

| Situation | Action |
|---|---|
| Tool missing or unauthenticated (401/403) | Stop, report, suggest reconnecting. Keep draft so user can retry. |
| Task not found (404) or ambiguous | Ask for task URL or correct ID. Do not post to near match. |
| Rate limited (429) or transient error | Retry once after short wait, then report. Never post duplicates. If retry outcome unclear, check task comments first. |
| Comment rejected (too long, bad content) | Report tool message, offer shortened version. |

## Done When

- User saw resolved task and approved text. Comment posted exactly once.
- Reply has task name and URL (plus comment ID if available), or clear failure reason with no partial writes.
