# Saga Orchestration Playbook

## When to choose orchestration vs choreography

- Choose orchestration when business flow needs visibility and centralized control.
- Choose choreography for high autonomy and low coupling.

## Saga design checklist

- Define explicit saga state machine.
- Define timeout policy per step.
- Define compensation for each compensatable step (pivot and retriable steps get none).
- Use idempotency keys in command handling.
- Store correlation IDs across all events and logs.

## Failure handling

- Retry transient failures with bounded exponential backoff.
- Escalate non-recoverable failures to compensation state.
- Capture operator-visible failure reason and current step.

## Verification

- Simulate failure at every step; confirm compensation path.
- Validate duplicate message handling.
- Validate recovery after orchestrator restart.
