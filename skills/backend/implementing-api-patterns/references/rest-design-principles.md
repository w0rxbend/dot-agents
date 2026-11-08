# REST Design Principles

## Table of Contents

- [Resource Modeling](#resource-modeling)
- [HTTP Methods](#http-methods)
- [HTTP Status Codes](#http-status-codes)
- [URL Design](#url-design)
- [Request and Response Formats](#request-and-response-formats)
- [Error Handling](#error-handling)
- [HATEOAS](#hateoas)

## Resource Modeling

### Resources as Nouns

Name resources with nouns (not verbs):

**Good:**
```
GET /users
GET /users/123
GET /users/123/posts
```

**Bad:**
```
GET /getUsers
GET /getUserById?id=123
POST /createUser
```

### Collection and Instance Resources

**Collection:** `/users` (plural noun)
**Instance:** `/users/123` (collection + ID)

### Nested Resources

Nested paths show relationships:

```
/users/123/posts           # Posts belonging to user 123
/users/123/posts/456       # Post 456 by user 123
/posts/456/comments        # Comments on post 456
```

**Limit nesting depth:** generally no more than 2-3 levels.

### Resource Naming Conventions

- Lowercase letters
- Hyphens (not underscores) for multi-word names
- Plural nouns for collections
- Avoid file extensions (.json, .xml)

**Examples:**
```
/api/v1/user-profiles
/api/v1/shopping-carts
/api/v1/product-categories
```

## HTTP Methods

### GET - Retrieve Resource

**Purpose:** Retrieve resource representation(s)
**Safe:** Yes (no side effects)
**Idempotent:** Yes (multiple identical requests = same result)

**Examples:**
```
GET /users              # List all users
GET /users/123          # Get specific user
GET /users?role=admin   # Filter users
```

**Response:**
- 200 OK with resource data
- 404 Not Found if resource doesn't exist

### POST - Create Resource

**Purpose:** Create new resource
**Safe:** No
**Idempotent:** No (creates new resource each time)

**Examples:**
```
POST /users
Content-Type: application/json

{
  "name": "Alice",
  "email": "alice@example.com"
}
```

**Response:**
- 201 Created with `Location` header pointing to new resource
- Include created resource in response body

```
HTTP/1.1 201 Created
Location: /users/124
Content-Type: application/json

{
  "id": 124,
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2025-12-02T10:00:00Z"
}
```

### PUT - Update/Replace Resource

**Purpose:** Update entire resource, or create it if missing
**Safe:** No
**Idempotent:** Yes (multiple identical requests = same result)

**Examples:**
```
PUT /users/123
Content-Type: application/json

{
  "name": "Alice Updated",
  "email": "alice.new@example.com"
}
```

**Response:**
- 200 OK with updated resource
- 201 Created if resource was created

**Important:** PUT replaces ENTIRE resource. Client must send all fields.

### PATCH - Partial Update

**Purpose:** Partially update resource
**Safe:** No
**Idempotent:** Depends on implementation (usually yes)

**Examples:**
```
PATCH /users/123
Content-Type: application/json

{
  "email": "alice.new@example.com"
}
```

**Response:**
- 200 OK with updated resource
- 204 No Content if no response body

**JSON Patch (RFC 6902):**
```
PATCH /users/123
Content-Type: application/json-patch+json

[
  { "op": "replace", "path": "/email", "value": "alice.new@example.com" },
  { "op": "add", "path": "/phone", "value": "+1234567890" }
]
```

### DELETE - Remove Resource

**Purpose:** Delete resource
**Safe:** No
**Idempotent:** Yes (deleting already-deleted resource returns same status)

**Examples:**
```
DELETE /users/123
```

**Response:**
- 200 OK with deleted resource
- 204 No Content if no response body
- 404 Not Found if resource doesn't exist (acceptable)

## HTTP Status Codes

### 2xx Success

| Code | Meaning | Usage |
|------|---------|-------|
| 200 OK | Request succeeded | GET, PUT, PATCH responses |
| 201 Created | Resource created | POST responses, include Location header |
| 202 Accepted | Accepted for processing | Async operations |
| 204 No Content | Success, no response body | DELETE, PATCH responses |

### 3xx Redirection

| Code | Meaning | Usage |
|------|---------|-------|
| 301 Moved Permanently | Resource permanently moved | Deprecated endpoints |
| 302 Found | Temporary redirect | Rare in APIs |
| 304 Not Modified | Not modified (caching) | Conditional GET requests |

### 4xx Client Errors

| Code | Meaning | Usage |
|------|---------|-------|
| 400 Bad Request | Invalid request syntax or validation | Malformed JSON, validation errors |
| 401 Unauthorized | Authentication required | Missing or invalid credentials |
| 403 Forbidden | Authenticated but not authorized | Permission denied |
| 404 Not Found | Resource doesn't exist | Invalid resource ID |
| 405 Method Not Allowed | HTTP method not supported | POST to read-only resource |
| 409 Conflict | Conflicts with current state | Duplicate resource, version conflict |
| 422 Unprocessable Entity | Validation errors | Semantic validation failures |
| 429 Too Many Requests | Rate limit exceeded | Rate limiting |

### 5xx Server Errors

| Code | Meaning | Usage |
|------|---------|-------|
| 500 Internal Server Error | Generic server error | Unhandled exceptions |
| 502 Bad Gateway | Invalid response from upstream | Proxy/gateway errors |
| 503 Service Unavailable | Temporarily unavailable | Maintenance, overload |
| 504 Gateway Timeout | Upstream timeout | Slow upstream services |

## URL Design

### API Versioning

**URI Versioning (Most Common):**
```
/api/v1/users
/api/v2/users
```

**Header Versioning:**
```
GET /api/users
Accept: application/vnd.myapi.v1+json
```

**Media Type Versioning:**
```
GET /api/users
Accept: application/vnd.myapi-v2+json
```

**Recommendation:** Use URI versioning. Simplest and clearest.

### Filtering

Filter collections with query parameters:

```
GET /users?role=admin
GET /users?created_after=2025-01-01
GET /users?status=active&department=engineering
```

### Sorting

Use `sort` or `order_by` query parameter:

```
GET /users?sort=created_at
GET /users?sort=-created_at        # Descending
GET /users?sort=name,created_at    # Multiple fields
```

### Pagination

See `pagination-patterns.md` for pagination strategies.

**Cursor-Based (Recommended):**
```
GET /users?cursor=xyz123&limit=20
```

**Offset-Based (Simple Cases):**
```
GET /users?page=2&per_page=20
GET /users?offset=20&limit=20
```

### Field Selection (Sparse Fieldsets)

Let clients request specific fields:

```
GET /users?fields=id,name,email
GET /users/123?fields=name,posts.title
```

## Request and Response Formats

### Request Format

**JSON (Recommended):**
```
POST /users
Content-Type: application/json

{
  "name": "Alice",
  "email": "alice@example.com"
}
```

**Form Data:**
```
POST /users
Content-Type: application/x-www-form-urlencoded

name=Alice&email=alice@example.com
```

**Multipart (File Uploads):**
```
POST /uploads
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="photo.jpg"
Content-Type: image/jpeg

[binary data]
------WebKitFormBoundary--
```

### Response Format

**Standard JSON Response:**
```json
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2025-12-02T10:00:00Z",
  "updated_at": "2025-12-02T10:00:00Z"
}
```

**Collection Response:**
```json
{
  "items": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ],
  "next_cursor": "xyz123",
  "has_more": true
}
```

## Error Handling

### RFC 7807 Problem Details

Use standard error format:

```json
{
  "type": "https://api.example.com/errors/insufficient-balance",
  "title": "Insufficient Balance",
  "status": 400,
  "detail": "Account balance is $10, but transaction requires $50",
  "instance": "/transactions/123",
  "balance": 10.00,
  "required": 50.00
}
```

**Fields:**
- `type`: URI identifying problem type
- `title`: Short, human-readable summary
- `status`: HTTP status code
- `detail`: Explanation specific to this occurrence
- `instance`: URI identifying this specific occurrence
- Extra fields allowed for more context

### Validation Errors

**Field-Level Validation:**
```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request validation failed",
  "errors": {
    "email": [
      "Email is required",
      "Email must be valid format"
    ],
    "age": [
      "Age must be at least 18"
    ]
  }
}
```

**FastAPI Example:**
```python
from fastapi import HTTPException

@app.post("/users")
async def create_user(user: UserCreate):
    if await email_exists(user.email):
        raise HTTPException(
            status_code=409,
            detail={
                "type": "https://api.example.com/errors/duplicate-email",
                "title": "Duplicate Email",
                "detail": f"Email {user.email} is already registered"
            }
        )
    return create_user_in_db(user)
```

## HATEOAS

Hypermedia as the Engine of Application State (HATEOAS) puts links to related resources in responses.

**Example Response:**
```json
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "_links": {
    "self": {
      "href": "/users/123"
    },
    "posts": {
      "href": "/users/123/posts"
    },
    "update": {
      "href": "/users/123",
      "method": "PUT"
    },
    "delete": {
      "href": "/users/123",
      "method": "DELETE"
    }
  }
}
```

**Benefits:**
- Self-documenting API
- Clients can discover actions
- Server can change URLs without breaking clients

**Drawbacks:**
- Larger responses
- Not widely adopted
- Needs client support

**Recommendation:** Use HATEOAS for public APIs where discoverability matters. Skip for internal APIs where clients know structure.

## Best Practices Summary

1. **Include timestamps:** `created_at`, `updated_at` on resources
2. **Document with OpenAPI:** Auto-generate when possible (FastAPI, Hono)

## Performance Optimization

**Connection Pooling:**
- Reuse database connections
- Tune pool size

**Caching:**
- Use HTTP caching headers (ETag, Cache-Control)
- Application-level caching for expensive queries
- See `caching-patterns.md` for details

**Rate Limiting:**
- Per-user or per-IP rate limits
- See `rate-limiting-strategies.md` for patterns

**Compression:**
- Enable gzip/brotli response compression

**Database Optimization:**
- Index frequently queried fields
- Fix N+1 queries

## Security Considerations

**Authentication:**
- JWT tokens for stateless authentication
- OAuth 2.0 for third-party access
- API keys for server-to-server

**Authorization:**
- Role-based access control (RBAC)
- Resource-level permissions
- Validate ownership before operations

**Input Validation:**
- Validate all input (never trust client)
- Use schema validation (Pydantic, Zod)
- Sanitize against injection attacks

**HTTPS:**
- Always use HTTPS in production
- Redirect HTTP to HTTPS

**CORS:**
- Configure allowed origins
- Don't use `*` for production APIs

See auth-security skill for full security patterns.
