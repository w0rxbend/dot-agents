# File Organization

## features/ vs components/ Distinction

### features/ Directory

**Purpose**: domain-specific features with own logic, API, components, custom hooks/utilities

**Examples:**
- `features/posts/` - Project catalog/post management
- `features/forms/` - Form builder and rendering
- `features/auth/` - Authentication flows

### components/ Directory

**Purpose**: truly reusable components shared by multiple features

**When to use:** component used in 3+ places, generic (no feature-specific logic), UI primitive or pattern.

**Examples:**
- `components/SuspenseLoader/` - Loading wrapper
- `components/CustomAppBar/` - Application header
- `components/ErrorBoundary/` - Error handling
- `components/LoadingOverlay/` - Loading overlay

**Structure:**
```
components/
  SuspenseLoader/
    SuspenseLoader.tsx
    SuspenseLoader.test.tsx
  CustomAppBar/
    CustomAppBar.tsx
    CustomAppBar.test.tsx
```

---

## Feature Directory Structure (Detailed)

### Complete Feature Example

Based on `features/posts/`:

```
features/
  posts/
    api/
      postApi.ts              # API service layer (GET, POST, PUT, DELETE)

    components/
      PostTable.tsx           # Main container component
      grids/
        PostDataGrid/
          PostDataGrid.tsx
      drawers/
        ProjectPostDrawer/
          ProjectPostDrawer.tsx
      cells/
        editors/
          TextEditCell.tsx
        renderers/
          DateCell.tsx
      toolbar/
        CustomToolbar.tsx

    hooks/
      usePostQueries.ts       # Regular queries
      useSuspensePost.ts      # Suspense queries
      usePostMutations.ts     # Mutations
      useGridLayout.ts              # Feature-specific hooks

    helpers/
      postHelpers.ts          # Utility functions
      validation.ts                 # Validation logic

    types/
      index.ts                      # TypeScript types/interfaces

    queries/
      postQueries.ts          # Query key factories (optional)

    context/
      PostContext.tsx         # React context (if needed)

    index.ts                        # Public API exports
```

### Subdirectory Guidelines

#### api/ Directory

**Purpose**: centralized API calls for feature

**Files:**
- `{feature}Api.ts` - main API service

**Pattern:**
```typescript
// features/my-feature/api/myFeatureApi.ts
import apiClient from '@/lib/apiClient';

export const myFeatureApi = {
    getItem: async (id: number) => {
        const { data } = await apiClient.get(`/blog/items/${id}`);
        return data;
    },
    createItem: async (payload) => {
        const { data } = await apiClient.post('/blog/items', payload);
        return data;
    },
};
```

#### components/ Directory

**Purpose**: feature-specific components

**Organization:**
- Flat structure if <5 components
- Subdirectories by responsibility if >5 components

**Examples:**
```
components/
  MyFeatureMain.tsx           # Main component
  MyFeatureHeader.tsx         # Supporting components
  MyFeatureFooter.tsx

  # OR with subdirectories:
  containers/
    MyFeatureContainer.tsx
  presentational/
    MyFeatureDisplay.tsx
  blogs/
    MyFeatureForm.tsx
```

#### hooks/ Directory

**Purpose**: custom hooks for feature

**Examples:**
```
hooks/
  useMyFeature.ts               # Main hook
  useSuspenseMyFeature.ts       # Suspense version
  useMyFeatureMutations.ts      # Mutations
  useMyFeatureFilters.ts        # Filters/search
```

#### helpers/ Directory

**Purpose**: feature-specific utility functions

**Examples:**
```
helpers/
  myFeatureHelpers.ts           # General utilities
  validation.ts                 # Validation logic
  transformers.ts               # Data transformations
  constants.ts                  # Constants
```

#### types/ Directory

**Purpose**: TypeScript types and interfaces

**Files:**
```
types/
  index.ts                      # Main types, exported
  internal.ts                   # Internal types (not exported)
```

---

## Import Aliases (Vite Configuration)

### Available Aliases

From `vite.config.ts` lines 180-185:

| Alias | Resolves To | Use For |
|-------|-------------|---------|
| `@/` | `src/` | Absolute imports from src root |
| `~types` | `src/types` | Shared TypeScript types |
| `~components` | `src/components` | Reusable components |
| `~features` | `src/features` | Feature imports |

### Usage Examples

```typescript
// ✅ PREFERRED - Use aliases for absolute imports
import { apiClient } from '@/lib/apiClient';
import { SuspenseLoader } from '~components/SuspenseLoader';
import { postApi } from '~features/posts/api/postApi';
import type { User } from '~types/user';

// ❌ AVOID - Relative paths from deep nesting
import { apiClient } from '../../../lib/apiClient';
import { SuspenseLoader } from '../../../components/SuspenseLoader';
```

### When to Use Which Alias

**@/ (General)**:
- Lib utilities: `@/lib/apiClient`
- Hooks: `@/hooks/useAuth`
- Config: `@/config/theme`
- Shared services: `@/services/authService`

---

## File Naming Conventions

### Components

**Pattern**: PascalCase, `.tsx` extension

```
MyComponent.tsx
PostDataGrid.tsx
CustomAppBar.tsx
```

**Avoid:**
- camelCase: `myComponent.tsx` ❌
- kebab-case: `my-component.tsx` ❌
- All caps: `MYCOMPONENT.tsx` ❌

### Hooks

**Pattern**: camelCase, `use` prefix, `.ts` extension

```
useMyFeature.ts
useSuspensePost.ts
useAuth.ts
useGridLayout.ts
```

### API Services

**Pattern**: camelCase, `Api` suffix, `.ts` extension

```
myFeatureApi.ts
postApi.ts
userApi.ts
```

### Helpers/Utilities

**Pattern**: camelCase, descriptive name, `.ts` extension

### Types

**Pattern**: camelCase, `index.ts` or descriptive name

```
types/index.ts
types/post.ts
types/user.ts
```

---

## When to Create a New Feature

### Create New Feature When:

- Multiple related components (>3)
- Own API endpoints
- Domain-specific logic
- Will grow over time
- Reused across multiple routes

**Example:** `features/posts/`
- 20+ components
- Own API service
- Complex state management
- Used in multiple routes

### Add to Existing Feature When:

- Related to existing feature
- Shares same API
- Logically grouped
- Extends existing functionality

**Example:** adding export dialog to posts feature

### Create Reusable Component When:

- Used across 3+ features
- Generic, no domain logic
- Pure presentation
- Shared pattern

**Example:** `components/SuspenseLoader/`

---

## Import Organization

### Import Order (Recommended)

```typescript
// 1. React and React-related
import React, { useState, useCallback, useMemo } from 'react';
import { lazy } from 'react';

// 2. Third-party libraries (alphabetical)
import { Box, Paper, Button, Grid } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';
import { useSuspenseQuery, useQueryClient } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

// 3. Alias imports (@ first, then ~)
import { apiClient } from '@/lib/apiClient';
import { useAuth } from '@/hooks/useAuth';
import { useMuiSnackbar } from '@/hooks/useMuiSnackbar';
import { SuspenseLoader } from '~components/SuspenseLoader';
import { postApi } from '~features/posts/api/postApi';

// 4. Type imports (grouped)
import type { Post } from '~types/post';
import type { User } from '~types/user';

// 5. Relative imports (same feature)
import { MySubComponent } from './MySubComponent';
import { useMyFeature } from '../hooks/useMyFeature';
import { myFeatureHelpers } from '../helpers/myFeatureHelpers';
```

**Use single quotes** for all imports (project standard)

---

## Public API Pattern

### feature/index.ts

Export feature public API for clean imports:

```typescript
// features/my-feature/index.ts

// Export main components
export { MyFeatureMain } from './components/MyFeatureMain';
export { MyFeatureHeader } from './components/MyFeatureHeader';

// Export hooks
export { useMyFeature } from './hooks/useMyFeature';
export { useSuspenseMyFeature } from './hooks/useSuspenseMyFeature';

// Export API
export { myFeatureApi } from './api/myFeatureApi';

// Export types
export type { MyFeatureData, MyFeatureConfig } from './types';
```

**Usage:**
```typescript
// ✅ Clean import from feature index
import { MyFeatureMain, useMyFeature } from '~features/my-feature';

// ❌ Avoid deep imports (but OK if needed)
import { MyFeatureMain } from '~features/my-feature/components/MyFeatureMain';
```

---

## Directory Structure Visualization

```
src/
├── features/                    # Domain-specific features
│   ├── posts/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── helpers/
│   │   ├── types/
│   │   └── index.ts
│   ├── blogs/
│   └── auth/
│
├── components/                  # Reusable components
│   ├── SuspenseLoader/
│   ├── CustomAppBar/
│   ├── ErrorBoundary/
│   └── LoadingOverlay/
│
├── routes/                      # TanStack Router routes
│   ├── __root.tsx
│   ├── index.tsx
│   ├── project-catalog/
│   │   ├── index.tsx
│   │   └── create/
│   └── blogs/
│
├── hooks/                       # Shared hooks
│   ├── useAuth.ts
│   ├── useMuiSnackbar.ts
│   └── useDebounce.ts
│
├── lib/                         # Shared utilities
│   ├── apiClient.ts
│   └── utils.ts
│
├── types/                       # Shared TypeScript types
│   ├── user.ts
│   ├── post.ts
│   └── common.ts
│
├── config/                      # Configuration
│   └── theme.ts
│
└── App.tsx                      # Root component
```

---

**See Also:**
- [component-patterns.md](component-patterns.md) - Component structure
- [data-fetching.md](data-fetching.md) - API service patterns
- [complete-examples.md](complete-examples.md) - Full feature example
