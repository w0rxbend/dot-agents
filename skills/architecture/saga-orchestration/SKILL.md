---
name: saga-orchestration
description: "Design sagas for business transactions that span several services or databases: orchestration vs choreography, compensating actions, pivot and retriable steps, outbox, idempotent consumers, semantic locks, timeouts, and mapping to Temporal or Step Functions. Use when a multi-step workflow cannot use one ACID transaction and must recover from partial failure; use using-message-queues for broker setup."
risk: safe
source: community
date_added: "2026-02-27"
---

# Saga Orchestration

Saga replaces one distributed ACID transaction with sequence of local transactions. Each step commits locally and publishes progress; if later step fails, **compensating actions** undo earlier steps. Result: eventual consistency with explicit, testable failure handling.

## Use this skill when

- Operation updates data owned by two or more services or databases (order -> payment -> inventory -> shipping)
- Process runs seconds to days and must survive crashes and restarts (approvals, onboarding, fulfillment)
- Adding compensation, timeouts or recovery to existing multi-service flow

## Do not use this skill when

- All data in one database: use local transaction
- Single idempotent call with retries suffices
- Only broker setup or consumer code needed (use `using-message-queues`)

## 1. Orchestration or Choreography

| Criterion | Orchestration (central coordinator) | Choreography (services react to events) |
|---|---|---|
| Steps | Many (4+) or branching | Few (2-3), linear |
| State visibility | One place to query "where is order 42?" | Rebuilt from events across services |
| Coupling | Orchestrator knows every participant | Participants know only events |
| Flow changes | Frequent: change one component | Rare: changes ripple through services |
| Risk | Orchestrator becomes god service | Cyclic event dependencies, hard debugging |

Default to **orchestration** for more than a few steps, timeouts or human approvals. Use choreography for short, stable flows between autonomous teams.

## 2. Classify Every Step

Put risky, reversible work before point of no return:

| Step type | Meaning | Rule |
|---|---|---|
| **Compensatable** | Semantically undoable (reserve stock -> release stock) | Must have compensation before go-live |
| **Pivot** | Go/no-go point; once it succeeds, saga must complete (e.g. capture payment, ship) | Exactly one per saga, after all compensatable steps |
| **Retriable** | After pivot; guaranteed to eventually succeed (send confirmation email) | Retry until success; no compensation |

Compensations are business operations (refund, cancel, release), not database rollbacks. Each must be idempotent, tolerate original step never having happened, and not fail permanently. If one can fail permanently, define manual escalation path.

## 3. Reliable Messaging: Outbox and Idempotent Consumers

- **Transactional outbox:** write state change and outgoing message in one local transaction on same database. Relay (poller or CDC such as Debezium) publishes from outbox table. Never "commit DB, then publish" as two independent steps.
- **At-least-once delivery is norm,** so every handler and compensation must be **idempotent**:
  - carry saga ID / idempotency key on every command,
  - record processed message IDs in inbox/dedup table, in same transaction as effect,
  - make updates conditional (`UPDATE ... WHERE status = 'RESERVED'`).
- **Correlation:** propagate saga ID and trace context through every message and log line.

## 4. Isolation: Countermeasures for Anomalies

Sagas lack isolation: other transactions see intermediate states. Countermeasures:

| Countermeasure | How | Example |
|---|---|---|
| Semantic lock | Mark records pending (`status = PENDING_APPROVAL`); others handle carefully or wait | Order not shippable until saga completes |
| Commutative updates | Make operation order irrelevant | Credit/debit deltas, not absolute balances |
| Pessimistic view / reorder | Put step most likely read by others late | Make funds available only after all checks |
| Reread value | Check record unchanged before update (optimistic version) | `WHERE version = :v` |
| Version file / by-value | Record operations to reorder or reject by value/risk | High-value orders take stricter path |

## 5. Timeouts and Failure Handling

- Every step has deadline. On timeout, orchestrator decides: retry, compensate, or escalate.
- Retry transient errors with bounded exponential backoff and jitter. Business errors (insufficient funds) are non-retriable: start compensation immediately.
- Persist saga state after every transition (`STARTED -> STEP_n_PENDING -> COMPENSATING -> COMPLETED | FAILED`) so restarted orchestrator resumes.
- Unrecoverable compensation failures go to dead-letter queue plus operator-visible record with saga ID, failed step and reason.

## 6. Durable Execution Engines

Prefer workflow engine, when available, over hand-built saga store and orchestrator:

| Saga concept | Temporal | AWS Step Functions |
|---|---|---|
| Orchestrator | Workflow function (deterministic code, replayed from history) | State machine (Amazon States Language) |
| Step | Activity | Task state (Lambda, SDK integration) |
| Retries / timeouts | Activity retry policy, start-to-close / schedule-to-close timeouts | `Retry` and `TimeoutSeconds` on states |
| Compensation | Workflow code collects compensations, runs them in reverse on failure | `Catch` transitions to compensation states |
| Waiting for humans/events | Signals, timers | Callback task tokens, `Wait` state |
| Saga state | Workflow history | Execution history |

Activities and Lambda tasks still run at least once, so step idempotency stays your job. Check installed SDK/service docs for exact option names. `using-message-queues` skill ships Temporal saga example (its `temporal-order-saga` example directory).

## 7. Test the Failure Paths

- For each step N, inject failure at N. Assert compensations ran for steps 1..N-1 in reverse order and final state is consistent.
- Deliver every message twice and out of order; assert no double effects.
- Kill orchestrator mid-saga, restart; assert it resumes from persisted state.
- Expire each timeout; assert chosen action (retry/compensate/escalate) happens.
- Make compensation fail; assert operators see escalation.

## Done When

- Every step classified (compensatable / pivot / retriable); each compensatable step has idempotent compensation
- Messages go through outbox (or durable engine); consumers deduplicate
- Each isolation anomaly listed with countermeasure
- Every step has timeout and decided timeout action
- Failure-injection tests above pass

## Reference

Read [references/detailed-guide.md](references/detailed-guide.md) for code templates: orchestrator base class with state store, order-fulfillment saga, choreography-based saga, step timeouts. Use [resources/implementation-playbook.md](resources/implementation-playbook.md) as short pre-launch checklist.
