---
name: saga-orchestration
description: "Design sagas for business transactions that span several services or databases: orchestration vs choreography, compensating actions, pivot and retriable steps, outbox, idempotent consumers, semantic locks, timeouts, and mapping to Temporal or Step Functions. Use when a multi-step workflow cannot use one ACID transaction and must recover from partial failure; use using-message-queues for broker setup."
risk: safe
source: community
date_added: "2026-02-27"
---

# Saga Orchestration

A saga replaces one distributed ACID transaction with a sequence of local transactions. Each step commits locally and publishes progress; if a later step fails, earlier steps are undone by **compensating actions**. The result is eventual consistency with explicit, testable failure handling.

## Use this skill when

- An operation updates data owned by two or more services or databases (order -> payment -> inventory -> shipping)
- A business process runs for seconds to days and must survive crashes and restarts (approvals, onboarding, fulfillment)
- You need to add compensation, timeouts or recovery to an existing multi-service flow

## Do not use this skill when

- All data lives in one database: use a local transaction
- A single idempotent call with retries suffices
- You only need broker setup or consumer code (use `using-message-queues`)

## 1. Orchestration or Choreography

| Criterion | Orchestration (central coordinator) | Choreography (services react to events) |
|-----------|-------------------------------------|----------------------------------------|
| Number of steps | Many (4+) or branching | Few (2-3), linear |
| Visibility of state | One place to query "where is order 42?" | Reconstructed from events across services |
| Coupling | Orchestrator knows every participant | Participants know only events |
| Change frequency of the flow | Frequent: change one component | Rare: changes ripple through services |
| Risk | Orchestrator becomes a god service | Cyclic event dependencies, hard debugging |

Default to **orchestration** when the flow has more than a few steps, timeouts or human approvals; use choreography for short, stable flows between autonomous teams.

## 2. Classify Every Step

Order the steps so that risky, reversible work happens before the point of no return:

| Step type | Meaning | Rule |
|-----------|---------|------|
| **Compensatable** | Can be semantically undone (reserve stock -> release stock) | Must have a compensation defined before go-live |
| **Pivot** | The go/no-go point; once it succeeds the saga must complete (e.g. capture payment, ship) | Exactly one per saga; place after all compensatable steps |
| **Retriable** | After the pivot; guaranteed to succeed eventually (send confirmation email) | Retry until success; no compensation |

Compensations are business operations (refund, cancel, release), not database rollbacks. They must be idempotent, must tolerate the original step having never happened, and must not fail permanently; if they can, define a manual escalation path.

## 3. Reliable Messaging: Outbox and Idempotent Consumers

- **Transactional outbox:** write the state change and the outgoing message to the same database in one local transaction; a relay (poller or CDC such as Debezium) publishes from the outbox table. Never "commit DB, then publish" as two independent steps.
- **At-least-once delivery is the norm,** so every handler and compensation must be **idempotent**:
  - carry a saga ID / idempotency key on every command,
  - record processed message IDs in an inbox/dedup table inside the same transaction as the effect,
  - make updates conditional (`UPDATE ... WHERE status = 'RESERVED'`).
- **Correlation:** propagate saga ID and trace context through every message and log line.

## 4. Isolation: Countermeasures for Anomalies

Sagas lack isolation: other transactions see intermediate states. Apply countermeasures:

| Countermeasure | How | Example |
|----------------|-----|---------|
| Semantic lock | Mark records as pending (`status = PENDING_APPROVAL`) so others treat them carefully or wait | Order not shippable until saga completes |
| Commutative updates | Design operations so order doesn't matter | Credit/debit deltas instead of absolute balances |
| Pessimistic view / reorder | Put the step most likely to be read by others late | Make funds available only after all checks |
| Reread value | Check the record hasn't changed before updating (optimistic version) | `WHERE version = :v` |
| Version file / by-value | Record operations to reorder or reject based on value/risk | High-value orders take a stricter path |

## 5. Timeouts and Failure Handling

- Every step has a deadline; on timeout the orchestrator decides: retry, compensate, or escalate.
- Retry transient errors with bounded exponential backoff and jitter; classify business errors (insufficient funds) as non-retriable and start compensation immediately.
- Persist saga state after every transition (`STARTED -> STEP_n_PENDING -> COMPENSATING -> COMPLETED | FAILED`) so a restarted orchestrator resumes.
- Unrecoverable compensation failures go to a dead-letter queue plus an operator-visible record with the saga ID, failed step and reason.

## 6. Durable Execution Engines

Rather than building a saga store and orchestrator, use a workflow engine when available:

| Saga concept | Temporal | AWS Step Functions |
|--------------|----------|--------------------|
| Orchestrator | Workflow function (deterministic code, replayed from history) | State machine (Amazon States Language) |
| Step | Activity | Task state (Lambda, SDK integration) |
| Retries / timeouts | Activity retry policy, start-to-close / schedule-to-close timeouts | `Retry` and `TimeoutSeconds` on states |
| Compensation | Code in workflow: collect compensations, run them in reverse on failure | `Catch` transitions to compensation states |
| Waiting for humans/events | Signals, timers | Callback task tokens, `Wait` state |
| Saga state | Workflow history | Execution history |

Activities and Lambda tasks are still executed at least once, so step idempotency remains your job. Check the installed SDK/service docs for exact option names. The `using-message-queues` skill ships a Temporal saga example (its `temporal-order-saga` example directory).

## 7. Test the Failure Paths

- For each step N, inject a failure at N and assert compensations ran for steps 1..N-1 in reverse order, and that final state is consistent.
- Deliver every message twice and out of order; assert no double effects.
- Kill the orchestrator mid-saga; restart and assert it resumes from persisted state.
- Expire each timeout; assert the chosen action (retry/compensate/escalate) happens.
- Make a compensation fail; assert escalation is visible to operators.

## Done When

- Every step is classified (compensatable / pivot / retriable) and every compensatable step has an idempotent compensation
- Messages are published via an outbox (or a durable engine) and consumers deduplicate
- Isolation anomalies are listed with a countermeasure each
- Every step has a timeout and a decided timeout action
- The failure-injection tests above pass

## Reference

Read [references/detailed-guide.md](references/detailed-guide.md) for code templates: an orchestrator base class with state store, an order-fulfillment saga, a choreography-based saga and step timeouts. Use [resources/implementation-playbook.md](resources/implementation-playbook.md) as a short pre-launch checklist.
