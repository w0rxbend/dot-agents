---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed."
disable-model-invocation: true
---

Turn current conversation context and codebase understanding into a spec. Do NOT interview the user; synthesize what you already know.

Issue tracker and triage label vocabulary should already be provided. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

1. Explore repo to understand current codebase state, if not already done. Use project's domain glossary vocabulary throughout spec. Respect any ADRs in area you're touching.

2. Sketch seams for testing the feature. Prefer existing seams over new ones. Use highest seam possible. If new seams are needed, propose them as high as possible. Fewer seams across codebase is better. Ideal is one.

Confirm with user that these seams match their expectations.

3. Write spec using template below. Strip secrets, credentials and private data: tracker may be public. Show user final spec; publish to project issue tracker only after they confirm. Apply `ready-for-agent` triage label (may start autonomous agents). No additional triage needed.

<spec-template>

## Problem Statement

Problem the user faces, from user's perspective.

## Solution

Solution to the problem, from user's perspective.

## User Stories

A LONG, numbered list of user stories. Format each as:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

Make list extremely extensive, covering all aspects of the feature.

## Implementation Decisions

List of implementation decisions made. Can include:

- Modules to be built/modified
- Interfaces of those modules to be modified
- Technical clarifications from developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may go stale quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it in the relevant decision. Briefly note it came from a prototype. Trim to decision-rich parts: not a working demo, only the important bits.

## Testing Decisions

List of testing decisions made. Include:

- What makes a good test (only test external behavior, not implementation details)
- Modules to test
- Prior art for the tests (similar tests in codebase)

## Out of Scope

Things out of scope for this spec.

## Further Notes

Further notes about the feature.

</spec-template>
