# Iteration Path

Use when improving a skill from outcomes, traces, examples, or user feedback.

## Gather examples

Collect:

- Positive examples where skill helped.
- Negative examples where skill misfired.
- Fix examples showing desired behavior.
- Any validation output or user correction.

Remove secrets and unrelated personal data before storing examples.

## Diagnose

For each example, identify whether problem is:

- Triggering: skill loaded too often or not often enough.
- Routing: wrong reference or workflow branch.
- Instruction gap: missing step, safety rule, or output requirement.
- Validation gap: no check caught failure.
- Overload: too much context or too many steps.

## Patch

Make smallest instruction change that would have changed outcome. When feasible, retest against at least one positive and one negative example.
