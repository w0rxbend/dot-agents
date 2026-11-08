---
name: shipping-and-launch
description: "Prepare a production launch - pre-launch readiness checklist, feature-flag strategy, staged/canary rollout, error-budget release gate, monitoring and a rollback plan. Use when getting a release ready to ship or deciding go/no-go; use building-ci-pipelines for the deploy pipeline and managing-incidents for the on-call process."
---

# Shipping and Launch

Agent proposes deploys, flag changes, rollbacks and team notices; runs each only after user confirms.

## When to Use

- First production deploy of a feature
- Releasing significant change to users
- Migrating data or infrastructure
- Opening beta or early access program
- Any risky deployment (all of them)

## The Pre-Launch Checklist

### Code Quality

- [ ] All tests pass (unit, integration, e2e)
- [ ] Build succeeds with no warnings
- [ ] Lint and type checking pass
- [ ] Code reviewed and approved
- [ ] No TODO comments blocking launch
- [ ] No `console.log` debugging in production code
- [ ] Error handling covers expected failure modes

### Security

- [ ] No secrets in code or version control
- [ ] Dependency audit (`npm audit`, `pip-audit`, `cargo audit`, ...) shows no critical or high vulnerabilities
- [ ] Input validation on all user-facing endpoints
- [ ] Authentication and authorization checks in place
- [ ] Security headers configured (CSP, HSTS, etc.)
- [ ] Rate limiting on authentication endpoints
- [ ] CORS limited to specific origins (not wildcard)

### Performance

- [ ] Core Web Vitals within "Good" thresholds
- [ ] No N+1 queries in critical paths
- [ ] Images optimized (compression, responsive sizes, lazy loading)
- [ ] Bundle size within budget
- [ ] Database queries have appropriate indexes
- [ ] Static assets and repeated queries cached

### Accessibility

- [ ] All interactive elements keyboard-navigable
- [ ] Screen reader conveys page content and structure
- [ ] Color contrast meets WCAG 2.1 AA (4.5:1 for text)
- [ ] Focus management correct for modals and dynamic content
- [ ] Error messages descriptive and tied to form fields
- [ ] No accessibility warnings in axe-core or Lighthouse

### Infrastructure

- [ ] Environment variables set in production
- [ ] Database migrations applied (or ready to apply)
- [ ] DNS and SSL configured
- [ ] CDN configured for static assets
- [ ] Logging and error reporting configured
- [ ] Health check endpoint responds

### Documentation

- [ ] README updated with new setup requirements
- [ ] API documentation current
- [ ] ADRs written for architectural decisions
- [ ] Changelog updated
- [ ] User-facing documentation updated (if applicable)

## Feature Flag Strategy

Ship behind feature flags to decouple deployment from release:

```typescript
// Feature flag check
const flags = await getFeatureFlags(userId);

if (flags.taskSharing) {
  // New feature: task sharing
  return <TaskSharingPanel task={task} />;
}

// Default: existing behavior
return null;
```

**Rules:**
- Every feature flag has owner and expiration date
- Clean up flags (remove flag and dead code path) within 2 weeks of full rollout
- Don't nest feature flags (combinations grow exponentially)
- Test both flag states (on and off) in CI

## Staged Rollout

### The Rollout Sequence

```
1. DEPLOY to staging
   └── Full test suite in staging environment
   └── Manual smoke test of critical flows

2. DEPLOY to production (feature flag OFF)
   └── Verify deployment succeeded (health check)
   └── Check error monitoring (no new errors)

3. ENABLE for team (flag ON for internal users)
   └── Team uses the feature in production
   └── 24-hour monitoring window

4. CANARY rollout (flag ON for 5% of users)
   └── Monitor error rates, latency, user behavior
   └── Compare metrics: canary vs. baseline
   └── 24-48 hour monitoring window
   └── Advance only if all thresholds pass (see table below)

5. GRADUAL increase (25% -> 50% -> 100%)
   └── Same monitoring at each step
   └── Ability to roll back to previous percentage at any point

6. FULL rollout (flag ON for all users)
   └── Monitor for 1 week
   └── Clean up feature flag
```

### Rollout Decision Thresholds

At each stage, use these thresholds to advance, hold or roll back:

| Metric | Advance (green) | Hold and investigate (yellow) | Roll back (red) |
|--------|-----------------|-------------------------------|-----------------|
| Error rate | Within 10% of baseline | 10-100% above baseline | >2x baseline |
| P95 latency | Within 20% of baseline | 20-50% above baseline | >50% above baseline |
| Client JS errors | No new error types | New errors at <0.1% of sessions | New errors at >0.1% of sessions |
| Business metrics | Neutral or positive | Decline <5% (may be noise) | Decline >5% |

### When to Roll Back

Roll back immediately if:
- Error rate above 2x baseline
- P95 latency up more than 50%
- User-reported issues spike
- Data integrity issues detected
- Security vulnerability discovered

## Monitoring and Observability

### What to Monitor

```
Application metrics:
├── Error rate (total and by endpoint)
├── Response time (p50, p95, p99)
├── Request volume
├── Active users
└── Key business metrics (conversion, engagement)

Infrastructure metrics:
├── CPU and memory utilization
├── Database connection pool usage
├── Disk space
├── Network latency
└── Queue depth (if applicable)

Client metrics:
├── Core Web Vitals (LCP, INP, CLS)
├── JavaScript errors
├── API error rates from client perspective
└── Page load time
```

### Error Reporting

```typescript
// Set up error boundary with reporting
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true }; // render the fallback on the next pass
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Report to error tracking service
    reportError(error, {
      componentStack: info.componentStack,
      userId: getCurrentUser()?.id,
      page: window.location.pathname,
    });
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback onRetry={() => this.setState({ hasError: false })} />;
    }
    return this.props.children;
  }
}

// Server-side error reporting
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  reportError(err, {
    method: req.method,
    url: req.url,
    userId: req.user?.id,
  });

  // Don't expose internals to users
  res.status(500).json({
    error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' },
  });
});
```

### Post-Launch Verification

First hour after launch:

```
1. Check health endpoint returns 200
2. Check error monitoring dashboard (no new error types)
3. Check latency dashboard (no regression)
4. Test the critical user flow manually
5. Verify logs are flowing and readable
6. Confirm rollback mechanism works (dry run if possible)
```

## Error Budget Release Gate

Error budget (fraction of requests or time SLO allows to fail) decides if shipping is safe. Objective gate, not negotiation:

```
Budget remaining > 20%  →  Ship normally; monitor closely
Budget remaining 0–20%  →  Slow rollouts only; no high-risk changes
Budget exhausted        →  Freeze feature work; focus entirely on reliability
Budget resets           →  Resume normal pace; bake in the fix that recovered it
```

Treat high burn rate during canary (budget consumed faster than baseline pace) as **hold** signal, same as elevated error rate in rollout thresholds table above.

## Rollback Strategy

Write rollback plan before every deployment:

```markdown
## Rollback Plan for [Feature/Release]

### Trigger Conditions
- Error rate > 2x baseline
- P95 latency > [X]ms
- User reports of [specific issue]

### Rollback Steps
1. Disable feature flag (if applicable)
   OR
1. Deploy previous version: `git revert <commit>`, ship via normal PR/protected-branch flow
2. Verify rollback: health check, error monitoring
3. Communicate: notify team of rollback

### Database Considerations
- Migration [X] has a rollback: <verified command or runbook link>
- Data inserted by new feature: [preserved / cleaned up]

### Time to Rollback
- Feature flag: < 1 minute
- Redeploy previous version: < 5 minutes
- Database rollback: < 15 minutes
```
## See Also

- Application security review before launch: `security-and-hardening`
- Alerting rules and SLO-tied thresholds: `observability-and-instrumentation`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It works in staging, it'll work in production" | Production differs in data, traffic patterns, edge cases. Monitor after deploy. |
| "We don't need feature flags for this" | Every feature benefits from kill switch. Even "simple" changes can break things. |
| "We'll add monitoring later" | Add before launch. Can't debug what you can't see. |
| "Rolling back is admitting failure" | Rolling back is responsible engineering. Shipping broken feature is the failure. |
| "The error rate looks fine, let's keep shipping" | Check burn rate, not only current error rate. Budget burning faster than baseline means hold, even when individual thresholds are green. |

## Red Flags

- Production environment configured from memory, not code
- "It's Friday afternoon, let's ship it"

## Verification

Before deploying:

- [ ] Pre-launch checklist completed (all sections green)
- [ ] Feature flag configured (if applicable)
- [ ] Rollback plan documented
- [ ] Monitoring dashboards set up
- [ ] Team notified of deployment

After deploying:

- [ ] Health check returns 200
- [ ] Error rate normal
- [ ] Latency normal
- [ ] Critical user flow works
- [ ] Logs flowing
- [ ] Rollback tested or verified ready

For every shipped service:

- [ ] Error budget policy in place: actions defined for budget below 20% and for exhausted budget
