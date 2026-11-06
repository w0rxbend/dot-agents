---
title: Factor Shared Code Into Libraries Managed by Dependency Manager
impact: HIGH
impactDescription: enables code reuse without coupling, allows independent versioning
tags: code, libraries, dependencies, modularity
---

## Factor Shared Code Into Libraries Managed by Dependency Manager

If multiple apps need same functionality, extract it into library pulled in via dependency manager. Keeps one-codebase-per-app rule and allows reuse.

**Incorrect (copy-pasting shared code):**

```text
# Duplicated code across apps
app-1/
├── src/
│   ├── utils/
│   │   └── validation.js  # Copy-pasted
│   └── index.js
app-2/
├── src/
│   ├── utils/
│   │   └── validation.js  # Same code, may drift
│   └── index.js
# Bug fixes must be applied in multiple places
```

**Correct (shared library via package manager):**

```text
# Shared library published to package registry
@company/validation/
├── package.json
│   {
│     "name": "@company/validation",
│     "version": "1.3.0"
│   }
├── src/
│   └── index.js
└── README.md
```

```json
// app-1/package.json
{
  "name": "app-1",
  "dependencies": {
    "@company/validation": "^1.3.0"
  }
}
```

```javascript
// Both apps import from the library
import { validateEmail, validatePhone } from '@company/validation';
```

Reference: [The Twelve-Factor App - Codebase](https://12factor.net/codebase)
