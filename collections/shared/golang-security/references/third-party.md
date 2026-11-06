# Third-Party Data Leak Rules

**Rules:**

1. PII MUST be filtered before sending to third-party services.
2. Error tracking MUST NOT receive raw user data. Redact with `BeforeSend` hooks.

---

## Table of Contents

- [Overview](#overview)
- [Common Vulnerable Services](#common-vulnerable-services)
- [Error Tracking Services — Medium](#error-tracking-services--medium)
- [Analytics/Monitoring Services — Medium](#analyticsmonitoring-services--medium)
- [Data Filtering Layer](#data-filtering-layer)
- [Review Checklist](#review-checklist)
- [CWE References](#cwe-references)

## Overview

Rules detect Go code that sends data to third-party services. Always review what data goes out. Confirm it complies with privacy regulations (GDPR, CCPA, etc.).

---

## Common Vulnerable Services

| Service          | Risk                                                  |
| ---------------- | ----------------------------------------------------- |
| Airbrake         | Error tracking - may send sensitive data              |
| Bugsnag          | Error tracking - sensitive data exposure              |
| Sentry           | Error tracking - sensitive data in breadcrumbs/events |
| Rollbar          | Error tracking - sensitive data leaks                 |
| Honeybadger      | Error tracking - sensitive data leaks                 |
| New Relic        | Monitoring - sensitive data exposure                  |
| Datadog          | Monitoring - sensitive data in telemetry              |
| OpenTelemetry    | Observability - sensitive data in traces/metrics      |
| Google Analytics | Analytics - PII tracking risks                        |
| Algolia          | Search API - data exfiltration risks                  |
| Segment          | Analytics - PII tracking risks                        |
| BigQuery         | Analytics - sensitive data in queries                 |
| ClickHouse       | Database - sensitive data queries                     |
| Elasticsearch    | Search engine - sensitive data in queries             |

---

## Error Tracking Services — Medium

**Bad:**

```go
import "github.com/getsentry/sentry-go"

sentry.CaptureException(err) // DON'T: Captures full request context
```

**Good:**

```go
sentry.Init(sentry.ClientOptions{
    Dsn: "https://xxx@sentry.io/123",
    RequestHeaders: []string{"Accept", "User-Agent"},
    BeforeSend: func(event *sentry.Event, hint *sentry.EventHint) *sentry.Event {
        // Remove sensitive headers
        if event.Request != nil {
            delete(event.Request.Headers, "Authorization")
            delete(event.Request.Headers, "Cookie")
        }
        return event
    },
})
```

---

## Analytics/Monitoring Services — Medium

**Bad:**

```go
analytics.Track("user_signed_up", analytics.Properties{
    "email":   user.Email,   // DON'T: PII!
    "phone":   user.Phone,   // DON'T: PII!
    "address": user.Address, // DON'T: PII!
})
```

**Good:**

```go
analytics.Track("user_signed_up", analytics.Properties{
    "user_id":        user.ID,          // OK: Internal identifier
    "plan":           user.Plan,        // OK: Business data
    "country":        user.CountryCode, // OK: Non-identifying
})

// Hash PII for correlation
func hashEmail(email string) string {
    h := sha256.New()
    h.Write([]byte(email))
    return hex.EncodeToString(h.Sum(nil))[:8]
}
```

---

## Data Filtering Layer

```go
type DataFilter struct {
    sensitiveFields []string
}

func NewDataFilter() *DataFilter {
    return &DataFilter{
        sensitiveFields: []string{
            "password", "token", "secret", "key", "email",
            "phone", "address", "ssn", "credit_card", "bank_account",
        },
    }
}

func (f *DataFilter) Filter(data map[string]interface{}) map[string]interface{} {
    result := make(map[string]interface{})
    for k, v := range data {
        keyLower := strings.ToLower(k)
        isSensitive := false
        for _, field := range f.sensitiveFields {
            if strings.Contains(keyLower, field) {
                isSensitive = true
                break
            }
        }
        if isSensitive {
            result[k] = "[REDACTED]"
        } else {
            result[k] = v
        }
    }
    return result
}
```

---

## Review Checklist

Before integrating any third-party service:

- [ ] Identify what data gets sent
- [ ] Remove all PII/PHI from transmitted data
- [ ] Review data residency requirements
- [ ] Set data retention policies
- [ ] Log and audit data exports
- [ ] Configure error handling to avoid data exposure
- [ ] Review terms of service on data usage
- [ ] Add user consent management
- [ ] Support data deletion requests
- [ ] Audit data flows regularly

---

## CWE References

- **CWE-200**: Exposure of Sensitive Information
- **CWE-359**: Exposure of Private Personal Information
- **CWE-201**: Information Exposure Through Sent Data
