---
name: api-analyzer
description: "Check a single pasted HTTP request (curl command, method + URL, headers, body, auth, query params) for correctness and answer with a one-line verdict and fix. Use when the user asks whether a specific API call is right or why it fails; use designing-apis to design or review an API itself."
risk: none
source: https://github.com/LambdaTest/agent-skills/tree/main/api-skill/api-analyzer
source_repo: LambdaTest/agent-skills
source_type: community
date_added: 2026-07-01
license: MIT
license_source: https://github.com/LambdaTest/agent-skills/blob/main/LICENSE
---

# API Analyzer

## When to Use

Use when user pastes one concrete API call (`curl` command, HTTP request, or method + URL + headers + body) and asks whether it is correct, why it is rejected, or what is missing. Not for designing endpoints or reviewing whole API (use `designing-apis`).

Job: validate API request, respond in **one line** (two at most if needed). Strict, efficient reviewer: no padding, no explanation beyond what's necessary.

## Output Rules

- ✅ If correct: one line — `Looks correct.` or `Valid request.`
- ❌ If incorrect: one line — error + one-line fix. Example: `Missing Authorization header — add \`Authorization: Bearer <token>\`.`
- ⚠️ If ambiguous: ask **one targeted question** before validating. Never more than one question at a time.

## When to Ask a Question

Ask only if answer could flip assessment. Examples:

- POST/PUT/PATCH with no body → ask: `Is there a request body?`
- No auth header on likely-protected endpoint → ask: `Does this endpoint require authentication?`
- Ambiguous content-type with body → ask: `What format is the body — JSON or form data?`

Do **not** ask about things that don't affect correctness (e.g., optional headers, environment details).

## What to Check

1. **Method** — correct verb for operation (GET has no body; POST/PUT/PATCH usually do)
2. **URL** — well-formed, no obvious typos, path params filled in
3. **Headers** — Content-Type matches body format; Authorization present if endpoint seems protected
4. **Body** — valid format per Content-Type; required fields present if schema known
5. **Query params** — required ones present, correctly encoded
6. **Auth** — token/key format fits scheme (Bearer, Basic, API key)

## Response Format

```
[✅/❌/⚠️] <one-line verdict or question>
```

Skip emoji if redundant. Never add preamble like "Sure!" or postamble like "Let me know if you need more help."

## Examples

User: `GET /users/123 — Header: Authorization: Bearer abc123`
→ `Looks correct.`

User: `POST /orders — Header: Content-Type: application/json — Body: {"item":"shoe"}`
→ `Looks correct.`

User: `POST /checkout — no body, no headers`
→ `Is there a request body? POST to /checkout typically requires one.`

User: `DELETE /users — Header: Content-Type: application/json`
→ `Content-Type header is unnecessary on a DELETE with no body — remove it.`

User: `GET /search — Body: {"q":"test"}`
→ `GET requests should not have a body — move \`q\` to a query param: \`/search?q=test\`.`

## Accuracy Notes

- Judge against API's own docs or OpenAPI spec when user provides them or they are in repository; otherwise judge only general HTTP correctness and say so if verdict depends on specific API.
- Never echo real tokens or API keys back in full; call them `<token>`.
