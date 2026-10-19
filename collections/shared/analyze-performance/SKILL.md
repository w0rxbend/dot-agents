---
name: analyze-performance
description: Pull Sentry performance data (via a Sentry MCP server, or the Sentry UI/API as fallback) to rank slow transactions by p95/p99 and impact, spot release regressions, and drill into slow spans. Use when the app already sends traces to Sentry and you need to know what is slow; to fix a bottleneck use performance-optimization, for load testing use performance-engineering.
---

# Analyze Performance in Sentry

Turn Sentry tracing data into a short, evidence-backed list of the slowest, most impactful transactions and the spans responsible.

## Inputs

- Sentry organization and project slug(s), environment (usually `production`).
- Time window (e.g. `24h`, `7d`) and, if investigating a regression, the suspect release and the previous release.
- Optional: a specific transaction (route/job name) to focus on.

Ask only for what is missing; default to the last 7 days of `production`.

## Access paths

1. **Sentry MCP server (preferred).** List the server's tools first and use the ones that search events/spans/traces and fetch issue or trace details; tool names and parameters differ between server versions, so read their schemas instead of guessing. Authentication is handled by the server (often OAuth).
2. **No MCP available.** Use the Sentry web UI (Insights / Performance views for transactions, Trace view for spans) and ask the user to paste or export the numbers, or query Sentry's organization events API with a user-provided auth token. Check the API documentation for the installed/hosted Sentry version before building queries. Never ask the user to paste a token into chat history that will be shared; prefer an environment variable they set.

If neither is possible, stop and say what access is needed. Do not invent numbers.

## Procedure

1. **Confirm data quality.** Check that tracing is enabled, note the trace sample rate, and whether the window has enough transactions to be meaningful. Sampled counts are not request totals; throughput figures from sampled data must be labeled as estimates unless Sentry extrapolates them.
2. **Rank transactions by impact, not just latency.** For each transaction collect count/throughput, p50, p95, p99 and failure rate. Rank by p95 × volume (time users spend waiting) and flag low-volume outliers separately.
3. **Compare releases.** For regressions, compare the same transaction's p95/p99 between the suspect release and its predecessor over comparable windows (same weekday/hour pattern). A change that coincides with a deploy is a hypothesis until the spans show what changed.
4. **Drill into spans.** Open representative slow traces (near p95, not only the single worst). Identify the dominant span types: DB queries, HTTP calls to other services, cache, rendering, queue waits. Look for repeated identical DB spans in one trace (N+1), long gaps without spans (uninstrumented work), and serial calls that could be parallel.
5. **Check the database spans properly.** Report the normalized query, its count per transaction and its duration. Do not recommend an index without knowing the predicate: e.g. `WHERE email LIKE '%@%'` (leading wildcard) cannot use a plain btree index on `email`; that needs a different query, a trigram/full-text index, or a different data model.
6. **Separate what you control.** Latency from third-party APIs goes under "dependency": recommend timeouts, caching, async handling or provider follow-up, not code micro-tuning.
7. **Write the report** (format below) and offer next steps: deeper analysis of one transaction, or handing a specific bottleneck to `performance-optimization`.

## Report format

```markdown
## Performance analysis: <project>, <environment>, <window>
Data: <N> sampled transactions, sample rate <x>; caveats: <...>

### Top transactions by impact
| Transaction | Volume | p50 | p95 | p99 | Failure rate | Dominant span |
|---|---|---|---|---|---|---|

### Regressions
- <transaction>: p95 <before> → <after> between <release A> and <release B>; evidence: <span/trace link>

### Findings
1. <finding>: evidence (trace IDs/links), likely cause, confidence (verified / hypothesis)

### Recommendations
1. <action>: expected effect, how to verify (metric + window)
```

Every number in the report must come from Sentry output you actually retrieved, with its window. Mark hypotheses as such.

## Tips

- Prefer p95/p99 over averages; averages hide tail latency.
- Watch for changes right after releases, and compare across environments only when traffic shapes are similar.
- Set a Sentry alert on p95 or failure rate for the transactions you fixed, so the regression is caught next time.
