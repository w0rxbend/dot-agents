# Loading & Error States

**CRITICAL**: proper loading and error state handling prevents layout shift and improves UX.

---

## ⚠️ CRITICAL RULE: Never Use Early Returns

### The Problem

```typescript
// ❌ NEVER DO THIS - Early return with loading spinner
const Component = () => {
    const { data, isLoading } = useQuery();

    // WRONG: This causes layout shift and poor UX
    if (isLoading) {
        return <LoadingSpinner />;
    }

    return <Content data={data} />;
};
```

**Why this is bad:**
1. **Layout Shift**: content jumps when loading completes
2. **CLS (Cumulative Layout Shift)**: poor Core Web Vital score
3. **Jarring UX**: page structure changes suddenly
4. **Lost Scroll Position**: user loses place on page

### The Solutions

**Option 1: SuspenseLoader (PREFERRED for new components)**

```typescript
import { SuspenseLoader } from '~components/SuspenseLoader';

const HeavyComponent = React.lazy(() => import('./HeavyComponent'));

export const MyComponent: React.FC = () => {
    return (
        <SuspenseLoader>
            <HeavyComponent />
        </SuspenseLoader>
    );
};
```

**Option 2: LoadingOverlay (for legacy useQuery patterns)**

```typescript
import { LoadingOverlay } from '~components/LoadingOverlay';

export const MyComponent: React.FC = () => {
    const { data, isLoading } = useQuery({ ... });

    return (
        <LoadingOverlay loading={isLoading}>
            <Content data={data} />
        </LoadingOverlay>
    );
};
```

---

## SuspenseLoader Component

### What It Does

- Shows loading indicator while lazy components load
- Smooth fade-in animation
- Prevents layout shift
- Same loading experience across app

### Import

```typescript
import { SuspenseLoader } from '~components/SuspenseLoader';
// Or
import { SuspenseLoader } from '@/components/SuspenseLoader';
```

### With useSuspenseQuery

```typescript
import { useSuspenseQuery } from '@tanstack/react-query';
import { SuspenseLoader } from '~components/SuspenseLoader';

const Inner: React.FC = () => {
    // No isLoading needed!
    const { data } = useSuspenseQuery({
        queryKey: ['data'],
        queryFn: () => api.getData(),
    });

    return <Display data={data} />;
};

// Outer component wraps in Suspense
export const Outer: React.FC = () => {
    return (
        <SuspenseLoader>
            <Inner />
        </SuspenseLoader>
    );
};
```

### Multiple Suspense Boundaries

**Pattern**: separate loading per independent section

```typescript
export const Dashboard: React.FC = () => {
    return (
        <Box>
            <SuspenseLoader>
                <Header />
            </SuspenseLoader>

            <SuspenseLoader>
                <MainContent />
            </SuspenseLoader>

            <SuspenseLoader>
                <Sidebar />
            </SuspenseLoader>
        </Box>
    );
};
```

### Nested Suspense

```typescript
export const ParentComponent: React.FC = () => {
    return (
        <SuspenseLoader>
            {/* Parent suspends while loading */}
            <ParentContent>
                <SuspenseLoader>
                    {/* Nested suspense for child */}
                    <ChildComponent />
                </SuspenseLoader>
            </ParentContent>
        </SuspenseLoader>
    );
};
```

---

## LoadingOverlay Component

### When to Use

- Legacy components with `useQuery` (not yet refactored to Suspense)
- Overlay loading state needed
- Can't use Suspense boundaries

### Usage

```typescript
import React from 'react';
import { Box } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { LoadingOverlay } from '~components/LoadingOverlay';
import { myFeatureApi } from '../api/myFeatureApi';

export const LegacyComponent: React.FC<{ id: number }> = ({ id }) => {
    const { data, isLoading, error } = useQuery({
        queryKey: ['entity', id],
        queryFn: () => myFeatureApi.getEntity(id),
    });

    return (
        <LoadingOverlay loading={isLoading}>
            <Box sx={{ p: 2 }}>
                {error && <ErrorDisplay error={error} />}
                {data && <Content data={data} />}
            </Box>
        </LoadingOverlay>
    );
};
```

**What it does:**
- Shows semi-transparent overlay with spinner
- Reserves content area (no layout shift)
- Blocks interaction while loading

---

## Error Handling

### useMuiSnackbar Hook (REQUIRED)

**NEVER use react-toastify**. Project standard is MUI Snackbar.

```typescript
import { useMuiSnackbar } from '@/hooks/useMuiSnackbar';

export const MyComponent: React.FC = () => {
    const { showSuccess, showError, showInfo, showWarning } = useMuiSnackbar();

    const handleAction = async () => {
        try {
            await api.doSomething();
            showSuccess('Operation completed successfully');
        } catch (error) {
            showError('Operation failed');
        }
    };

    return <Button onClick={handleAction}>Do Action</Button>;
};
```

**Available Methods:**
- `showSuccess(message)` - green success message
- `showError(message)` - red error message
- `showWarning(message)` - orange warning message
- `showInfo(message)` - blue info message

### TanStack Query Errors

TanStack Query v5 has no `onError` option on `useQuery`/`useSuspenseQuery`. `useSuspenseQuery` throws to nearest error boundary, so render error there (see Error Boundaries below). For global notification on every failed query, use `new QueryCache({ onError })` when creating `QueryClient`. Mutations still accept `onError`:

```typescript
import { useMutation } from '@tanstack/react-query';
import { useMuiSnackbar } from '@/hooks/useMuiSnackbar';

export const SaveButton: React.FC = () => {
    const { showError } = useMuiSnackbar();

    const saveMutation = useMutation({
        mutationFn: () => api.save(),
        onError: (error) => {
            showError('Failed to save');
            console.error('Mutation error:', error);
        },
    });

    return <Button onClick={() => saveMutation.mutate()}>Save</Button>;
};
```

### Error Boundaries

```typescript
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }) {
    return (
        <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant='h5' color='error'>
                Something went wrong
            </Typography>
            <Typography>{error.message}</Typography>
            <Button onClick={resetErrorBoundary}>Try Again</Button>
        </Box>
    );
}

export const MyPage: React.FC = () => {
    return (
        <ErrorBoundary
            FallbackComponent={ErrorFallback}
            onError={(error) => console.error('Boundary caught:', error)}
        >
            <SuspenseLoader>
                <ComponentThatMightError />
            </SuspenseLoader>
        </ErrorBoundary>
    );
};
```

---

## Loading State Anti-Patterns

### ❌ What NOT to Do

```typescript
// ❌ NEVER - Early return
if (isLoading) {
    return <CircularProgress />;
}

// ❌ NEVER - Conditional rendering
{isLoading ? <Spinner /> : <Content />}

// ❌ NEVER - Layout changes
if (isLoading) {
    return (
        <Box sx={{ height: 100 }}>
            <Spinner />
        </Box>
    );
}
return (
    <Box sx={{ height: 500 }}>  // Different height!
        <Content />
    </Box>
);
```

### ✅ What TO Do

```typescript
// ✅ BEST - useSuspenseQuery + SuspenseLoader
<SuspenseLoader>
    <ComponentWithSuspenseQuery />
</SuspenseLoader>

// ✅ ACCEPTABLE - LoadingOverlay
<LoadingOverlay loading={isLoading}>
    <Content />
</LoadingOverlay>

// ✅ OK - Inline skeleton with same layout
<Box sx={{ height: 500 }}>
    {isLoading ? <Skeleton variant='rectangular' height='100%' /> : <Content />}
</Box>
```

---

## Skeleton Loading (Alternative)

### MUI Skeleton Component

```typescript
import { Skeleton, Box } from '@mui/material';

export const MyComponent: React.FC = () => {
    const { data, isLoading } = useQuery({ ... });

    return (
        <Box sx={{ p: 2 }}>
            {isLoading ? (
                <>
                    <Skeleton variant='text' width={200} height={40} />
                    <Skeleton variant='rectangular' width='100%' height={200} />
                    <Skeleton variant='text' width='100%' />
                </>
            ) : (
                <>
                    <Typography variant='h5'>{data.title}</Typography>
                    <img src={data.image} />
                    <Typography>{data.description}</Typography>
                </>
            )}
        </Box>
    );
};
```

**Key**: skeleton must have **same layout** as real content (no shift)

---

**See Also:**
- [component-patterns.md](component-patterns.md) - Suspense integration
- [data-fetching.md](data-fetching.md) - useSuspenseQuery details
