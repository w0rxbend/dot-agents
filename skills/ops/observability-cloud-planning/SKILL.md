---
name: observability-cloud-planning
description: 'Plan, for a small business without a dedicated ops team, which services to monitor, the few alerts worth waking someone for, their owners and runbooks, SLO targets and the monitoring/cloud budget, as a short recommendation or a CSV/SQL/JSON Schema/Notion register. Use for non-technical SME planning; to instrument code use observability-and-instrumentation, for incident process use managing-incidents.'
category: engineering
risk: safe
source: self
source_type: self
date_added: "2026-09-27"
author: WHOISABHISHEKADHIKARI
tags: [sme, observability, monitoring, slo, sli, alerting, cloud-cost, uptime, incident, reliability, csv, sql, notion]
tools: []
source_repo: WHOISABHISHEKADHIKARI/sme-ops-system-builder
---

# Cloud and Observability Planning

## Overview

Finds smallest monitoring plan that would catch business's worst failure; builds it only
when asked. Default output: short recommendation, not service register. Register (CSV, SQL
DDL, JSON Schema, Notion mapping) only on request, from one field list so the four cannot
drift apart.

**The rule this table exists to enforce:** alert is human cost, so `Alert Channel` and
`Severity` decide whether person is woken at 3am. Other fields make that decision possible:
what service does (`SLI Definition`), what good looks like (`SLO Target`), what is measured
(`Dashboard URL`), what it costs (`Monthly Cost Estimate`), and what happens when alert
fires (`Runbook URL`), the field most tables omit.

**The second rule:** `Phase` keeps this affordable. Phase 1 holds only the few signals
whose failure hurts business most. Rest waits for phase 2 or 3, so ten-service stack does
not become forty alerts on day one. Business with no developer should run managed platform
and three alerts, not collector stack.

## When to Use This Skill

- Small business asks "what should we watch", "how do we know the site is down", or "we found out from a customer"
- Choosing managed hosting, VPS, containers or serverless at SME scale, with cost in view
- Deciding which few alerts reach a person, who owns them, what each costs
- Writing SLO targets and monthly monitoring/cloud budget before buying tools
- Producing service/monitoring register (CSV, SQL DDL, JSON Schema, Notion mapping) on request

Do not use for: writing instrumentation or application code (`observability-and-instrumentation`),
deploying monitoring stack (`implementing-observability`), CI/CD pipelines (`building-ci-pipelines`),
security architecture (`architecting-security`), designing incident-response process or postmortems
(`managing-incidents`), or live outage, which needs action now, not plan.

## How It Works

Never hold or invent real data.

### Step 1 - Identify intent

Read request, pick intent before asking anything.

- "plan" / "set up" / "we need" -> artifacts wanted; go to Step 2.
- "the site is down" / "is it down" / "we are down" -> incident, right now. Confirm
  user-facing failure first and point at runbook. Do not build anything.
- "what does this cost" / "review" / "audit" -> review, not build.
- "should we use" -> decision question. Answer with trade-offs, then offer register.

Ask only if this is highest-value missing fact; otherwise proceed without opener:

> **Q:** What breaks for the business if the site or app is down for one hour, and who
> would notice first - a customer, a member of staff, or an automated system?

### Step 2 - Ask only what is missing

Treat ambiguous replies as unanswered; ask which explicit option user means. Text fields:
record unknown as `Unknown`. Numeric fields (`Monthly Cost Estimate`): leave blank/NULL;
unknown is not zero. Record must not be `Done` when required check fails.

Skip anything already answered. Ask rest one at a time. Stop once remaining answers would
not change plan.

- **Failure** - What is business-critical: website, booking form, till, email, file
  uploads? / Worst realistic failure: down, slow, wrong data, or email that silently stops
  arriving? / How long will customer wait before complaining, and before leaving?
- **Stack** - What runs today: shared hosting, VPS, managed platform, SaaS tool,
  containers? / Who set it up, and is that person still available? / Is there a
  repository, and who can deploy?
- **Traffic** - Roughly how many visitors, orders or jobs a day? / Seasonal or campaign
  peaks that change it by an order of magnitude? / Peak periods where slow is worse than
  down?
- **People** - Anyone who can be on call, and at what hours? / Does someone already use a
  tool the business pays for? / Who may restart something at 3am?
- **Data and money** - What must not be lost, and what is acceptable recovery point? /
  Rough current monthly spend, and budget ceiling? / Does anything process payment,
  personal data, or health data?

Never invent an answer. Traffic numbers, costs, hostnames, provider names, service
identifiers, error rates, uptime figures and recovery times user has not supplied are
`Unknown`.

### Step 3 - Hold the internal context

```yaml
module: observability-cloud-planning
intent: null            # set up | review | report | import
scale: null             # Starter | Growth | Scale, only if the answer changes it
areas:
  "Failure": null
  "Stack": null
  "Traffic": null
  "People": null
  "Data and money": null
requested_outputs: []
confirmed_facts: []
open_questions: []
```

### Step 4 - Recommend the smallest workflow

Build already requested artifact without asking again. Advice-only request: give short
recommendation, offer relevant artifact.

**Recommended approach:** Start with the one thing whose failure stops business earning,
usually checkout or booking form. Watch exactly that from outside infrastructure, so check
does not fail with what it checks. Three signals, no more: reachable, answering within
target time, money or data transaction succeeding. One alert channel reaching a human,
runbook per alert, named owner. Everything else (traces, log aggregation, five custom
dashboards, status page) waits for later phase, once first phase proves someone reads it.

**Workflow:** Worst failure named → What must be measured to catch it, from outside →
Baseline measured, not assumed → Three signals defined with targets → Alerts with a channel
and a runbook each → Costs estimated against a ceiling → Owner and review date set →
Runbook rehearsed → Phase 2 only after phase 1 is being read → Quarterly review of alerts
kept, deleted and added

### Step 5 - Build only on request

Once user asks, derive fields from confirmed context and emit requested artifacts.
Machine-readable text: keep prose outside data. Files: provide usable link. Report
material validation failures or limitations separately.

**Notion output.** When user selects Notion, deliver CSV with Field Reference columns,
property-mapping table (column to Notion property type, from Select Options below) and
short manual import steps: import CSV, then change each property type per mapping. Manual
CSV and mapping outputs need no connection. Write to workspace only through verified
MCP/tool connection, after confirming target. User saying "connected" is not tool
evidence. Never ask for Notion password or token.

```csv
Service ID,Service Name,Purpose,Criticality,Owner,Environment,Monitored From,SLI Definition,SLO Target,Dashboard URL,Log Source,Alert Channel,Severity,Alert Threshold,Runbook URL,Escalation Path,Monthly Cost Estimate,Data Handled,Deployment Method,Dependencies,Phase,Review Date,Status,Notes
,Example Booking Service,Takes customer bookings and confirms by email,High,Example Owner,Production,External region outside the hosting provider,Uptime of the public booking page,99.5% monthly,Not yet created,Application and web server logs,Email and SMS to on-call,Critical,3 consecutive failed checks or 5 minutes above target,Not yet created,On-call then business owner,"",Payment card details,Managed platform,None,1 - core,2026-10-27,Not started,Example row - replace every value before use.
```

```sql
-- Engine assumption: PostgreSQL 10+. For another engine use the engine's auto-increment
-- equivalent and keep the rest portable. Import the CSV with a column list that omits
-- service_id (the CSV leaves it blank) and treat blank cost as NULL (unknown), e.g.
-- \copy obs_service (service_name, ..., notes) FROM 'plan.csv' CSV HEADER
CREATE TABLE obs_service (
  service_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  service_name VARCHAR(100) NOT NULL,
  purpose TEXT NOT NULL,
  criticality VARCHAR(50) NOT NULL,
  owner VARCHAR(255) NOT NULL,
  environment VARCHAR(50) NOT NULL,
  monitored_from VARCHAR(100) NOT NULL,
  sli_definition TEXT NOT NULL,
  slo_target VARCHAR(50) NOT NULL,
  dashboard_url VARCHAR(255),
  log_source VARCHAR(255) NOT NULL,
  alert_channel VARCHAR(255) NOT NULL,
  severity VARCHAR(50) NOT NULL,
  alert_threshold VARCHAR(255) NOT NULL,
  runbook_url VARCHAR(255),
  escalation_path TEXT,
  monthly_cost_estimate NUMERIC(10,2),
  data_handled VARCHAR(255) NOT NULL,
  deployment_method VARCHAR(100) NOT NULL,
  dependencies TEXT,
  phase VARCHAR(50) NOT NULL,
  review_date DATE,
  status VARCHAR(50) NOT NULL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT obs_service_phase CHECK (phase IN ('1 - core','2 - deepen','3 - optional','Sunset')),
  CONSTRAINT obs_service_status CHECK (status IN ('Not started','In progress','Blocked','Done','Cancelled')),
  CONSTRAINT obs_service_severity CHECK (severity IN ('Info','Warning','Critical')),
  CONSTRAINT obs_service_criticality CHECK (criticality IN ('Low','Medium','High','Critical')),
  CONSTRAINT obs_service_cost_non_negative CHECK (monthly_cost_estimate IS NULL OR monthly_cost_estimate >= 0)
);

CREATE INDEX idx_obs_service_status ON obs_service (status);
CREATE INDEX idx_obs_service_phase ON obs_service (phase);
CREATE INDEX idx_obs_service_review ON obs_service (review_date);
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Cloud and Observability Plan",
  "type": "object",
  "additionalProperties": false,
  "properties": {
      "Service ID": { "type": "integer" },
      "Service Name": { "type": "string" },
      "Purpose": { "type": "string" },
      "Criticality": { "type": "string" },
      "Owner": { "type": "string" },
      "Environment": { "type": "string" },
      "Monitored From": { "type": "string" },
      "SLI Definition": { "type": "string" },
      "SLO Target": { "type": "string" },
      "Dashboard URL": { "type": "string" },
      "Log Source": { "type": "string" },
      "Alert Channel": { "type": "string" },
      "Severity": { "type": "string" },
      "Alert Threshold": { "type": "string" },
      "Runbook URL": { "type": "string" },
      "Escalation Path": { "type": "string" },
      "Monthly Cost Estimate": { "type": ["number", "null"], "description": "null or omitted when unknown" },
      "Data Handled": { "type": "string" },
      "Deployment Method": { "type": "string" },
      "Dependencies": { "type": "string" },
      "Phase": { "type": "string" },
      "Review Date": { "type": "string", "format": "date" },
      "Status": { "type": "string" },
      "Notes": { "type": "string" }
  },
  "required": [
      "Service Name",
      "Purpose",
      "Criticality",
      "Owner",
      "Environment",
      "Monitored From",
      "SLI Definition",
      "SLO Target",
      "Log Source",
      "Alert Channel",
      "Severity",
      "Alert Threshold",
      "Data Handled",
      "Deployment Method",
      "Phase",
      "Status"
  ]
}
```

```markdown
| CSV column | Notion property | Set after import |
|---|---|---|
| Service ID | Text (preserve source ID) | Keep imported IDs as Text; optionally add a separate Unique ID property |
| Service Name | Title | Use as the database title |
| Purpose | Text | Leave as Text. What the business loses if this stops. Not a technical description |
| Criticality | Select (add options after import) | Convert to Select, add options: "Low", "Medium", "High", "Critical". Critical means the business stops earning |
| Owner | Text | Leave as Text. A named person. A service with no owner is unmonitored in practice |
| Environment | Select (add options after import) | Convert to Select, add options: "Production", "Staging", "Development". Monitoring a staging URL and calling it uptime is a common and expensive mistake |
| Monitored From | Text | Leave as Text. Where the check runs. It must not run on the thing it is checking |
| SLI Definition | Text | Leave as Text. The measurement in plain words - "public booking page answers in under 2 seconds for 95% of requests" |
| SLO Target | Text | Leave as Text. The number and the window, e.g. "99.5% monthly". A target nobody has ever met is a target that gets deleted |
| Dashboard URL | Text | Leave as Text. Blank until a dashboard exists, which is the correct state in phase 1 |
| Log Source | Text | Leave as Text. Where the logs are today, including "none - not collected" |
| Alert Channel | Text | Leave as Text. The specific route: which email, which SMS, which app. "Alerts" is not a channel |
| Severity | Select (add options after import) | Convert to Select, add options: "Info", "Warning", "Critical". Only Critical should page a human outside working hours |
| Alert Threshold | Text | Leave as Text. The condition that fires, written so it is unambiguous and testable |
| Runbook URL | Text | Leave as Text. Blank is a finding, not a formatting gap. An alert with no runbook must not ship |
| Escalation Path | Text | Leave as Text. Who is woken first, then who, then who gives up and calls the host |
| Monthly Cost Estimate | Number | Convert to Number, two decimal places. Leave blank when unknown (never the word "Unknown"). An estimate against a ceiling, in the business's own currency |
| Data Handled | Select (add options after import) | Convert to Select, add options: "None", "Personal data", "Payment card details", "Health data", "Credentials or secrets", "Business confidential", "Public only". Drives the log retention and access rules |
| Deployment Method | Text | Leave as Text. How a change reaches this service, and by whom |
| Dependencies | Text | Leave as Text. What this needs to work. "None" is a valid and worth recording answer |
| Phase | Select (add options after import) | Convert to Select, add options: "1 - core", "2 - deepen", "3 - optional", "Sunset". The affordability control |
| Review Date | Date | Convert to Date. When the alerts, the target and the cost are re-examined |
| Status | Select (add options after import) | Convert to Select, add options: "Not started", "In progress", "Blocked", "Done", "Cancelled" |
| Notes | Text | Leave as Text |
```

Rows above are documentation examples only. Emit empty templates unless user explicitly
requests examples. `Dashboard URL` and `Runbook URL` read `Not yet created`, not
plausible-looking link: dead or wrong runbook link is worse than obvious gap.

## Field Reference

| # | Field | Type | SQL | JSON Schema | Notion | CSV example |
|---:|---|---|---|---|---|---|
| 1 | Service ID | `id` | `BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` | `integer` | Text or Notion auto-ID | (blank) |
| 2 | Service Name | `text` | `VARCHAR(100)` | `string` | Text | *(blank)* |
| 3 | Purpose | `long_text` | `TEXT` | `string` | Text | *(blank)* |
| 4 | Criticality | `select` | `VARCHAR(50)` | `string` | Select | High |
| 5 | Owner | `text` | `VARCHAR(255)` | `string` | Text | *(blank)* |
| 6 | Environment | `select` | `VARCHAR(50)` | `string` | Select | Production |
| 7 | Monitored From | `text` | `VARCHAR(100)` | `string` | Text | *(blank)* |
| 8 | SLI Definition | `long_text` | `TEXT` | `string` | Text | *(blank)* |
| 9 | SLO Target | `text` | `VARCHAR(50)` | `string` | Text | 99.5% monthly |
| 10 | Dashboard URL | `text` | `VARCHAR(255)` | `string` | Text | *(blank)* |
| 11 | Log Source | `text` | `VARCHAR(255)` | `string` | Text | *(blank)* |
| 12 | Alert Channel | `text` | `VARCHAR(255)` | `string` | Text | *(blank)* |
| 13 | Severity | `select` | `VARCHAR(50)` | `string` | Select | Critical |
| 14 | Alert Threshold | `text` | `VARCHAR(255)` | `string` | Text | *(blank)* |
| 15 | Runbook URL | `text` | `VARCHAR(255)` | `string` | Text | *(blank)* |
| 16 | Escalation Path | `long_text` | `TEXT` | `string` | Text | *(blank)* |
| 17 | Monthly Cost Estimate | `number` | `NUMERIC(10,2)` | `number` (null when unknown) | Number | *(blank = unknown)* |
| 18 | Data Handled | `select` | `VARCHAR(255)` | `string` | Select | Personal data |
| 19 | Deployment Method | `text` | `VARCHAR(100)` | `string` | Text | *(blank)* |
| 20 | Dependencies | `long_text` | `TEXT` | `string` | Text | None |
| 21 | Phase | `select` | `VARCHAR(50)` | `string` | Select | 1 - core |
| 22 | Review Date | `date` | `DATE` | `string, format: date` | Date | *(blank)* |
| 23 | Status | `select` | `VARCHAR(50)` | `string` | Select | Not started |
| 24 | Notes | `long_text` | `TEXT` | `string` | Text | *(blank)* |

## Select Options

**Criticality** - what business loses. `Critical` means business stops earning, not that
service is technically important. Search index down: `Low`. Checkout down: `Critical`.

```
Low | Medium | High | Critical
```

**Environment** - prevents monitoring staging URL and reporting it as uptime. Only
Production earns an alert.

```
Production | Staging | Development
```

**Severity** - notification versus woken person. Only `Critical` should reach human outside
working hours: `Warning` paging at 3am trains on-call to ignore channel.

```
Info | Warning | Critical
```

**Data Handled** - instruction, not documentation. `Payment card details`, `Health data`
and `Credentials or secrets` change log retention period, who may read logs, and whether
logs may go to third-party service at all.

```
None | Personal data | Payment card details | Health data | Credentials or secrets | Business confidential | Public only
```

**Phase** - Phase 1 catches worst failure and is read. Nothing enters phase 2 until phase 1
is read and acted on. Plan shipping all phases at once is plan nobody maintains.

```
1 - core | 2 - deepen | 3 - optional | Sunset
```

**Status** - `Blocked` is honest value whenever something waits on person, contract or
decision not yet made.

```
Not started | In progress | Blocked | Done | Cancelled
```

## Relations

- `Dependencies` names other rows in this table. Cycle is design smell, not error; find it
  deliberately.
- `Log Source` and `Data Handled` should match business's own data-privacy and retention
  rules. Confirm before making join live. Third-party log destination is data transfer.
- `Runbook URL` points at that alert's runbook document.

## Examples

**Prompt**

```
We run a booking site on a VPS. Last month it was down for a whole Sunday and we only
found out on Monday from a customer. We want to know if it goes down, and we do not know
what we should be paying for all this.
```

**Context first** - one question per message, nothing already answered:

> **Q:** What breaks for the business if the site or app is down for one hour, and who
> would notice first - a customer, a member of staff, or an automated system?
> **A:** The booking form. A customer, obviously.
>
> **Q:** What is actually running today, and who set it up?
> **A:** A VPS with the site on it, set up by an agency we no longer deal with.
>
> **Q:** Roughly how many visitors or bookings a day?
> **A:** Maybe 20 bookings. It is much busier in December.
>
> **Q:** Is there anyone who could be on call, and at what hours?
> **A:** Me, evenings and weekends.
>
> **Q:** What is the current monthly spend, roughly, and the ceiling?
> **A:** Forty a month for the server. I would not want to spend much more than that.

**Recommended next step** - offered, not built:

> One external uptime check on the booking page, run from outside your provider, plus a
> check that a test booking actually completes. That catches the Sunday problem. Two
> alerts, both to your phone: the page unreachable for three checks running, and a test
> booking that fails. No dashboard, no log shipping, no tracing - the site does not earn
> that yet. A one-page runbook for each: what to check, how to restart it, and the agency
> number if it does not come back. December is your peak, so test it properly in November.
> Keep it near 40 a month, or you will pay more for storage than you do for the server.
>
> Workflow: Worst failure named → What must be measured, from outside → Baseline measured
> → Three signals with targets → Alerts with a channel and a runbook each → Costs
> estimated → Owner and review date set → Runbook rehearsed → Phase 2 only if phase 1 is
> being read
>
> Want the CSV, SQL DDL, JSON Schema and Notion mapping for this?

## Best Practices

- One question per message. Batched intake reads as form and gets guessed at.
- Monitor transaction, not server. Server can return 200 while checkout throws exception on
  every attempt; no CPU monitoring catches that.
- Measure baseline before setting target. SLO above anything system has ever done
  guarantees permanently firing alert.
- No alert without runbook. Blank `Runbook URL` is finding that blocks going live.
- Set alert threshold in advance and test it. Alert that never fired is untested
  assumption.
- Track cost against ceiling business named. Plan with no ceiling becomes invoice nobody
  predicted.
- Name owner per service. Unowned service is unmonitored in practice, whatever dashboards
  say.
- Set review date and honour it. Quarterly, ask of each alert: did a human act on this? If
  not, delete it.
- Never log secrets, tokens, full card numbers, or unnecessary personal data. `Data Handled`
  makes that decision explicit before logs ship anywhere.
- Logs sent to third-party service are data transfer with own agreement. Confirm it; do not
  assume it is fine.
- Derive all four artifacts from field list in this file, never by hand.
- If user requests example row, keep it obviously fake so nobody imports it as real service.

## Limitations

- Plan only. Does not deploy anything, install agent, open dashboard, create alert or read
  log.
- No access to business infrastructure: cannot measure baseline, read metric, or verify
  SLO. Every value here comes from user.
- Costs are estimates. They depend on region, tier, retention and traffic this skill cannot
  see. Treat `Monthly Cost Estimate` as planning figure, never as quote or provider price
  list.
- No specific provider recommendation on current price. Provider capabilities, pricing and
  free tiers change; verify against provider's own current documentation.
- Log volume, cardinality and ingestion cost usually cause unexpected bills. Cannot
  estimate them without real traffic.
- Cannot tell what runs now, what alerts now, or whether current setup already covers worst
  failure. That needs access.
- Uptime, latency and error-rate targets are engineering commitments, not business
  promises. Missed target triggers decision, not contractual breach.
- SLOs do not replace backup, restore test, or disaster recovery plan. Monitored service
  without tested restore is still lost database.
- Logging, retention and personal-data compliance is jurisdiction- and sector-specific; not
  modelled here.
- Security monitoring, intrusion detection and access review out of scope; use
  `architecting-security` or `security-hardening`.
- Cannot judge whether provider, region or architecture is right. Structures the question.


See [Security & Safety Notes](references/security-safety-notes.md) for full guidance.
