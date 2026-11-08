# Evaluation Path

Evaluate to decide whether skill changes agent behavior.

## Lightweight qualitative check

Run by default:

1. Read skill as an agent would.
2. Simulate one realistic task.
3. Confirm output contract is clear.
4. Check validation is possible.
5. List residual gaps.

## Depth rubric

Score each dimension as pass, partial, or fail:

- Trigger precision.
- Workflow completeness.
- Safety and permission boundaries.
- Output determinism.
- Validation strength.
- Progressive disclosure.

## Baseline comparison

Run deeper baseline-vs-with-skill comparison only when requested or risk is high. Use same task, same inputs, and a holdout case not used while editing.
