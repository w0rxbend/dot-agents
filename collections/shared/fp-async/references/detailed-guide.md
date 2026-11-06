# Practical Async Patterns with fp-ts - Detailed Guide

## 1. Wrapping Promises Safely

### Wrap Once, Handle Cleanly

`TE.tryCatch` takes two args: (1) async function that might throw, (2) function converting thrown value into your error type.

```typescript
import * as TE from 'fp-ts/TaskEither'
import * as E from 'fp-ts/Either'
import { pipe } from 'fp-ts/function'

// One wrapper function - reuse everywhere
const fetchJson = <T>(url: string): TE.TaskEither<Error, T> =>
  TE.tryCatch(
    async () => {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      return response.json()
    },
    (error) => error instanceof Error ? error : new Error(String(error))
  )

// AFTER: Clean and composable
const getUser = (userId: string) => fetchJson<User>(`/api/users/${userId}`)
const getPosts = (userId: string) => fetchJson<Post[]>(`/api/users/${userId}/posts`)
```

### Creating Success and Failure Values

```typescript
// Wrap a value as success
const success = TE.right<Error, number>(42)

// Wrap a value as failure
const failure = TE.left<Error, number>(new Error('Nope'))

// From a nullable value (null/undefined becomes error)
const fromNullable = TE.fromNullable(new Error('Value was null'))
const result = fromNullable(maybeUser) // TaskEither<Error, User>

// From a condition
const mustBePositive = TE.fromPredicate(
  (n: number) => n > 0,
  (n) => new Error(`Expected positive, got ${n}`)
)
```

---


## 2. Chaining Async Operations

### flatMap vs map

Use `map` when transformation is sync and cannot fail:

```typescript
pipe(
  fetchUser(userId),
  TE.map(user => user.name.toUpperCase())  // Just transforms the value
)
```

Use `flatMap` when transformation is async or can fail (`chain` is legacy alias found in pre-2.14 code):

```typescript
pipe(
  fetchUser(userId),
  TE.flatMap(user => fetchOrders(user.id))  // Returns another TaskEither
)
```

### Building Context with Do Notation

For values from multiple steps:

```typescript
// BEFORE: Have to thread values through manually
const processOrderManual = (orderId: string) =>
  pipe(
    fetchOrder(orderId),
    TE.flatMap(order =>
      pipe(
        fetchUser(order.userId),
        TE.flatMap(user =>
          pipe(
            chargePayment(user, order.total),
            TE.map(payment => ({ order, user, payment }))
          )
        )
      )
    )
  )

// AFTER: Do notation keeps everything accessible
const processOrder = (orderId: string) =>
  pipe(
    TE.Do,
    TE.bind('order', () => fetchOrder(orderId)),
    TE.bind('user', ({ order }) => fetchUser(order.userId)),
    TE.bind('payment', ({ user, order }) => chargePayment(user, order.total)),
    TE.bind('shipment', ({ order, user }) => createShipment(order, user)),
    TE.map(({ order, payment, shipment }) => ({
      orderId: order.id,
      paymentId: payment.id,
      trackingNumber: shipment.tracking
    }))
  )
```

---


## 3. Parallel vs Sequential Execution

### When to Use Each

**Sequential** (one after another):
- Each operation depends on previous result
- Rate limits must be respected
- Order matters

**Parallel** (all at once):
- Operations are independent
- Speed matters
- Fetching multiple resources by ID

### Sequential Chaining

```typescript
// Operations depend on each other - must be sequential
const getUserWithOrg = (userId: string) =>
  pipe(
    fetchUser(userId),                              // First: get user
    TE.flatMap(user => fetchTeam(user.teamId)),      // Then: get their team
    TE.flatMap(team => fetchOrganization(team.orgId)) // Finally: get org
  )
```

### Parallel Execution

```typescript
import { sequenceT } from 'fp-ts/Apply'

// Independent operations - run in parallel
const getDashboardData = (userId: string) =>
  sequenceT(TE.ApplyPar)(
    fetchUser(userId),
    fetchNotifications(userId),
    fetchRecentActivity(userId)
  ) // Returns TaskEither<Error, [User, Notification[], Activity[]]>

// With destructuring:
const getDashboard = (userId: string) =>
  pipe(
    sequenceT(TE.ApplyPar)(
      fetchUser(userId),
      fetchNotifications(userId),
      fetchRecentActivity(userId)
    ),
    TE.map(([user, notifications, activities]) => ({
      user,
      notifications,
      activities,
      unreadCount: notifications.filter(n => !n.read).length
    }))
  )
```

### Parallel Array Operations

```typescript
// Fetch multiple users in parallel
const userIds = ['1', '2', '3', '4', '5']

// TE.traverseArray runs all fetches in parallel
const fetchAllUsers = pipe(
  userIds,
  TE.traverseArray(fetchUser)
) // TaskEither<Error, readonly User[]>

// Note: Fails fast - if ANY request fails, the whole thing fails
// All errors after the first are lost
```

### Parallel with Batch Control

To limit concurrent requests:

```typescript
const chunk = <T>(arr: T[], size: number): T[][] => {
  const chunks: T[][] = []
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size))
  }
  return chunks
}

// Process in batches of 5 concurrent requests
const fetchUsersWithLimit = (userIds: string[]) => {
  const batches = chunk(userIds, 5)

  return pipe(
    batches,
    // Process batches sequentially (traverseSeqArray; traverseArray would start every batch at once)
    TE.traverseSeqArray(batch =>
      // But within each batch, run in parallel
      pipe(batch, TE.traverseArray(fetchUser))
    ),
    TE.map(results => results.flat())
  )
}
```

### Sequential When Parallel Looks Tempting

```typescript
// WRONG: This looks parallel but order might matter for DB operations
const createUserAndProfile = (userData: UserData) =>
  sequenceT(TE.ApplyPar)(
    createUser(userData),           // Creates user with ID
    createProfile(userData.profile) // Needs user ID - race condition!
  )

// RIGHT: Sequential when there's a dependency
const createUserAndProfile = (userData: UserData) =>
  pipe(
    createUser(userData),
    TE.flatMap(user =>
      pipe(
        createProfile(user.id, userData.profile),
        TE.map(profile => ({ user, profile }))
      )
    )
  )
```

---


## 4. Error Recovery Patterns

### Fallback to Alternative

```typescript
// Try primary API, fall back to cache
const getUserWithFallback = (userId: string) =>
  pipe(
    fetchUserFromApi(userId),
    TE.orElse(() => fetchUserFromCache(userId))
  )

// Chain multiple fallbacks
const getConfigRobust = () =>
  pipe(
    fetchRemoteConfig(),
    TE.orElse(() => loadLocalConfig()),
    TE.orElse(() => TE.right(defaultConfig))
  )
```

### Typed Error Recovery

```typescript
type ApiError =
  | { _tag: 'NotFound'; id: string }
  | { _tag: 'NetworkError'; cause: Error }
  | { _tag: 'Unauthorized' }

const fetchUser = (id: string): TE.TaskEither<ApiError, User> =>
  TE.tryCatch(
    async () => {
      const res = await fetch(`/api/users/${id}`)
      if (res.status === 404) throw { _tag: 'NotFound', id }
      if (res.status === 401) throw { _tag: 'Unauthorized' }
      if (!res.ok) throw { _tag: 'NetworkError', cause: new Error(`HTTP ${res.status}`) }
      return res.json()
    },
    (e): ApiError =>
      typeof e === 'object' && e !== null && '_tag' in e
        ? e as ApiError
        : { _tag: 'NetworkError', cause: e instanceof Error ? e : new Error(String(e)) }
  )

// Handle specific errors differently
const getUserOrGuest = (userId: string) =>
  pipe(
    fetchUser(userId),
    TE.orElse(error => {
      switch (error._tag) {
        case 'NotFound':
          return TE.right(createGuestUser())
        case 'Unauthorized':
          return TE.left(error) // Propagate auth errors
        case 'NetworkError':
          return fetchUserFromCache(userId) // Try cache on network issues
      }
    })
  )
```

### Retry with Exponential Backoff

```typescript
import * as T from 'fp-ts/Task'

const wait = (ms: number): T.Task<void> =>
  () => new Promise(resolve => setTimeout(resolve, ms))

const retry = <E, A>(
  operation: TE.TaskEither<E, A>,
  maxAttempts: number,
  baseDelayMs: number = 1000
): TE.TaskEither<E, A> => {
  const attempt = (remaining: number, delay: number): TE.TaskEither<E, A> =>
    pipe(
      operation,
      TE.orElse(error =>
        remaining <= 1
          ? TE.left(error)
          : pipe(
              TE.fromTask(wait(delay)),
              TE.flatMap(() => attempt(remaining - 1, delay * 2))
            )
      )
    )

  return attempt(maxAttempts, baseDelayMs)
}

// Usage
const fetchUserWithRetry = (userId: string) =>
  retry(fetchUser(userId), 3, 1000)
  // Attempts: immediate, 1s, 2s delays between retries
```

### Default Values

```typescript
// Get value or use default (removes the error channel)
const getUsernameOrDefault = (userId: string) =>
  pipe(
    fetchUser(userId),
    TE.map(user => user.name),
    TE.getOrElse(() => T.of('Anonymous'))
  ) // Task<string> - no more error tracking

// Keep error channel but provide fallback value
const getUserWithDefault = (userId: string) =>
  pipe(
    fetchUser(userId),
    TE.orElse(() => TE.right(defaultUser))
  ) // TaskEither<Error, User> - error channel still exists but always succeeds
```

---


## 5. Handling Results

### Pattern Matching with fold/match

```typescript
// fold: Handle both success and failure, returns a Task (no more error channel)
const displayResult = pipe(
  fetchUser(userId),
  TE.fold(
    (error) => T.of(`Error: ${error.message}`),
    (user) => T.of(`Welcome, ${user.name}!`)
  )
) // Task<string>

// Execute and get the string
const message = await displayResult()
```

### Getting the Raw Either

```typescript
// Sometimes you need to work with the Either directly
const result = await fetchUser(userId)() // Either<Error, User>

if (E.isLeft(result)) {
  console.error('Failed:', result.left)
} else {
  console.log('User:', result.right)
}
```

### In Express/Hono Handlers

```typescript
// Express
app.get('/users/:id', async (req, res) => {
  const result = await pipe(
    fetchUser(req.params.id),
    TE.fold(
      (error) => T.of({ status: 500, body: { error: error.message } }),
      (user) => T.of({ status: 200, body: user })
    )
  )()

  res.status(result.status).json(result.body)
})

// Cleaner with a helper
const sendResult = <E, A>(
  res: Response,
  te: TE.TaskEither<E, A>,
  errorStatus: number = 500
) =>
  pipe(
    te,
    TE.fold(
      (error) => T.of(res.status(errorStatus).json({ error })),
      (data) => T.of(res.json(data))
    )
  )()

app.get('/users/:id', async (req, res) => {
  await sendResult(res, fetchUser(req.params.id), 404)
})
```

---


## 6. Common Patterns Reference

### Quick Transformations

```typescript
// Transform success value
TE.map(user => user.name)

// Transform error
TE.mapLeft(error => ({ ...error, timestamp: Date.now() }))

// Transform both at once
TE.bimap(
  error => enhanceError(error),
  user => user.profile
)
```

### Filtering

```typescript
// Fail if condition not met
pipe(
  fetchUser(userId),
  TE.filterOrElse(
    user => user.isActive,
    user => new Error(`User ${user.id} is not active`)
  )
)
```

### Side Effects Without Changing Value

```typescript
// Log on success, keep the value unchanged
pipe(
  fetchUser(userId),
  TE.tap(user => TE.fromIO(() => console.log(`Fetched user: ${user.id}`)))
)

// Log on error, keep the error unchanged
pipe(
  fetchUser(userId),
  TE.tapError(error => TE.fromIO(() => console.error(`Failed: ${error.message}`)))
)

// tap also accepts effects that can fail; the original value is kept
pipe(
  createUser(userData),
  TE.tap(user => sendWelcomeEmail(user.email))
) // Returns the created user, not the email result
```

### Converting From Other Types

```typescript
// From Either
const fromEither = TE.fromEither(E.right(42))

// From Option
import * as O from 'fp-ts/Option'
const fromOption = TE.fromOption(() => new Error('Value was None'))
const result = fromOption(O.some(42))

// From boolean
const fromBoolean = TE.fromPredicate(
  (x: number) => x > 0,
  () => new Error('Must be positive')
)
```
