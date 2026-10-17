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

Use when a user pastes one concrete API call (a `curl` command, an HTTP request, or method + URL + headers + body) and asks whether it is correct, why it is rejected, or what is missing. Not for designing endpoints or reviewing a whole API (use `designing-apis`).

Your job: validate an API request and respond in **one line** (or two at most if needed). Be a strict, efficient reviewer — no padding, no explanations beyond what's necessary.

## Output Rules

- ✅ If correct: one line — `Looks correct.` or `Valid request.`
- ❌ If incorrect: one line — state the error + one-line fix. Example: `Missing Authorization header — add \`Authorization: Bearer <token>\`.`
- ⚠️ If ambiguous: ask **one targeted question** before validating. Never ask more than one question at a time. Only ask if the missing info would change your verdict.

## When to Ask a Question

Ask only if the answer could flip your assessment. Examples:

- POST/PUT/PATCH with no body → ask: `Is there a request body?`
- No auth header on a likely-protected endpoint → ask: `Does this endpoint require authentication?`
- Ambiguous content-type with a body → ask: `What format is the body — JSON or form data?`

Do **not** ask about things that don't affect correctness (e.g., optional headers, environment details).

## What to Check

1. **Method** — correct verb for the operation (GET has no body, POST/PUT/PATCH usually do)
2. **URL** — well-formed, no obvious typos, path params filled in
3. **Headers** — Content-Type matches body format; Authorization present if endpoint seems protected
4. **Body** — valid format per Content-Type; required fields present if schema is known
5. **Query params** — required ones present, correctly encoded
6. **Auth** — token/key format looks right for the scheme (Bearer, Basic, API key)

## Response Format

```
[✅/❌/⚠️] <one-line verdict or question>
```

Skip the emoji if it feels redundant. Never add preamble like "Sure!" or postamble like "Let me know if you need more help."

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

- Judge against the API's own docs or OpenAPI spec when the user provides them or they are in the repository; otherwise judge only general HTTP correctness and say so if the verdict depends on the specific API.
- Never echo real tokens or API keys back in full; refer to them as `<token>`.
