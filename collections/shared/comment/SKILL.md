---
name: comment
description: "Post a comment on a ClickUp task through a connected ClickUp MCP server or tool, after resolving the task and getting the user's confirmation. Use when the user asks to comment on, reply to or add a note to a ClickUp task (for example `/comment ABC123 text`); not for GitHub, Jira or Linear comments."
---

# ClickUp: Comment on a Task

Usage: `/comment <task-id> [comment text]`. The task ID may be written `#ABC123` or `ABC123`.

## Preconditions

- A ClickUp MCP server or tool must be connected in this session. Check your available tools for ClickUp task-lookup and add-comment operations.
- If none is connected, stop. Tell the user that ClickUp is not connected and how to connect it (for example, by authenticating the ClickUp plugin or MCP server in their client), and offer to draft the comment text instead. Never call the ClickUp API with guessed credentials or URLs.
- Take parameter names from the connected tool's schema. Do not assume them.

## Procedure

1. **Parse** the task ID (strip a leading `#`) and any comment text. If no text was given, ask for it; multi-line text is fine.
2. **Resolve the task** with the connected tool's task lookup. Teams may use ClickUp custom task IDs (such as `ABC-123`) as well as internal IDs, so use the lookup option for custom IDs if the tool has one. Confirm that exactly one task matches. If none or several match, report that and ask for the correct ID or the task URL.
3. **Confirm before writing.** Posting is visible to other people and can notify them. Show the user:

   ```
   Task:    <task name> (<id>), <status>, <list>
   Comment:
   <comment text>
   Notify:  <only assignees/default | all followers, if requested>
   Post this comment? (yes/no)
   ```

   Post only after an explicit yes. A comment that the user dictated word for word in this turn, with a clear instruction to post it, counts as confirmed. Still show the resolved task name.
4. **Post** with the connected tool's add-comment operation. Pass the notify-all option only if the user asked to notify all followers.
5. **Report** "Comment posted to <task name>" with the task URL from the tool's response. If the tool returns a comment ID, include it.

## Formatting

ClickUp comments generally render Markdown (bold, italic, inline code, code blocks, lists, links). If the comment is long, offer to structure it with a short summary line first. Keep task mentions and links as the user wrote them.

## Errors

| Situation | Action |
|---|---|
| Tool missing or unauthenticated (401/403) | Stop, report it, and suggest reconnecting. Keep the drafted text so the user can retry. |
| Task not found (404) or ambiguous | Ask for the task URL or the correct ID. Do not post to a near match. |
| Rate limited (429) or transient error | Retry once after a short wait, then report. Never post duplicates; if a retry outcome is unclear, check the task's comments first. |
| Comment rejected (too long, bad content) | Report the tool's message and offer a shortened version. |

## Done When

- The user saw the resolved task and approved the text, and the comment was posted exactly once.
- The reply includes the task name and URL (and the comment ID if available), or a clear failure reason with no partial writes.
