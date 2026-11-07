---
name: backend-dev-guidelines
description: "Implement Node.js/Express/TypeScript service routes, validation, data access, and errors using the repository's architecture. The bundled BaseController, Prisma, Zod, and Sentry patterns are examples, not defaults for other backends."
---

# Backend Development Guidelines

## Purpose

Use Node.js/Express/TypeScript patterns that match repository. Referenced BaseController, unifiedConfig, Prisma, Sentry and Zod arrangements are examples from one service architecture. Preserve existing FastAPI, Tapir, Go and other backend conventions.

Resource files quote code from one sample codebase (paths like `blog-api/` and `form/`, an `SSOMiddleware` auth client). Treat those names as placeholders. Map them to equivalent service, auth middleware and config module in current repository. Do not create them.

## When to Use This Skill

Use for Node.js/Express/TypeScript service work:
- Create or modify routes, endpoints, APIs
- Build controllers, services, repositories
- Add middleware (auth, validation, error handling)
- Prisma database operations
- Sentry error tracking
- Zod input validation
- Configuration management
- Backend testing and refactoring

---

## Quick Start

### New Backend Feature Checklist

- [ ] **Route**: Clean definition; delegate to controller
- [ ] **Controller**: Extend BaseController
- [ ] **Service**: Business logic with DI
- [ ] **Repository**: Database access (if complex)
- [ ] **Validation**: Zod schema
- [ ] **Sentry**: Error tracking
- [ ] **Tests**: Unit + integration tests
- [ ] **Config**: Use unifiedConfig

### New Microservice Checklist

- [ ] Directory structure (see [architecture-overview.md](resources/architecture-overview.md))
- [ ] instrument.ts for Sentry
- [ ] unifiedConfig setup
- [ ] BaseController class
- [ ] Middleware stack
- [ ] Error boundary
- [ ] Testing framework

---

## Architecture Overview

### Layered Architecture

```
HTTP Request
    ↓
Routes (routing only)
    ↓
Controllers (request handling)
    ↓
Services (business logic)
    ↓
Repositories (data access)
    ↓
Database (Prisma)
```

**Key Principle:** Each layer has ONE responsibility.

Full details: [architecture-overview.md](resources/architecture-overview.md).

---

## Directory Structure

```
service/src/
├── config/              # UnifiedConfig
├── controllers/         # Request handlers
├── services/            # Business logic
├── repositories/        # Data access
├── routes/              # Route definitions
├── middleware/          # Express middleware
├── types/               # TypeScript types
├── validators/          # Zod schemas
├── utils/               # Utilities
├── tests/               # Tests
├── instrument.ts        # Sentry (FIRST IMPORT)
├── app.ts               # Express setup
└── server.ts            # HTTP server
```

**Naming Conventions:**
- Controllers: `PascalCase` - `UserController.ts`
- Services: `camelCase` - `userService.ts`
- Routes: `camelCase + Routes` - `userRoutes.ts`
- Repositories: `PascalCase + Repository` - `UserRepository.ts`

---

## Core Principles (7 Key Rules)

### 1. Routes Only Route, Controllers Control

```typescript
// ❌ NEVER: Business logic in routes
router.post('/submit', async (req, res) => {
    // 200 lines of logic
});

// ✅ ALWAYS: Delegate to controller
router.post('/submit', (req, res) => controller.submit(req, res));
```

### 2. All Controllers Extend BaseController

```typescript
export class UserController extends BaseController {
    async getUser(req: Request, res: Response): Promise<void> {
        try {
            const user = await this.userService.findById(req.params.id);
            this.handleSuccess(res, user);
        } catch (error) {
            this.handleError(error, res, 'getUser');
        }
    }
}
```

### 3. All Errors to Sentry

```typescript
try {
    await operation();
} catch (error) {
    Sentry.captureException(error);
    throw error;
}
```

Never console.log instead of Sentry.

### 4. Use unifiedConfig, NEVER process.env

```typescript
// ❌ NEVER
const timeout = process.env.TIMEOUT_MS;

// ✅ ALWAYS
import { config } from './config/unifiedConfig';
const timeout = config.timeouts.default;
```

### 5. Validate All Input with Zod

```typescript
const schema = z.object({ email: z.string().email() });
const validated = schema.parse(req.body);
```

### 6. Use Repository Pattern for Data Access

```typescript
// Service → Repository → Database
const users = await userRepository.findActive();
```

### 7. Comprehensive Testing Required

```typescript
describe('UserService', () => {
    it('should create user', async () => {
        expect(user).toBeDefined();
    });
});
```

---

## Common Imports

```typescript
// Express
import express, { Request, Response, NextFunction, Router } from 'express';

// Validation
import { z } from 'zod';

// Database
import { PrismaClient } from '@prisma/client';
import type { Prisma } from '@prisma/client';

// Sentry
import * as Sentry from '@sentry/node';

// Config
import { config } from './config/unifiedConfig';

// Middleware
import { authMiddleware } from './middleware/auth'; // your project's auth middleware
import { asyncErrorWrapper } from './middleware/errorBoundary';
```

---

## Quick Reference

HTTP status codes: see [routing-and-controllers.md](resources/routing-and-controllers.md).

### Service Templates

Use most mature existing service in repository as template for new routes and services. If none exists, start from [complete-examples.md](resources/complete-examples.md).

---

## Navigation Guide

| Need to... | Read this |
|------------|-----------|
| Understand architecture (layers, request lifecycle, separation of concerns) | [architecture-overview.md](resources/architecture-overview.md) |
| Create routes/controllers (BaseController, error handling, examples) | [routing-and-controllers.md](resources/routing-and-controllers.md) |
| Organize business logic (service patterns, DI, repository pattern, caching) | [services-and-repositories.md](resources/services-and-repositories.md) |
| Validate input (Zod schemas, DTO pattern) | [validation-patterns.md](resources/validation-patterns.md) |
| Add error tracking (Sentry init, error capture, performance monitoring) | [sentry-and-monitoring.md](resources/sentry-and-monitoring.md) |
| Create middleware (auth, audit, error boundaries, AsyncLocalStorage) | [middleware-guide.md](resources/middleware-guide.md) |
| Database access (PrismaService, repositories, transactions, optimization) | [database-patterns.md](resources/database-patterns.md) |
| Manage config (UnifiedConfig, environment configs, secrets) | [configuration.md](resources/configuration.md) |
| Handle async/errors (custom errors, asyncErrorWrapper) | [async-and-errors.md](resources/async-and-errors.md) |
| Write tests (unit/integration, mocking, coverage) | [testing-guide.md](resources/testing-guide.md) |
| See examples (full examples, refactoring guide) | [complete-examples.md](resources/complete-examples.md) |

---

## Related Skills

- **backend-patterns** - Framework-neutral backend patterns (caching, queues, rate limiting)
- **observability-and-instrumentation** - Logging, metrics, tracing and error tracking
- **using-relational-databases** - Schema, migrations and ORM usage beyond Prisma basics
