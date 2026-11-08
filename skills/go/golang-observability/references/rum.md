# Real User Monitoring (RUM) and Product Observability

## Table of Contents

- [What RUM Is](#what-rum-is)
- [RUM Capabilities](#rum-capabilities)
- [Identity Key: Use `user_id`, Never Email](#identity-key-use-user_id-never-email)
- [Backend Role in RUM](#backend-role-in-rum)
  - [1. Server-Side Event Tracking](#1-server-side-event-tracking)
  - [2. Connecting Frontend Sessions to Backend Traces](#2-connecting-frontend-sessions-to-backend-traces)
  - [3. CDP Event Ingestion](#3-cdp-event-ingestion)
- [GDPR and CCPA Compliance](#gdpr-and-ccpa-compliance)
  - [Consent Management](#consent-management)
  - [Data Subject Rights Endpoints](#data-subject-rights-endpoints)
  - [Privacy Checklist](#privacy-checklist)
- [Self-Hosted vs SaaS](#self-hosted-vs-saas)
- [Cost of RUM](#cost-of-rum)

## What RUM Is

Backend observability (logs, metrics, traces, profiles) shows how your **system** behaves. RUM shows how your **users** experience it. Frontend SDKs capture browser-side signals. Go backend still plays critical role: tracks server-side business events, feeds Customer Data Platforms, correlates user sessions with backend traces.

## RUM Capabilities

| Capability | What it reveals | Example tools |
| --- | --- | --- |
| **Product Analytics** | What users do — page views, clicks, feature adoption, retention | PostHog, Amplitude, Mixpanel |
| **Funnel Analysis** | Where users drop off in multi-step flows (signup, checkout, onboarding) | PostHog, Amplitude, Mixpanel |
| **CDP** | Unified user profile from all data sources — events, properties, segments | Segment, RudderStack |

## Identity Key: Use `user_id`, Never Email

distinct_id (identity key) for all RUM tracking MUST be your internal, immutable `user_id`. NEVER use email addresses.

```go
// ✗ Bad — email is mutable, PII, and breaks analytics when users change it
posthogClient.Enqueue(posthog.Capture{
    DistinctId: user.Email, // "alice@example.com" → user changes email → events split into two users
    Event:      "order_completed",
})

// ✓ Good — user_id is immutable, stable, and not PII
posthogClient.Enqueue(posthog.Capture{
    DistinctId: user.ID, // "usr_a1b2c3" — never changes, always the same user
    Event:      "order_completed",
})
```

**Why email is a bad identity key:**

- **Mutable** — users change email. Events before and after split into two users, breaking funnels, retention analysis and cohort tracking.
- **PII** — every event, session recording and analytics query then holds personally identifiable information. Complicates GDPR/CCPA compliance: you can't anonymize analytics without losing user identity.
- **Non-unique across systems** — same email may belong to different accounts across services or environments.
- **Leaks into third-party systems** — distinct_id goes to your analytics platform (PostHog, Segment, etc.). Email there means PII shared with every vendor in your analytics pipeline.

Use `user_id` as identity key everywhere: PostHog `DistinctId`, Segment `UserId`, Amplitude `user_id`. Store email as user property if needed for display, never as primary key.

## Backend Role in RUM

### 1. Server-Side Event Tracking

Track critical server-side business events (payment completed, subscription upgraded, email sent) from Go, so they land in same analytics pipeline as frontend events.

```go
import "github.com/posthog/posthog-go"

var posthogClient posthog.Client

func initPostHog() {
    var err error
    posthogClient, err = posthog.NewWithConfig(
        os.Getenv("POSTHOG_API_KEY"),
        posthog.Config{Endpoint: os.Getenv("POSTHOG_HOST")},
    )
    if err != nil {
        slog.Error("failed to init PostHog", "error", err)
    }
}

func (s *OrderService) Complete(ctx context.Context, order Order) error {
    // ... business logic ...

    // Track server-side event — appears alongside frontend events in PostHog
    posthogClient.Enqueue(posthog.Capture{
        DistinctId: order.UserID, // immutable user_id, not email
        Event:      "order_completed",
        Properties: posthog.NewProperties().
            Set("order_id", order.ID).
            Set("amount", order.Total).
            Set("payment_method", order.PaymentMethod).
            Set("item_count", len(order.Items)),
    })

    return nil
}
```

### 2. Connecting Frontend Sessions to Backend Traces

Pass frontend session ID or distinct ID in HTTP headers to correlate backend traces with RUM sessions. When user reports "the page was slow," you find their session recording AND backend trace for same request.

```go
func TracingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx := r.Context()
        span := trace.SpanFromContext(ctx)

        // Attach RUM session ID to the backend span
        if sessionID := r.Header.Get("X-Session-ID"); sessionID != "" {
            span.SetAttributes(attribute.String("rum.session_id", sessionID))
        }

        // Attach analytics distinct ID for user correlation
        if distinctID := r.Header.Get("X-Distinct-ID"); distinctID != "" {
            span.SetAttributes(attribute.String("rum.distinct_id", distinctID))
        }

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

### 3. CDP Event Ingestion

With Customer Data Platform (Segment, RudderStack), Go backend sends events via CDP's server-side SDK. CDP merges them with frontend events into single user profile.

```go
import "github.com/segmentio/analytics-go/v3"

var segmentClient analytics.Client

func initSegment() {
    segmentClient = analytics.New(os.Getenv("SEGMENT_WRITE_KEY"))
}

func (s *UserService) Upgrade(ctx context.Context, userID string, plan string) error {
    // ... business logic ...

    // Track through CDP — unified with frontend events
    segmentClient.Enqueue(analytics.Track{
        UserId: userID, // immutable user_id, not email
        Event:  "plan_upgraded",
        Properties: analytics.NewProperties().
            Set("plan", plan).
            Set("source", "api"),
    })

    // Update user profile in CDP
    segmentClient.Enqueue(analytics.Identify{
        UserId: userID,
        Traits: analytics.NewTraits().
            Set("plan", plan).
            Set("upgraded_at", time.Now()),
    })

    return nil
}
```

## GDPR and CCPA Compliance

RUM collects user behavior data (clicks, page views, session recordings), so privacy regulations apply. Compliance is not optional. Violations carry heavy fines (GDPR: up to 4% of global revenue, CCPA: $7,500 per intentional violation).

### Consent Management

GDPR/CCPA consent SHOULD be obtained before loading RUM SDKs or sending tracking events. Covers both frontend scripts and server-side event tracking.

```go
// Server-side: check consent before tracking
func (s *OrderService) Complete(ctx context.Context, order Order) error {
    // ... business logic ...

    // Only track if user has consented to analytics
    consent := auth.ConsentFromContext(ctx)
    if consent.Analytics {
        posthogClient.Enqueue(posthog.Capture{
            DistinctId: order.UserID,
            Event:      "order_completed",
            Properties: posthog.NewProperties().
                Set("order_id", order.ID).
                Set("amount", order.Total),
        })
    }

    return nil
}
```

### Data Subject Rights Endpoints

GDPR and CCPA require letting users access, export and delete their data. Implement API endpoints that propagate these requests to every system holding user data: database, analytics platform, CDP. Authorize every request: only the authenticated owner of `:id` (or an admin) may export or delete, else 403.

```go
// DELETE /api/users/:id/data — GDPR Article 17 "Right to Erasure"
func (h *PrivacyHandler) HandleDataDeletion(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    userID := chi.URLParam(r, "id")
    if !auth.CanAccessUser(ctx, userID) { // caller must be this user or an admin
        http.Error(w, "forbidden", http.StatusForbidden)
        return
    }

    // 1. Delete from your database
    if err := h.userRepo.DeleteAllData(ctx, userID); err != nil {
        slog.ErrorContext(ctx, "failed to delete user data", "user_id", userID, "error", err)
        http.Error(w, "internal error", http.StatusInternalServerError)
        return
    }

    // 2. Delete from analytics platform
    if err := h.posthog.DeleteUser(ctx, userID); err != nil {
        slog.ErrorContext(ctx, "failed to delete analytics data", "user_id", userID, "error", err)
    }

    // 3. Delete from CDP
    if err := h.segment.DeleteUser(ctx, userID); err != nil {
        slog.ErrorContext(ctx, "failed to delete CDP data", "user_id", userID, "error", err)
    }

    slog.InfoContext(ctx, "user data deletion completed", "user_id", userID)
    w.WriteHeader(http.StatusNoContent)
}

// GET /api/users/:id/data — GDPR Article 15 "Right of Access"
func (h *PrivacyHandler) HandleDataExport(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    userID := chi.URLParam(r, "id")
    if !auth.CanAccessUser(ctx, userID) { // caller must be this user or an admin
        http.Error(w, "forbidden", http.StatusForbidden)
        return
    }

    export, err := h.userRepo.ExportAllData(ctx, userID)
    if err != nil {
        slog.ErrorContext(ctx, "failed to export user data", "user_id", userID, "error", err)
        http.Error(w, "internal error", http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(export)
}
```

### Privacy Checklist

- [ ] **Consent before tracking** — no analytics scripts load and no server-side events fire until user consents
- [ ] **Consent + cookie banner** — clear opt-in (not pre-checked boxes), separate consent for analytics vs marketing vs functional (frontend job, but backend must respect consent flag)
- [ ] **Data minimization** — collect only what you need, never track PII in analytics events
- [ ] **Data retention policy** — auto-delete old analytics data (e.g., 2 years for aggregated analytics)
- [ ] **Data subject rights** — endpoints for data export (right of access) and deletion (right to erasure)
- [ ] **Data processing agreements** — signed DPAs with all third-party analytics/CDP vendors
- [ ] **Privacy policy** — lists all RUM tools, data they collect, retention period
- [ ] **Identity key is not PII** — use `user_id`, not email, as distinct_id across all platforms
- [ ] **Self-hosted option** — consider self-hosting (PostHog, Matomo): keeps data in your infrastructure, simplifies compliance

## Self-Hosted vs SaaS

| Factor | Self-hosted (PostHog, Matomo) | SaaS (Amplitude, Mixpanel) |
| --- | --- | --- |
| **Data residency** | Full control — data stays in your infra | Data on vendor's servers |
| **GDPR compliance** | Simpler — no cross-border data transfer | Requires DPA, SCCs, or adequacy decision |
| **Cost** | Infrastructure cost, scales with volume | Per-event or per-seat pricing |
| **Maintenance** | You manage upgrades, scaling, backups | Vendor handles everything |
| **Features** | Catching up but improving fast | Often more polished and feature-rich |

For EU-focused products or strict data residency requirements, self-hosting PostHog is pragmatic choice. Removes most GDPR concerns around cross-border data transfer.

## Cost of RUM

RUM costs scale with **event volume**:

- **Event-based pricing** — every page view, click and custom event counts. Busy SaaS app can produce millions of events/month per user segment.
- **CDP costs** — CDPs charge per tracked user and per event. Segment at scale can cost more than your whole backend infrastructure.

**Mitigation:**

- Filter events server-side to drop low-value ones before they reach analytics platform
- Self-host where possible: per-event pricing becomes fixed infrastructure cost
- Set data retention limits on aggregated analytics
