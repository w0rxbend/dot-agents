# Injection Security Rules

**Rules:**

1. SQL queries MUST use parameterized placeholders — NEVER concatenate user input.
2. Command execution MUST use `exec.Command` with separate args — NEVER shell interpolation.
3. HTML output MUST use `html/template` for automatic escaping.
4. SSRF: outbound URLs MUST be validated against an allowlist.

---

## Table of Contents

- [SQL Injection — Critical](#sql-injection--critical)
  - [Dynamic IN clauses](#dynamic-in-clauses)
  - [Dynamic column names and ORDER BY](#dynamic-column-names-and-order-by)
  - [Dynamic WHERE filters](#dynamic-where-filters)
  - [Prefer `sqlx` or `pgx` over raw `database/sql`](#prefer-sqlx-or-pgx-over-raw-databasesql)
- [XPath Injection — High](#xpath-injection--high)
- [Code Injection — Critical](#code-injection--critical)
- [Command Injection — Critical](#command-injection--critical)
- [Template Injection — High](#template-injection--high)
- [Cross-Site Scripting (XSS) — High](#cross-site-scripting-xss--high)
- [HTML Tag Injection — High](#html-tag-injection--high)
- [Server-Side Request Forgery (SSRF) — High](#server-side-request-forgery-ssrf--high)
- [Unsafe Deserialization — Critical](#unsafe-deserialization--critical)
- [CWE References](#cwe-references)

## SQL Injection — Critical

**Bad:**

```go
query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", input)
query := "SELECT * FROM users WHERE id = " + id
query := "DELETE FROM orders WHERE id = " + strconv.Itoa(orderID) // safe but inconsistent — use placeholders everywhere
```

**Good:**

```go
// Placeholder syntax varies by driver: $1 (pgx/lib/pq), ? (MySQL/SQLite)
db.QueryRow("SELECT * FROM users WHERE name = $1", input)
db.Exec("DELETE FROM orders WHERE id = $1", orderID)
```

### Dynamic IN clauses

Never build `IN (...)` by joining user strings. Generate numbered placeholders.

**Bad:**

```go
query := fmt.Sprintf("SELECT * FROM users WHERE id IN (%s)", strings.Join(ids, ","))
```

**Good:**

```go
// Build placeholders: $1, $2, $3, ...
placeholders := make([]string, len(ids))
args := make([]any, len(ids))
for i, id := range ids {
    placeholders[i] = fmt.Sprintf("$%d", i+1)
    args[i] = id
}
query := fmt.Sprintf("SELECT * FROM users WHERE id IN (%s)", strings.Join(placeholders, ","))
rows, err := db.Query(query, args...)
```

With `sqlx`:

```go
query, args, err := sqlx.In("SELECT * FROM users WHERE id IN (?)", ids)
query = db.Rebind(query) // converts ? to $1,$2,... for postgres
rows, err := db.Query(query, args...)
```

### Dynamic column names and ORDER BY

Placeholders only work for **values**, not identifiers (table/column names) or SQL keywords. Allowlist identifiers explicitly.

**Bad:**

```go
query := fmt.Sprintf("SELECT * FROM users ORDER BY %s", sortCol) // SQL injection
```

**Good:**

```go
allowed := map[string]string{
    "name": "name", "created": "created_at", "email": "email",
}
col, ok := allowed[sortCol]
if !ok {
    col = "created_at"
}
query := fmt.Sprintf("SELECT * FROM users ORDER BY %s", col) // safe: col is from allowlist
```

### Dynamic WHERE filters

Build queries incrementally; parameterize every user-supplied value.

```go
var conditions []string
var args []any
idx := 1

if name != "" {
    conditions = append(conditions, fmt.Sprintf("name = $%d", idx))
    args = append(args, name)
    idx++
}
if minAge > 0 {
    conditions = append(conditions, fmt.Sprintf("age >= $%d", idx))
    args = append(args, minAge)
    idx++
}

query := "SELECT * FROM users"
if len(conditions) > 0 {
    query += " WHERE " + strings.Join(conditions, " AND ")
}
rows, err := db.Query(query, args...)
```

### Prefer `sqlx` or `pgx` over raw `database/sql`

`sqlx` and `pgx` give safer ergonomics (named parameters, `IN` clause expansion, struct scanning), still using prepared statements underneath. Less temptation to concatenate strings for complex queries.

---

## XPath Injection — High

**Bad:**

```go
xpathQuery := "//user[@username='" + username + "']" // Vulnerable
```

**Good:**

```go
// Use numeric ID
xpathQuery := fmt.Sprintf("//user[@id='%d']", userID)

// Or parse XML without XPath
```

---

## Code Injection — Critical

**Bad:**

```go
template := "func handle" + resourceName + "() {...}" // DON'T
```

**Good:**

```go
// Validate resource name matches whitelist
if !allowedResources[resourceName] {
    return errors.New("invalid resource")
}
// Use predefined templates
```

---

## Command Injection — Critical

**Bad:**

```go
cmd := exec.Command("sh", "-c", "rm -f /tmp/"+filename) // DON'T
```

**Good:**

```go
// Validate first: bare file name only, else "../etc/x" escapes /tmp
if !filepath.IsLocal(filename) || filepath.Base(filename) != filename {
    return errors.New("invalid filename")
}
cmd := exec.Command("rm", "-f", filepath.Join("/tmp", filename))
```

---

## Template Injection — High

**Bad:**

```go
data := r.URL.Query().Get("user") // Untrusted input
t.Execute(w, data)
```

**Good:**

```go
// Validate input
user := strings.TrimSpace(r.URL.Query().Get("user"))
if !allowedRoles[role] {
    role = "user"
}
t.Execute(w, data)
```

---

## Cross-Site Scripting (XSS) — High

**Bad:**

```go
w.Write([]byte(fmt.Sprintf("<div>%s</div>", data))) // DON'T
```

**Good:**

```go
import "html/template"
t := template.Must(template.New("safe").Parse("<div>{{.}}</div>"))
t.Execute(w, data) // Auto-escapes
```

---

## HTML Tag Injection — High

**Bad:**

```go
fmt.Fprintf(w, "<div>Welcome, %s!</div>", input) // DON'T
```

**Good:**

```go
import "html"
escaped := html.EscapeString(input)
fmt.Fprintf(w, "<div>Welcome, %s!</div>", escaped)
```

---

## Server-Side Request Forgery (SSRF) — High

**Bad:**

```go
url := r.URL.Query().Get("url")
resp, _ := http.Get(url) // DON'T: No validation
```

**Good:**

```go
u, err := url.Parse(targetURL)
// Block non-HTTP/S protocols
if u.Scheme != "http" && u.Scheme != "https" {
    return errors.New("invalid scheme")
}
// Block internal hosts
if isInternalIP(u.Hostname()) {
    return errors.New("internal host not allowed")
}
// Block metadata endpoints
if strings.Contains(u.Hostname(), "metadata.") {
    return errors.New("metadata endpoint blocked")
}
```

Hostname checks alone miss DNS rebinding and redirects: prefer a host allowlist, check resolved IPs at dial time (`net.Dialer.Control`), and re-validate each redirect (`http.Client.CheckRedirect`).

---

## Unsafe Deserialization — Critical

Deserializing untrusted input can cause resource exhaustion, type confusion, or unsafe object construction.

**Bad:**

```go
dec := gob.NewDecoder(r.Body) // DON'T: gob is not hardened for adversarial input
var user interface{}
dec.Decode(&user)
```

**Good:**

```go
import "encoding/json"
dec := json.NewDecoder(r.Body)
var user User
dec.Decode(&user) // JSON doesn't execute code
// Validate fields
```

---

## CWE References

- **CWE-78**: OS Command Injection
- **CWE-89**: SQL Injection
- **CWE-94**: Code Injection
- **CWE-79**: Cross-site Scripting (XSS)
- **CWE-918**: Server-Side Request Forgery (SSRF)
- **CWE-502**: Deserialization of Untrusted Data
- **CWE-20**: Improper Input Validation
