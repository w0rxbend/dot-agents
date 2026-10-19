---
name: analytics
description: "Design or audit an event tracking plan (naming, properties, GA4/GTM, UTMs, validation); use when adding or fixing product or marketing analytics."
source: https://github.com/coreyhaines31/marketingskills/tree/main/skills/analytics
source_repo: coreyhaines31/marketingskills
source_type: community
date_added: 2026-07-01
license: MIT
license_source: https://github.com/coreyhaines31/marketingskills/blob/main/LICENSE
---

# Analytics Tracking

Set up tracking that produces trustworthy, decision-ready data. Start from the decisions the data must inform and the instrumentation that already exists; do not propose another analytics service before auditing the current one.

For in-product analytics (activation funnels, cohort retention, North Star metric, PostHog capture and flags, A/B significance), read [references/product-analytics.md](references/product-analytics.md).

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before implementing tracking, understand:

1. **Business Context** - What decisions will this data inform? What are key conversions?
2. **Current State** - What tracking exists? What tools are in use?
3. **Technical Context** - What's the tech stack? Any privacy/compliance requirements?

---

## Core Principles

### 1. Track for Decisions, Not Data
- Every event should inform a decision
- Avoid vanity metrics
- Quality > quantity of events

### 2. Start with the Questions
- What do you need to know?
- What actions will you take based on this data?
- Work backwards to what you need to track

### 3. Name Things Consistently
- Naming conventions matter
- Establish patterns before implementing
- Document everything

### 4. Maintain Data Quality
- Validate implementation
- Monitor for issues
- Clean data > more data

---

## Tracking Plan Framework

### Structure

```
Event Name | Category | Properties | Trigger | Notes
---------- | -------- | ---------- | ------- | -----
```

### Event Types

| Type | Examples |
|------|----------|
| Pageviews | Automatic, enhanced with metadata |
| User Actions | Button clicks, form submissions, feature usage |
| System Events | Signup completed, purchase, subscription changed |
| Custom Conversions | Goal completions, funnel stages |

**For comprehensive event lists**: See [references/event-library.md](references/event-library.md)

---

## Event Naming Conventions

### Recommended Format: Object-Action

```
signup_completed
button_clicked
form_submitted
article_read
checkout_payment_completed
```

### Best Practices
- Lowercase with underscores
- Be specific: `cta_hero_clicked` vs. `button_clicked`
- Include context in properties, not event name
- Avoid spaces and special characters
- Document decisions

---

## Essential Events

### Marketing Site

| Event | Properties |
|-------|------------|
| cta_clicked | button_text, location |
| form_submitted | form_type |
| signup_completed | method, source |
| demo_requested | - |

### Product/App

| Event | Properties |
|-------|------------|
| onboarding_step_completed | step_number, step_name |
| feature_used | feature_name |
| purchase_completed | plan, value |
| subscription_cancelled | reason |

**For full event library by business type**: See [references/event-library.md](references/event-library.md)

---

## Event Properties

### Standard Properties

| Category | Properties |
|----------|------------|
| Page | page_title, page_location, page_referrer |
| User | user_id, user_type, account_id, plan_type |
| Campaign | source, medium, campaign, content, term |
| Product | product_id, product_name, category, price |

### Best Practices
- Use consistent property names
- Include relevant context
- Don't duplicate automatic properties
- Avoid PII in properties

---

## Conversion Strategy

### What qualifies as a conversion

A conversion marks real value, completed intent and progress that is not undone by a reload: `signup_completed`, `purchase_completed`, `demo_booked`. Page views, button clicks and form starts are intent signals, not conversions.

### Counting rules

- Decide per conversion whether it counts once per session, once per user, or every occurrence, and write that in the tracking plan.
- Use the same rule in every tool (GA4, ad platforms, product analytics, BI); mismatched rules are the most common source of "the numbers disagree".
- Give transactional conversions a deduplication key (order or transaction ID) so redirects, reloads and retries do not double-count.
- Fire on confirmed success (server response, payment confirmation), not on the button click that started it.
- Document how refunds, cancellations and test transactions are excluded.

**Worked example.** `purchase_completed` fires on both the payment redirect and a page reload. Use the paid transaction ID as the dedup key, fire only after payment success, and reconcile one transaction plus two reloads against the order database: expected one counted purchase, no card data, email or raw URL query in properties. Record source count, accepted events, rejected duplicates and unexplained differences for the same window. Test consent denied, consent granted and delayed backend confirmation separately; a `dataLayer.push` alone does not prove delivery.

---

## GA4 Implementation

### Quick Setup

1. Create GA4 property and data stream
2. Install gtag.js or GTM
3. Enable enhanced measurement
4. Configure custom events
5. Mark conversion events as key events in Admin (GA4 renamed "conversions" to "key events" in 2024)

### Custom Event Example

```javascript
gtag('event', 'signup_completed', {
  'method': 'email',
  'plan': 'free'
});
```

**For detailed GA4 implementation**: See [references/ga4-implementation.md](references/ga4-implementation.md)

---

## Google Tag Manager

### Container Structure

| Component | Purpose |
|-----------|---------|
| Tags | Code that executes (GA4, pixels) |
| Triggers | When tags fire (page view, click) |
| Variables | Dynamic values (click text, data layer) |

### Data Layer Pattern

```javascript
dataLayer.push({
  'event': 'form_submitted',
  'form_name': 'contact',
  'form_location': 'footer'
});
```

**For detailed GTM implementation**: See [references/gtm-implementation.md](references/gtm-implementation.md)

---

## UTM Parameter Strategy

### Standard Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| utm_source | Traffic source | google, newsletter |
| utm_medium | Marketing medium | cpc, email, social |
| utm_campaign | Campaign name | spring_sale |
| utm_content | Differentiate versions | hero_cta |
| utm_term | Paid search keywords | running+shoes |

### Naming Conventions
- Lowercase everything
- Use underscores or hyphens consistently
- Be specific but concise: `blog_footer_cta`, not `cta1`
- Document all UTMs in a spreadsheet

---

## Debugging and Validation

### Testing Tools

| Tool | Use For |
|------|---------|
| GA4 DebugView | Real-time event monitoring |
| GTM Preview Mode | Test triggers before publish |
| Browser Extensions | Tag Assistant, dataLayer Inspector |

### Validation Checklist

- [ ] Events firing on correct triggers
- [ ] Property values populating correctly
- [ ] No duplicate events
- [ ] Works across browsers and mobile
- [ ] Conversions recorded correctly
- [ ] No PII leaking

### Common Issues

| Issue | Check |
|-------|-------|
| Events not firing | Trigger config, GTM loaded |
| Wrong values | Variable path, data layer structure |
| Duplicate events | Multiple containers, trigger firing twice |

---

## Measurement Readiness Review (optional rubric)

When auditing an existing setup, score each area from evidence (event definitions, sample payloads, reconciliation against the source of truth). This is a review aid with no validated thresholds; leave an area "unknown" rather than guessing, and never let a high total override a failed reconciliation, duplicate purchases, missing exposures or a consent violation.

| Area | Weight | Look for |
|------|--------|----------|
| Decision alignment | 25 | Business questions written down; every event maps to a decision; nothing tracked "just in case" |
| Event model clarity | 20 | Events are meaningful state changes; consistent naming; properties carry context, not noise |
| Data accuracy | 20 | Fires reliably; no duplication or inflation; values complete; cross-browser and mobile checked |
| Conversion definitions | 15 | Conversions represent real success; counting rules explicit; funnel stages distinguishable |
| Attribution and context | 10 | UTMs consistent; source context preserved; cross-domain/device handled where needed |
| Governance | 10 | Plan documented; owner named; changes versioned and monitored |

Rough reading of the total: 85+ usable for decisions if the evidence holds; 70-84 fix gaps before major decisions; 55-69 unreliable; below 55 do not act on the data. Report remediation in priority order of concrete defects, not by score.

---

## Privacy and Compliance

### Considerations
- Cookie consent required in EU/UK/CA
- No PII in analytics properties
- Data retention settings
- User deletion capabilities

### Implementation
- Use consent mode (wait for consent)
- No IP-anonymization setting needed in GA4 (it never logs or stores IP addresses); in other tools, truncate or drop IPs
- Only collect what you need
- Integrate with consent management platform

---

## Output Format

### Tracking Plan Document

```markdown
# [Site/Product] Tracking Plan

## Overview
- Tools: GA4, GTM
- Last updated: [Date]

## Events

| Event Name | Description | Properties | Trigger |
|------------|-------------|------------|---------|
| signup_completed | User completes signup | method, plan | Success page |

## Custom Dimensions

| Name | Scope | Parameter |
|------|-------|-----------|
| user_type | User | user_type |

## Conversions

| Conversion | Event | Counting |
|------------|-------|----------|
| Signup | signup_completed | Once per session |
```

---

## Task-Specific Questions

1. What tools are you using (GA4, Mixpanel, etc.)?
2. What key actions do you want to track?
3. What decisions will this data inform?
4. Who implements - dev team or marketing?
5. Are there privacy/consent requirements?
6. What's already tracked?

---

## Tools

GA4 (web, Google ecosystem), Mixpanel and Amplitude (product analytics, cohorts), PostHog (open-source analytics, flags, session replay), Segment (event routing to several destinations). Prefer the tool already installed; check each SDK's current API in its official docs before writing code.

## Done when

- Every event in the plan names the decision it supports, its trigger and its properties
- Conversions have explicit counting and dedup rules, identical across tools
- Events were observed in DebugView / GTM preview / the tool's live view with correct values, and consent-denied behavior was tested
- Counts for at least one key conversion reconcile with the source of truth for the same window, with differences explained
- No PII or free text in event properties
