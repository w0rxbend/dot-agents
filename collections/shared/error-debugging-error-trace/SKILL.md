---
name: error-debugging-error-trace
description: "Set up or tune an error tracker (Sentry-style capture, release tagging, grouping/fingerprints, severity, alert routing, sampling, PII scrubbing). Use when exceptions are not being captured, issues are mis-grouped, or error alerts are noisy; to debug one specific bug use debugging-and-error-recovery."
risk: safe
source: community
date_added: "2026-02-27"
---

# Error Tracking Setup

Make every unhandled and meaningful handled error reach an error tracker (Sentry, Rollbar, Bugsnag, Honeybadger, Datadog Error Tracking, or an OTel-based backend) with enough context to act on, grouped correctly, routed to an owner, and free of secrets.

**Not this skill:** root-causing one bug (`debugging-and-error-recovery`), general logs/metrics/traces for a feature (`observability-and-instrumentation`), incident process (`managing-incidents`).

## Inputs to pin first

- Tracker and **installed SDK major version** (APIs change between majors; read that version's docs).
- Runtimes and frameworks in scope (backend, browser, mobile, workers/cron).
- Environments (`production`, `staging`, …) and how a release/revision string is produced in CI.
- Owners: team or on-call per service/component, and the channels they actually watch.
- Data policy: which fields may leave the process, retention, region.

## Procedure

1. **Assess current capture.** Find where errors are swallowed: empty `catch`, `catch → log → continue`, promise rejections without handlers, worker/cron entry points, framework error middleware ordering. Check whether the tracker already exists and which SDK version is installed.
2. **Initialize correctly.** Initialize the SDK as early as the runtime requires (many Node SDKs must load before other imports to auto-instrument), once per process. Set `environment` and `release` from CI; never hard-code. Ensure flush on shutdown for short-lived processes (CLIs, serverless, jobs).
3. **Capture the gaps.** Register framework error handlers and global handlers (uncaught exceptions, unhandled rejections, browser `window.onerror`). For deliberately handled errors that still matter, capture explicitly with tags, not by re-throwing.
4. **Attach context, not payloads.** Add bounded tags (service, route template, job name, tenant tier, feature flag) and a correlation/trace ID. Do not attach request bodies, tokens, cookies or full user records.
5. **Upload source maps / debug symbols** for the same `release` string, so stack traces resolve. Verify one resolved frame.
6. **Tune grouping** (checklist below).
7. **Define severity and routing** (checklist below), then alert rules.
8. **Set sampling** (checklist below).
9. **Validate with a synthetic error** in each environment and runtime: it arrives once, with the right release/environment, resolved stack, expected tags, no private data, grouped into the intended issue, and the alert reaches the right channel.

## Checklists

### Grouping and deduplication
- [ ] Default stack-trace grouping reviewed on the top 20 issues; look for one bug split into many issues or many bugs merged into one.
- [ ] Dynamic values (IDs, timestamps, URLs with IDs) are not in exception messages used for grouping, or a custom fingerprint normalizes them.
- [ ] Custom fingerprints are applied only to known cases (e.g. all upstream `502` from one provider → one issue per provider + route).
- [ ] Wrapper/re-throw layers don't hide the original cause; chained causes are preserved.
- [ ] Expected, non-actionable errors (client aborts, 4xx validation, bot noise) are filtered or downgraded at the SDK, not ignored by humans.

### Severity
| Level | Meaning | Default routing |
|---|---|---|
| fatal / critical | Process crash, data loss risk, payments/auth broken | Page on-call |
| error | Request or job failed for a user | Ticket/channel for owning team |
| warning | Degraded but handled (fallback, retry succeeded) | Dashboard only; trend review |
| info | Expected domain failure | Usually not sent to the tracker |

Base severity on user impact, not on the exception class alone.

### Alert routing
- [ ] Every alert has an owner (team/service ownership rules or code-owner mapping), not a shared catch-all inbox.
- [ ] Alert on **new issue in production**, **regression of a resolved issue**, and **frequency/user-count spikes**; not on every event.
- [ ] Thresholds use rates or affected-user counts over a window, with a rationale; "5% error rate" means 0.05, not 0.05%.
- [ ] Paging alerts link to a runbook and are test-fired once.
- [ ] Release health (crash-free sessions/users) is watched after each deploy where the tracker supports it.

### Sampling and volume
- [ ] Error events: keep 100% unless volume or quota forces sampling; if sampling, sample per issue/fingerprint or rate-limit noisy issues instead of dropping uniformly.
- [ ] Performance traces/profiles: sampled separately (e.g. a low base rate with higher rates for critical routes).
- [ ] Quotas and spike protection configured so one runaway loop can't exhaust the monthly budget.
- [ ] `beforeSend`-style hooks never throw; a failing hook must not drop all events.

### Privacy
- [ ] Default PII sending is off unless the data policy allows it.
- [ ] Server-side scrubbing rules plus SDK-side scrubbing for known sensitive keys; spot-check real received events, not just config.
- [ ] Breadcrumbs/console capture reviewed for secrets.

## Output format

Report the work in these sections (skip any that don't apply):

1. **Error tracking analysis**: current capture, gaps found (file:line), SDK/version.
2. **Integration configuration**: init code/config per runtime, release and environment wiring.
3. **Logging implementation**: how logs correlate with tracker events (trace/correlation ID).
4. **Alert rules**: each rule, threshold rationale, owner, channel, runbook link.
5. **Error grouping**: fingerprint rules and filters added, with the issues they affect.
6. **Recovery strategies**: retries/fallbacks added or reviewed (only with clear failure predicates and idempotency for writes).
7. **Dashboard setup**: release health / error-rate views, if requested.
8. **Documentation**: how to verify, how to add a new service, known untested paths.

## Done when

- A synthetic error from every runtime in scope appears once, correctly grouped, with resolved stack, release and environment, and no private data.
- Every alert rule has an owner and has been test-fired.
- Known noisy issues are filtered or fingerprinted, and the change is visible on the issue list.

## Reference

`resources/implementation-playbook.md` holds long code samples (codebase error-handling analyzer, Sentry/structured-logging/alert-manager/grouping/recovery/dashboard examples). Read it only when you need a starting template, and check each API against the installed SDK version (the Sentry Node.js sample targets `@sentry/node` v8+).
