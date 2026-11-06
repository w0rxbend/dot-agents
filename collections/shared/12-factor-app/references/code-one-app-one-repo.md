---
title: Enforce One-to-One Correlation Between Codebase and Application
impact: CRITICAL
impactDescription: prevents coupling, enables independent deployment
tags: code, architecture, microservices, modularity
---

## Enforce One-to-One Correlation Between Codebase and Application

Each app must have exactly one codebase. Multiple codebases make a distributed system, each component its own app. If apps share code, factor it into libraries.

**Incorrect (multiple apps sharing one codebase):**

```text
my-monorepo/
├── frontend-app/
│   └── package.json  # App 1
├── backend-api/
│   └── package.json  # App 2
├── worker-service/
│   └── package.json  # App 3
└── shared/
    └── utils.js      # Shared code tightly coupled
# All three apps deployed together, can't scale independently
```

**Correct (separate codebases with shared libraries):**

```text
# Each app has its own repository
github.com/company/frontend-app     # App 1
github.com/company/backend-api      # App 2
github.com/company/worker-service   # App 3
github.com/company/shared-utils     # Published as npm/pip package

# package.json in frontend-app
{
  "dependencies": {
    "@company/shared-utils": "^2.1.0"
  }
}

# Each app can be deployed, scaled, and versioned independently
```

**When NOT to use this pattern:**
- Initial prototyping, while boundaries are unclear
- Monorepos acceptable if each app has independent build/deploy pipelines

Reference: [The Twelve-Factor App - Codebase](https://12factor.net/codebase)
