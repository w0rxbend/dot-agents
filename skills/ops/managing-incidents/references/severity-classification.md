# Severity Classification Guide


## Table of Contents

- [Severity Levels](#severity-levels)
  - [SEV0 (P0) - Critical Outage](#sev0-p0-critical-outage)
  - [SEV1 (P1) - Major Degradation](#sev1-p1-major-degradation)
  - [SEV2 (P2) - Minor Issues](#sev2-p2-minor-issues)
  - [SEV3 (P3) - Low Impact](#sev3-p3-low-impact)
- [Impact vs. Urgency Matrix](#impact-vs-urgency-matrix)
- [Decision Tree](#decision-tree)
- [Special Considerations](#special-considerations)
  - [Security Incidents](#security-incidents)
  - [Compliance and Regulatory](#compliance-and-regulatory)
  - [Time-Based Severity Escalation](#time-based-severity-escalation)
- [Common Misclassifications](#common-misclassifications)
  - [Over-Severity (Too High)](#over-severity-too-high)
  - [Under-Severity (Too Low)](#under-severity-too-low)
- [Severity Reclassification](#severity-reclassification)
  - [Escalation Triggers](#escalation-triggers)
  - [De-escalation Triggers](#de-escalation-triggers)
- [Metrics and Tracking](#metrics-and-tracking)
  - [Severity Distribution](#severity-distribution)
  - [Severity Duration](#severity-duration)
  - [Reclassification Rate](#reclassification-rate)
- [Example Scenarios with Classification](#example-scenarios-with-classification)
  - [Scenario 1: Database Slow Queries](#scenario-1-database-slow-queries)
  - [Scenario 2: Login Button Color Wrong](#scenario-2-login-button-color-wrong)
  - [Scenario 3: Payment API 100% Errors](#scenario-3-payment-api-100-errors)
  - [Scenario 4: Search Returns Stale Results](#scenario-4-search-returns-stale-results)
- [Interactive Severity Classifier](#interactive-severity-classifier)
- [Customization for Your Organization](#customization-for-your-organization)
- [Further Reading](#further-reading)

## Severity Levels

### SEV0 (P0) - Critical Outage

**Definition:** Complete outage, critical data loss, or security breach with immediate risk.

**Impact Criteria:**
- All customers unable to use core functionality
- API or web app completely unavailable
- Critical data loss or corruption
- Payment processing completely broken
- Security breach with active data exfiltration
- Legal/regulatory violation in progress

**Response Requirements:**
- **Alert:** Page all hands immediately, 24/7
- **Escalation:** Notify executives (CTO, CEO)
- **IC Assignment:** Senior engineer or team lead
- **Communication:** Status updates every 15 minutes
- **External:** Immediate status page update, customer notification
- **Post-Mortem:** Mandatory within 24 hours

**Response Time Target:**
- Acknowledgment: < 2 minutes
- Mitigation: < 30 minutes
- Resolution: < 2 hours

**Examples:**
- Database primary down, no automatic failover
- Complete AWS region outage hitting production
- Ransomware encrypting production systems
- Payment API returning 100% errors
- Customer PII exposed publicly
- DDoS overwhelming all infrastructure

---

### SEV1 (P1) - Major Degradation

**Definition:** Major functionality degraded, significant customer impact, service partly up.

**Impact Criteria:**
- 10-50% of customers unable to use core features
- Elevated error rates (5-25% failure)
- Major slowdown (10x slower)
- Critical feature unavailable (authentication, checkout)
- Major third-party integration failure
- Data sync delays causing business impact

**Response Requirements:**
- **Alert:** Page on-call in business hours, escalate off-hours
- **Escalation:** Notify team lead, assign IC
- **IC Assignment:** Senior on-call engineer
- **Communication:** Status updates every 30 minutes
- **External:** Status page update within 30 minutes
- **Post-Mortem:** Mandatory within 48 hours

**Response Time Target:**
- Acknowledgment: < 5 minutes
- Mitigation: < 1 hour
- Resolution: < 4 hours

**Examples:**
- API error rate at 15%, checkout partially working
- Database replica lag causing stale data
- Search completely broken
- Email delivery delayed by hours
- Mobile app crashing on startup for iOS users
- Cache failure causing severe slowdown

---

### SEV2 (P2) - Minor Issues

**Definition:** Minor functionality impaired, small subset of customers affected, workaround available.

**Impact Criteria:**
- < 10% of customers impacted
- Edge-case bug in specific scenarios
- Non-critical feature unavailable
- Minor slowdown (2x slower)
- Cosmetic issues with functional impact
- Internal tool degradation (not customer-facing)

**Response Requirements:**
- **Alert:** Email/Slack notification to on-call
- **Escalation:** Standard on-call response, no immediate escalation
- **IC Assignment:** Optional (single responder enough)
- **Communication:** Status updates at major milestones
- **External:** Status page update if customer-visible
- **Post-Mortem:** Optional (recommended for novel issues)

**Response Time Target:**
- Acknowledgment: < 15 minutes
- Mitigation: < 4 hours
- Resolution: Next business day

**Examples:**
- Admin dashboard slow for specific filter combinations
- Export timing out for large datasets
- Notification emails delayed by 1-2 hours
- UI rendering wrong on specific browser version
- Internal monitoring dashboard unavailable
- Third-party integration showing stale data

---

### SEV3 (P3) - Low Impact

**Definition:** Cosmetic issues, low-impact bugs, documentation errors, no customer functionality affected.

**Impact Criteria:**
- No customer functional impact
- Cosmetic UI issues
- Documentation errors or outdated content
- Minor performance inconsistencies
- Internal-only impact with workaround
- Feature requests labeled as bugs

**Response Requirements:**
- **Alert:** Create ticket, no immediate notification
- **Escalation:** None
- **IC Assignment:** None
- **Communication:** None required
- **External:** No status page update
- **Post-Mortem:** Not required

**Response Time Target:**
- Acknowledgment: Next sprint planning
- Mitigation: Planned release
- Resolution: As capacity allows

**Examples:**
- Button color inconsistent with design system
- Tooltip text has typo
- Log message formatting wrong
- Internal admin tool has minor UI glitch
- Documentation outdated but not misleading
- Error message wording unclear

---

## Impact vs. Urgency Matrix

Use when severity unclear:

```
                High Impact                  Low Impact
              ───────────────────────────────────────────
High         │ SEV0                       │ SEV2          │
Urgency      │ (Complete outage)          │ (Minor issue) │
             │                            │               │
              ───────────────────────────────────────────
Low          │ SEV1                       │ SEV3          │
Urgency      │ (Major degradation)        │ (Backlog)     │
             │                            │               │
              ───────────────────────────────────────────
```

**Impact Dimensions:**
- Customers affected
- Revenue impact
- Core vs. edge functionality
- Workaround availability

**Urgency Dimensions:**
- Degradation speed (getting worse?)
- Time-sensitivity (end of quarter, holiday shopping)
- Escalation risk (security threat, compliance)
- Media/PR exposure potential

---

## Decision Tree

```
1. Is production completely down or critical data at risk?
   ├─ YES → SEV0 (Critical Outage)
   └─ NO  → Continue to #2

2. Is major functionality degraded?
   ├─ YES → Continue to #3
   └─ NO  → Continue to #4

3. Is there a workaround available?
   ├─ YES → SEV1 (Major Degradation)
   └─ NO  → SEV0 (No workaround = Critical)

4. Are customers impacted?
   ├─ YES → SEV2 (Minor Issues)
   └─ NO  → SEV3 (Low Impact)
```

---

## Special Considerations

### Security Incidents

Security incidents often rate higher:
- **Active breach or data exfiltration:** SEV0 (always)
- **Vulnerability discovered, no active exploit:** SEV1
- **Patch required for known CVE:** SEV2
- **Security scan findings:** SEV3

**Additional Actions:**
- Engage security team immediately
- Preserve forensic evidence
- Follow regulatory notification requirements
- Involve legal for SEV0

### Compliance and Regulatory

Compliance incidents get elevated severity:
- **Active compliance violation:** SEV0 (GDPR breach, PCI violation)
- **Potential compliance risk:** SEV1 (audit finding)
- **Reporting delay or error:** SEV2

**Additional Actions:**
- Notify legal and compliance teams
- Track regulatory notification timeline
- Preserve documentation

### Time-Based Severity Escalation

Unresolved incidents can escalate:
- **SEV2 unresolved for 8+ hours:** Consider escalating to SEV1
- **SEV1 unresolved for 4+ hours:** Consider escalating to SEV0
- **Repeated SEV2 incidents:** Pattern may warrant SEV1 for systemic fix

---

## Common Misclassifications

### Over-Severity (Too High)

**Anti-Pattern:** Labeling everything SEV0/SEV1 to get attention

**Examples:**
- Internal tool down → Labeled SEV0 (should be SEV2)
- Single customer bug → Labeled SEV1 (should be SEV2)
- Minor UI glitch → Labeled SEV2 (should be SEV3)

**Solution:** Use decision tree consistently. Review quarterly for patterns.

### Under-Severity (Too Low)

**Anti-Pattern:** Downplaying impact to avoid escalation

**Examples:**
- 20% error rate → Labeled SEV2 (should be SEV1)
- Checkout broken → Labeled SEV3 (should be SEV0)
- Security vulnerability → Labeled SEV2 (should be SEV1)

**Solution:** When uncertain, default to higher severity (can always downgrade).

---

## Severity Reclassification

### Escalation Triggers
- Impact expands (1% → 20% of customers)
- Mitigation attempts fail
- Root cause worse than first assessed
- Secondary failures cascade

### De-escalation Triggers
- Workaround works
- Impact contained to smaller scope
- Service partially restored
- Initial assessment over-estimated

**Process:** IC announces severity change in incident channel. IC updates status page if external communication already sent.

---

## Metrics and Tracking

### Severity Distribution

Track monthly severity counts:
- **Healthy:** 70% SEV3, 20% SEV2, 8% SEV1, 2% SEV0
- **Warning:** 50% SEV1/SEV0 indicates instability
- **Target:** SEV0/SEV1 trending down over quarters

### Severity Duration

Track average resolution time per severity:
- **SEV0:** Target < 2 hours
- **SEV1:** Target < 4 hours
- **SEV2:** Target < 24 hours
- **SEV3:** No target (planned work)

### Reclassification Rate

Track how often severity changes mid-incident:
- **Normal:** < 10% reclassification rate
- **Warning:** > 25% indicates poor initial assessment

---

## Example Scenarios with Classification

### Scenario 1: Database Slow Queries

**Situation:** Database queries take 5 seconds instead of 500ms

**Analysis:**
- Impact: All customers affected, 10x performance degradation
- Functionality: Still working, only slow
- Workaround: None

**Classification:** SEV1 (Major Degradation)

**Reasoning:** Major slowdown for all customers, no workaround, but service still works.

---

### Scenario 2: Login Button Color Wrong

**Situation:** Login button shows green instead of blue per design system

**Analysis:**
- Impact: No functional impact
- Functionality: Login works perfectly
- Workaround: Not applicable

**Classification:** SEV3 (Low Impact)

**Reasoning:** Cosmetic issue, no customer functional impact.

---

### Scenario 3: Payment API 100% Errors

**Situation:** Payment processing returns errors for all requests

**Analysis:**
- Impact: No customers can complete purchases
- Functionality: Core revenue-generating feature down
- Workaround: None

**Classification:** SEV0 (Critical Outage)

**Reasoning:** Revenue-critical functionality completely unavailable, all customers impacted.

---

### Scenario 4: Search Returns Stale Results

**Situation:** Search index 2 hours behind, showing outdated product availability

**Analysis:**
- Impact: All customers see stale data
- Functionality: Search works, data only delayed
- Workaround: Manual refresh of product pages

**Classification:** SEV2 (Minor Issues)

**Reasoning:** Non-critical feature, workaround available, no complete outage.

---

## Interactive Severity Classifier

```bash
python scripts/classify-severity.py
```

Script asks:
1. Is production completely down? (Y/N)
2. What percentage of customers affected? (0-100)
3. Is core functionality impacted? (Y/N)
4. Is there a workaround? (Y/N)
5. Is revenue actively being lost? (Y/N)

From answers, it recommends severity and explains reasoning.

---

## Customization for Your Organization

**Startup (Pre-Revenue):**
- May not need SEV0 (no revenue to lose)
- SEV1 for anything customer-facing
- Focus on learning, not strict classification

**Enterprise (Large Customer Base):**
- May add SEV00 for "Business-Critical Emergency"
- Segment by customer tier (enterprise vs. self-serve)
- SLA-driven severity (SLA breach = higher severity)

**B2B SaaS:**
- Factor customer size into severity (1 enterprise customer down = SEV1)
- Contractual SLAs dictate response times
- Compliance incidents often SEV0

**Consumer App:**
- User count drives severity (1M users = SEV0)
- Factor in app store rating impact
- Viral negative feedback escalates severity

---

## Further Reading

- Google SRE Book: "Monitoring Distributed Systems" (Chapter 6)
- PagerDuty: "Incident Severity Levels"
- Atlassian: "Incident Severity Guide"
- ITIL: "Incident Management - Priority Matrix"
