# Incident Response Workflow

## Table of Contents

- [Stage Details](#stage-details)
  - [1. Detection](#1-detection)
  - [2. Triage & Severity Assignment](#2-triage-severity-assignment)
  - [3. Incident Declaration](#3-incident-declaration)
  - [4. Investigation & Diagnosis](#4-investigation-diagnosis)
  - [5. Mitigation](#5-mitigation)
  - [6. Resolution](#6-resolution)
  - [7. Monitoring](#7-monitoring)
  - [8. Closure](#8-closure)
  - [9. Post-Mortem](#9-post-mortem)
- [Decision Points](#decision-points)
  - [When to Declare Incident](#when-to-declare-incident)
  - [When to Escalate](#when-to-escalate)
  - [When to Close](#when-to-close)
- [Workflow Variations](#workflow-variations)
  - [SEV0 Workflow (All Hands)](#sev0-workflow-all-hands)
  - [SEV2 Workflow (Single Responder)](#sev2-workflow-single-responder)
  - [SEV3 Workflow (Ticket)](#sev3-workflow-ticket)
- [Communication During Workflow](#communication-during-workflow)
  - [Status Update Frequency](#status-update-frequency)
  - [Update Template](#update-template)
  - [External Communication](#external-communication)
- [Workflow Anti-Patterns](#workflow-anti-patterns)
- [Further Reading](#further-reading)

## Stage Details

### 1. Detection

**Sources:**
- Automated alerts (Prometheus, Datadog, CloudWatch)
- Customer reports (support tickets, social media)
- Synthetic monitoring (uptime checks)
- Internal discovery (engineer notices issue)

**Actions:**
- Alert fires to on-call via PagerDuty/Opsgenie
- On-call acknowledges within 5 minutes (MTTA target)

### 2. Triage & Severity Assignment

**On-Call Assesses:**
- What is broken?
- How many customers affected?
- Core functionality impacted?
- Workaround exists?

**Assign Severity:** SEV0, SEV1, SEV2, or SEV3 (use `python scripts/classify-severity.py`)

### 3. Incident Declaration

**For SEV1/SEV0:**
- Create incident Slack channel: `#incident-YYYY-MM-DD-topic`
- Assign Incident Commander (IC)
- Post initial status: Severity, IC, brief description
- Update status page: "Investigating"

**Slack Command:**
```
/incident-declare SEV1 API experiencing elevated error rates
```

### 4. Investigation & Diagnosis

**IC Coordinates:**
- SMEs investigate logs, metrics, recent changes
- Consult runbooks if known failure scenario
- Form root-cause hypothesis

**Key Questions:**
- When did this start?
- What changed recently (deploys, config, traffic)?
- Which systems affected?

**IC Decision:** Enough info to mitigate? If yes, go to Mitigation. If no, continue investigation.

### 5. Mitigation

**Goal:** Stop customer impact ASAP (not fix root cause).

**Common Mitigations:**
- Rollback recent deploy
- Disable feature flag
- Failover to secondary database
- Scale up infrastructure
- Rate limit traffic
- Enable maintenance mode

**IC Announces:** "Mitigation deployed: [action]. Monitoring for impact reduction."

### 6. Resolution

**Goal:** Fix root cause permanently.

**Actions:**
- Deploy permanent fix (if mitigation was temporary)
- Verify fix resolves issue
- Test affected functionality

**Example:** Mitigation was rollback. Resolution is fixing bug and deploying fixed version.

### 7. Monitoring

**Duration:** 30+ minutes of stability before closure.

**Monitor:**
- Error rates back to baseline
- Latency normal
- No new customer reports
- All metrics green

**IC Decision:** If stable, proceed to Closure. If unstable, return to Investigation.

### 8. Closure

**IC Declares Resolved:**
- Post in incident channel: "Incident resolved at [timestamp]"
- Update status page: "Resolved"
- Thank responders
- Schedule post-mortem (within 48 hours)

### 9. Post-Mortem

**Timeline:** Within 48 hours of resolution.

**Process:**
- IC schedules post-mortem meeting
- Scribe creates post-mortem document (use `examples/postmortem-template.md`)
- Team runs blameless review
- Define action items with owners and due dates

For facilitation detail, see blameless post-mortems guide.

## Decision Points

### When to Declare Incident

**Declare if:**
- Customer-facing impact occurring
- Production issue needs multiple people
- Severity SEV1 or higher
- Impact uncertain (declare; can always downgrade)

**Do NOT wait for certainty.** Declaring enables coordination.

### When to Escalate

**Escalate if:**
- No progress after 30 minutes
- Severity increases (SEV2 → SEV1)
- Specialized expertise needed (database, security)
- Incident runs past expected timeframe

See escalation matrix for escalation paths and contacts.

### When to Close

**Close when:**
- Issue resolved and stable for 30+ minutes
- Monitoring shows baseline metrics
- No customer-reported issues
- IC confident in stability and confirms no further action needed

**Do NOT close prematurely.** Closing too early risks recurrence.

## Workflow Variations

### SEV0 Workflow (All Hands)

1. Detection: immediate page to all hands
2. Declare SEV0: assign IC, Communications Lead, Scribe
3. War room: video call for real-time coordination
4. Executive notification: within 15 minutes
5. Status updates: every 15 minutes
6. Post-mortem: within 24 hours (faster than normal)

### SEV2 Workflow (Single Responder)

1. Detection: alert to on-call
2. Single responder investigates; no IC needed
3. Fix applied: standard response
4. Update status page if customer-visible
5. Post-mortem optional (recommended if novel issue)

### SEV3 Workflow (Ticket)

1. Detection: create ticket, no alert
2. Triage: assign to backlog
3. Plan fix: next sprint
4. No post-mortem: track in regular sprint retrospective

## Communication During Workflow

### Status Update Frequency

- **SEV0:** Every 15 minutes
- **SEV1:** Every 30 minutes
- **SEV2:** At major milestones

### Update Template

```
[TIMESTAMP] Update #[N] - [Status]

Current Status: [Investigating | Identified | Implementing Fix | Monitoring]
Issue: [One-sentence description]
Impact: [Who/what affected]
Progress: [What we've learned/done]
Next Steps: [What we're doing next]
ETA: [Expected resolution or "Unknown"]
Next Update: [TIMESTAMP]
```

### External Communication

- Status page: Investigating → Identified → Monitoring → Resolved
- Customer email: post-resolution (within 24 hours for SEV0/SEV1)

## Workflow Anti-Patterns

**IC Doing Hands-On Debugging:**
- IC loses strategic view
- Fix: IC delegates all debugging to SMEs

**No Status Updates:**
- Stakeholders uninformed, anxiety rises
- Fix: set timer for regular updates

## Further Reading

- Google SRE Book: "Managing Incidents" (Chapter 14)
- PagerDuty: "Incident Response Process"
- Atlassian: "Incident Management Best Practices"
