# Real API Examples (fp-ts TaskEither)

End-to-end wrappers for fetch, Prisma and Node file I/O. Imports assumed: `import { pipe } from 'fp-ts/function'`, `import * as T from 'fp-ts/Task'`, `import * as TE from 'fp-ts/TaskEither'`.

## Complete Fetch Wrapper

```typescript
// types.ts
interface ApiError {
  code: string
  message: string
  status: number
  details?: unknown
}

// api.ts
const createApiError = (
  code: string,
  message: string,
  status: number,
  details?: unknown
): ApiError => ({ code, message, status, details })

const request = <T>(
  url: string,
  options: RequestInit = {}
): TE.TaskEither<ApiError, T> =>
  TE.tryCatch(
    async () => {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw createApiError(
          body.code || 'HTTP_ERROR',
          body.message || response.statusText,
          response.status,
          body
        )
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return undefined as T
      }

      return response.json()
    },
    (error): ApiError => {
      if (typeof error === 'object' && error !== null && 'code' in error) {
        return error as ApiError
      }
      return createApiError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : 'Request failed',
        0
      )
    }
  )

// API client
const api = {
  get: <T>(url: string) => request<T>(url),

  post: <T>(url: string, body: unknown) =>
    request<T>(url, {
      method: 'POST',
      body: JSON.stringify(body)
    }),

  put: <T>(url: string, body: unknown) =>
    request<T>(url, {
      method: 'PUT',
      body: JSON.stringify(body)
    }),

  delete: (url: string) =>
    request<void>(url, { method: 'DELETE' }),
}

// Usage
const getUser = (id: string) => api.get<User>(`/api/users/${id}`)
const createUser = (data: CreateUserDto) => api.post<User>('/api/users', data)
const updateUser = (id: string, data: UpdateUserDto) => api.put<User>(`/api/users/${id}`, data)
const deleteUser = (id: string) => api.delete(`/api/users/${id}`)
```

## Database Operations (Prisma Example)

```typescript
import { PrismaClient, Prisma } from '@prisma/client'

type DbError =
  | { _tag: 'NotFound'; entity: string; id: string }
  | { _tag: 'UniqueViolation'; field: string }
  | { _tag: 'ConnectionError'; cause: unknown }

const prisma = new PrismaClient()

const wrapPrisma = <T>(
  operation: () => Promise<T>
): TE.TaskEither<DbError, T> =>
  TE.tryCatch(
    operation,
    (error): DbError => {
      if (error instanceof Prisma.PrismaClientKnownRequestError) {
        if (error.code === 'P2002') {
          const field = (error.meta?.target as string[])?.join(', ') || 'unknown'
          return { _tag: 'UniqueViolation', field }
        }
        if (error.code === 'P2025') {
          return { _tag: 'NotFound', entity: 'Record', id: 'unknown' }
        }
      }
      return { _tag: 'ConnectionError', cause: error }
    }
  )

// Repository pattern
const userRepository = {
  findById: (id: string): TE.TaskEither<DbError, User> =>
    pipe(
      wrapPrisma(() => prisma.user.findUnique({ where: { id } })),
      TE.flatMap(user =>
        user
          ? TE.right(user)
          : TE.left({ _tag: 'NotFound', entity: 'User', id })
      )
    ),

  findByEmail: (email: string): TE.TaskEither<DbError, User | null> =>
    wrapPrisma(() => prisma.user.findUnique({ where: { email } })),

  create: (data: CreateUserInput): TE.TaskEither<DbError, User> =>
    wrapPrisma(() => prisma.user.create({ data })),

  update: (id: string, data: UpdateUserInput): TE.TaskEither<DbError, User> =>
    wrapPrisma(() => prisma.user.update({ where: { id }, data })),

  delete: (id: string): TE.TaskEither<DbError, void> =>
    pipe(
      wrapPrisma(() => prisma.user.delete({ where: { id } })),
      TE.map(() => undefined)
    ),
}

// Service using repository
const createUserService = (input: CreateUserInput) =>
  pipe(
    // Check email doesn't exist
    userRepository.findByEmail(input.email),
    TE.flatMap(existing =>
      existing
        ? TE.left({ _tag: 'UniqueViolation' as const, field: 'email' })
        : TE.right(undefined)
    ),
    // Create user
    TE.flatMap(() => userRepository.create(input))
  )
```

## File Operations (Node.js)

```typescript
import * as fs from 'fs/promises'
import * as path from 'path'

type FileError =
  | { _tag: 'NotFound'; path: string }
  | { _tag: 'PermissionDenied'; path: string }
  | { _tag: 'IoError'; cause: unknown }

const toFileError = (error: unknown, filePath: string): FileError => {
  if (error instanceof Error) {
    if ('code' in error) {
      if (error.code === 'ENOENT') return { _tag: 'NotFound', path: filePath }
      if (error.code === 'EACCES') return { _tag: 'PermissionDenied', path: filePath }
    }
  }
  return { _tag: 'IoError', cause: error }
}

const readFile = (filePath: string): TE.TaskEither<FileError, string> =>
  TE.tryCatch(
    () => fs.readFile(filePath, 'utf-8'),
    (e) => toFileError(e, filePath)
  )

const writeFile = (filePath: string, content: string): TE.TaskEither<FileError, void> =>
  TE.tryCatch(
    () => fs.writeFile(filePath, content, 'utf-8'),
    (e) => toFileError(e, filePath)
  )

const readJson = <T>(filePath: string): TE.TaskEither<FileError | { _tag: 'ParseError'; cause: unknown }, T> =>
  pipe(
    readFile(filePath),
    TE.flatMap(content =>
      TE.tryCatch(
        () => Promise.resolve(JSON.parse(content)),
        (e): { _tag: 'ParseError'; cause: unknown } => ({ _tag: 'ParseError', cause: e })
      )
    )
  )

// Usage: Load config with fallback
const loadConfig = () =>
  pipe(
    readJson<Config>('./config.json'),
    TE.orElse(() => readJson<Config>('./config.default.json')),
    TE.getOrElse(() => T.of(defaultConfig))
  )
```
