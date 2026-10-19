# Product Analytics: Events, Funnels, Cohorts, North Star, Experiments

Read this when the work is in-product analytics (activation, retention, feature adoption, experiments) rather than marketing-site tracking. All numbers below are illustrative, not benchmarks.

## Before instrumenting

Record, in the tracking plan: the product decision the data informs, the source of truth (app DB, billing, analytics tool), the consent rules that apply, the reporting time zone, and the unit of analysis (user, account, device, session).

## Event taxonomy by lifecycle stage

Name events `object_past_tense_verb` (`user_signed_up`, `upgrade_completed`), never bare verbs (`signup`, `click`, `conversion`).

```python
PRODUCT_EVENTS = {
    # Acquisition
    "user_signed_up":         ["source", "medium", "campaign"],
    "onboarding_completed":   ["time_to_complete_s", "steps_skipped"],
    # Activation
    "first_value_reached":    ["trigger", "session_number"],   # your "aha" moment
    "feature_discovered":     ["feature_name", "discovery_method"],
    # Retention
    "session_started":        ["days_since_last", "platform"],
    # Revenue
    "upgrade_viewed":         ["trigger", "current_tier"],
    "upgrade_completed":      ["tier", "plan", "revenue"],
    "subscription_canceled":  ["reason", "tier", "tenure_days"],
    "payment_failed":         ["attempt_count", "error_code"],
}
```

Do not put user-generated text (messages, search queries, form contents) in properties.

## PostHog server-side capture (Python)

Verified against `posthog` 7.x, where `capture` takes the event first and `distinct_id` as a keyword, and person properties are set with `set` (older SDKs used `capture(distinct_id, event, ...)` and `identify`). Check the installed version before copying.

```python
import os
from posthog import Posthog

posthog = Posthog(
    os.environ["POSTHOG_API_KEY"],
    host=os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com"),
)

def track(user_id: str, event: str, properties: dict | None = None) -> None:
    posthog.capture(event, distinct_id=user_id, properties=properties or {})

def set_person_properties(user_id: str, traits: dict) -> None:
    posthog.set(distinct_id=user_id, properties=traits)

track("user_123", "session_started", {"platform": "web", "days_since_last": 2})
# call posthog.shutdown() on process exit so queued events are flushed
```

Feature flags: in 7.x, `feature_enabled(key, distinct_id)` is deprecated in favor of evaluating once per request:

```python
flags = posthog.evaluate_flags(user_id)
if flags.is_enabled("new-onboarding-v2") is True:   # None/False -> safe default path
    show_new_onboarding()
else:
    show_old_onboarding()
```

Do not send events or identify users before consent where the project requires it.

## Funnel analysis

Illustrative activation funnel (hypothetical numbers): landing visit 100% -> clicked "try" 40% -> signed up 28% -> first value 17% -> returned next day 8.5% -> active 3+ days in week 3.4% -> converted to paid 0.7%.

For each step whose drop-off is worse than your own baseline:
1. Locate where users leave (step and screen).
2. Find out why (session recordings, surveys, error logs).
3. Form a hypothesis for a change.
4. Test it with a pre-registered experiment (see below).
5. Measure over the predefined window and sample: effect with interval, data quality checks, guardrail metrics. Do not stop early on a favorable p-value; check for sample-ratio mismatch and tracking loss.
6. Record what was learned even if the change failed.

## Weekly cohort retention (pandas)

```python
import pandas as pd

def weekly_cohort_retention(events: pd.DataFrame, activity_event: str = "session_started") -> pd.DataFrame:
    """events: columns user_id, event_name, event_ts (datetime64).
    Returns % of each weekly cohort active N weeks after its first active week."""
    active = events.loc[events["event_name"] == activity_event, ["user_id", "event_ts"]].copy()
    ts = active["event_ts"]
    if ts.dt.tz is not None:
        ts = ts.dt.tz_convert("UTC").dt.tz_localize(None)  # pick the reporting zone explicitly
    active["week"] = ts.dt.to_period("W")
    active["cohort"] = active.groupby("user_id")["week"].transform("min")
    active["weeks_since"] = (active["week"] - active["cohort"]).apply(lambda d: d.n)
    counts = active.groupby(["cohort", "weeks_since"])["user_id"].nunique().unstack()
    return counts.divide(counts[0], axis=0).mul(100).round(1)
```

Report cohort size next to each row. A week that has not finished yet is unobserved (NaN), not zero retention; mask immature cells. Compare against mature cohorts of your own product, not published "benchmarks".

## North Star metric

1. What creates real value for the user? (e.g. completed conversations that lead to an action)
2. State it as a hypothesis to validate: users with 3+ such sessions a week get recurring value.
3. Define it precisely: "Weekly Active Conversationalists = users with >= 3 conversations of >= 2 minutes in the week."

Compute it as one aggregate number per closed window, same time zone as the rest of reporting:

```sql
SELECT COUNT(*) AS wac
FROM (
  SELECT user_id
  FROM conversations
  WHERE created_at >= :window_start AND created_at < :window_end
    AND duration_seconds >= 120
  GROUP BY user_id
  HAVING COUNT(*) >= 3
) AS qualifying_users;
```

Check: in a closed window where user A has three 120 s conversations, B has two, and C has four 60 s ones, the result is 1.

## A/B significance check (two proportions)

Before computing anything, record the randomization unit, primary metric, window, minimum detectable effect, stopping rule and guardrails.

```python
from scipy import stats

def ab_test_significance(control_conversions: int, control_visitors: int,
                         variant_conversions: int, variant_visitors: int,
                         alpha: float = 0.05) -> dict:
    counts = (control_conversions, control_visitors, variant_conversions, variant_visitors)
    if any(type(v) is not int or v < 0 for v in counts):
        raise ValueError("counts must be non-negative integers")
    if not (control_visitors > 0 and variant_visitors > 0
            and control_conversions <= control_visitors
            and variant_conversions <= variant_visitors and 0 < alpha < 1):
        raise ValueError("invalid denominators, conversions or alpha")
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    table = [[control_conversions, control_visitors - control_conversions],
             [variant_conversions, variant_visitors - variant_conversions]]
    if any(sum(col) == 0 for col in zip(*table)):
        return {"status": "insufficient-variation"}
    _, p_value, _, expected = stats.chi2_contingency(table)
    if (expected < 5).any():
        return {"status": "sparse-counts", "advice": "use a pre-registered exact test, e.g. scipy.stats.fisher_exact"}
    return {
        "status": "ok",
        "control_rate": round(control_rate, 4),
        "variant_rate": round(variant_rate, 4),
        "absolute_diff_pp": round((variant_rate - control_rate) * 100, 2),
        "relative_lift_pct": round((variant_rate / control_rate - 1) * 100, 1) if control_rate else None,
        "p_value": round(float(p_value), 4),
        "significant": bool(p_value < alpha),
    }

# ab_test_significance(100, 1000, 130, 1000) -> p_value 0.0421, significant True
```

A p-value alone does not measure product value, remove bias, or replace confidence intervals and experiment design. Treat the output as one input to a rollout decision, never as an automatic deploy trigger.
