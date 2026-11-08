# Cookie Security Rules

**Rules:**

1. Session and authentication cookies MUST set `HttpOnly`.
2. Cookies MUST set `Secure` in production (HTTPS only).
3. `SameSite` SHOULD be `Lax` or `Strict`; `None` only when cross-site access required.

---

## Table of Contents

- [HTTP-Only Flag Missing — Medium](#http-only-flag-missing--medium)
- [Insecure Cookie Configuration (Missing Secure Flag) — Medium](#insecure-cookie-configuration-missing-secure-flag--medium)
- [SameSite Cookie Protection — Medium](#samesite-cookie-protection--medium)
- [Cookie Prefix Examples — Low](#cookie-prefix-examples--low)
- [Gorilla Sessions Cookie Security — High](#gorilla-sessions-cookie-security--high)
- [Cookie Best Practices Checklist](#cookie-best-practices-checklist)
- [CWE References](#cwe-references)

## HTTP-Only Flag Missing — Medium

Without HttpOnly, JavaScript can read cookies.

**Bad:**

```go
cookie := &http.Cookie{
    Name:  "session",
    Value: sessionID,
    // DON'T: Missing HttpOnly, Secure flags
}
```

**Good:**

```go
cookie := &http.Cookie{
    Name:     "session",
    Value:    sessionID,
    HttpOnly: true,   // Prevents JavaScript access
    Secure:   true,   // Only sends over HTTPS
    SameSite: http.SameSiteStrictMode,
    Path:     "/",
    MaxAge:   3600,
}
```

---

## Insecure Cookie Configuration (Missing Secure Flag) — Medium

Without Secure, cookies travel over unencrypted HTTP.

**Bad:**

```go
http.SetCookie(w, &http.Cookie{
    Name:  "auth_token",
    Value: token,
    // Missing Secure, HttpOnly flags
})
```

**Good:**

```go
http.SetCookie(w, &http.Cookie{
    Name:     "auth_token",
    Value:    token,
    Secure:   true,   // HTTPS only
    HttpOnly: true,   // No JavaScript access
    SameSite: http.SameSiteLaxMode,
    Path:     "/",
    MaxAge:   86400,
    Domain:   "",  // Default: send to exact host only
})
```

---

## SameSite Cookie Protection — Medium

SameSite blocks CSRF.

**Bad:**

```go
cookie := &http.Cookie{
    Name:     "session",
    Value:    token,
    Secure:   true,
    HttpOnly: true,
    // DON'T: Missing SameSite
}
```

**Good:**

```go
// Strict for high-security operations
authCookie := &http.Cookie{
    Name:     "auth",
    Value:    token,
    Secure:   true,
    HttpOnly: true,
    SameSite: http.SameSiteStrictMode,
}

// Lax for most applications
sessionCookie := &http.Cookie{
    Name:     "session",
    Value:    token,
    Secure:   true,
    HttpOnly: true,
    SameSite: http.SameSiteLaxMode,
}

// None for cross-site cookies (requires Secure: true)
crossSiteCookie := &http.Cookie{
    Name:     "analytics",
    Value:    trackingID,
    Secure:   true,
    HttpOnly: true,
    SameSite: http.SameSiteNoneMode,
}
```

---

## Cookie Prefix Examples — Low

Cookie prefixes make browsers enforce cookie rules.

```go
// __Secure- prefix: Requires Secure flag
secureCookie := &http.Cookie{
    Name:     "__Secure-Session",
    Value:    token,
    Secure:   true,   // Required for __Secure-
    HttpOnly: true,
}

// __Host- prefix: Requires Secure, no Domain, origin-bound path
hostCookie := &http.Cookie{
    Name:     "__Host-CSRF",
    Value:    csrfToken,
    Secure:   true,    // Required
    HttpOnly: true,
    Domain:   "",      // Must be empty
    Path:     "/",     // Required
}
```

---

## Gorilla Sessions Cookie Security — High

**Bad:**

```go
import "github.com/gorilla/sessions"
store := sessions.NewCookieStore([]byte("secret-key")) // DON'T: Hardcoded key
```

**Good:**

```go
import "github.com/gorilla/sessions"

store := sessions.NewCookieStore(
    []byte(os.Getenv("SESSION_AUTH_KEY")),   // Use env var
    []byte(os.Getenv("SESSION_ENC_KEY")),   // Separate encryption key
)

store.Options = &sessions.Options{
    Path:     "/",
    MaxAge:   86400 * 30,
    HttpOnly: true,
    Secure:   true,
    SameSite: http.SameSiteStrictMode,
}
```

---

## Cookie Best Practices Checklist

- [ ] Use short `MaxAge` expiration
- [ ] Avoid setting cookie `Domain` unless necessary
- [ ] Validate cookie values on every request
- [ ] Use cryptographically signed cookies
- [ ] Rotate cookie secrets regularly
- [ ] Clear cookies on logout
- [ ] Use double-submit cookie pattern for CSRF protection

---

## CWE References

- **CWE-1004**: Sensitive Cookie Without 'HttpOnly' Flag
- **CWE-614**: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute
- **CWE-352**: Cross-Site Request Forgery (CSRF)
- **CWE-285**: Improper Authorization
- **CWE-565**: Reliance on Cookies without Validation
