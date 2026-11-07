---
name: building-tables
description: Builds tables and data grids for displaying tabular information, from simple HTML tables to complex enterprise data grids. Use when creating tables, implementing sorting/filtering/pagination, handling large datasets (10-1M+ rows), building spreadsheet-like interfaces, or designing data-heavy components. Provides performance optimization strategies, accessibility patterns (WCAG/ARIA), responsive designs, and library recommendations (TanStack Table, AG Grid).
---

# Building Tables & Data Grids

## When to Use

Use when:
- Creating tables, data grids or spreadsheet-like interfaces
- Displaying tabular or structured data
- Implementing sorting, filtering or pagination
- Handling large datasets or performance concerns
- Building inline editing or data entry interfaces
- Needing row selection or bulk operations
- Implementing data export (CSV, Excel, PDF)
- Ensuring table accessibility or responsive behavior

## Quick Decision Framework

Pick tier by data volume:

```
<100 rows        → Simple HTML table with progressive enhancement
100-1,000 rows   → Client-side features (sort, filter, paginate)
1,000-10,000     → Server-side operations with API pagination
10,000-100,000   → Virtual scrolling with windowing
>100,000 rows    → Enterprise grid with streaming and workers
```

Detailed selection criteria: `references/selection-framework.md`.

## Core Implementation Patterns

### Tier 1: Basic Tables (<100 rows)

Simple, read-only data display:
- Use semantic HTML `<table>` structure
- Responsive behavior via CSS
- Client-side sorting if needed
- Patterns: `references/basic-tables.md`

Example: `examples/simple-responsive-table.tsx`

### Tier 2: Interactive Tables (100-10K rows)

Feature-rich interactions:
- Filtering, pagination, selection
- Inline or modal editing
- Client-side operations up to 1K rows
- Switch to server-side beyond 1K rows
- Reference `references/interactive-tables.md`

Example: `examples/sortable-filtered-table.tsx`

### Tier 3: Advanced Grids (10K+ rows)

Massive datasets:
- Virtual scrolling
- Server-side aggregation
- Grouping and hierarchies
- Consider enterprise solutions
- Reference `references/advanced-grids.md`

Example: `examples/virtual-scrolling-grid.tsx`

## Performance Optimization

Critical thresholds:
- Client-side operations: <1,000 rows (instant, <50ms)
- Server-side operations: 1,000-10,000 rows (<200ms API)
- Virtual scrolling: 10,000+ rows (60fps, constant memory)
- Streaming: 100,000+ rows (progressive rendering)

Benchmark:
```bash
# Generate test data
python scripts/generate_mock_data.py --rows 10000

# Time in-memory sort/filter/search for given sizes (Node.js; not DOM rendering)
node scripts/analyze_performance.js --rows 1000,10000,100000
```

Rendering and scroll performance measurable only in browser (DevTools Performance panel, React Profiler).

Optimization strategies: `references/performance-optimization.md`.

## Feature Implementation

### Sorting
- Single or multi-column sorting
- Custom sort logic (numeric, date, natural)
- Visual indicators, keyboard support
- Reference `references/sorting-filtering.md`

### Filtering & Search
- Column-specific filters (text, range, select)
- Global search across all columns
- Advanced filter logic (AND/OR)
- Reference `references/sorting-filtering.md`

### Pagination
- Client-side for small datasets
- Server-side for large datasets
- Infinite scroll alternative
- Reference `references/pagination-strategies.md`

### Selection & Bulk Actions
- Single or multi-row selection
- Range selection (Shift+click)
- Bulk operations toolbar
- Reference `references/selection-patterns.md`

### Inline Editing
- Cell-level or row-level editing
- Validation and error handling
- Optimistic updates
- Reference `references/editing-patterns.md`

### Export
- CSV, Excel, PDF formats
- Preserve formatting and encoding
- Stream large exports
- Run `scripts/export_table_data.py`

## Accessibility Requirements

Essential WCAG compliance:
- Semantic HTML, proper structure
- ARIA grid pattern for interactive tables
- Full keyboard navigation
- Screen reader announcements

Check table markup with static heuristics (caption, headers, `scope`, ARIA roles). Contrast, focus and keyboard behaviour still need browser check with axe or Lighthouse:
```bash
node scripts/validate_accessibility.js path/to/table.html
```

Full requirements: `references/accessibility-patterns.md`.

## Responsive Design

Four strategies:
1. **Horizontal scroll** - Simple, preserves structure
2. **Card stack** - Rows become cards on mobile
3. **Priority columns** - Hide less important columns
4. **Truncate & expand** - Compact, details on demand

Implementations: `examples/responsive-patterns.tsx`.
Details: `references/responsive-strategies.md`.

## Library Recommendations

### Primary: TanStack Table (Headless)
Best for custom designs, full control:
- TypeScript-first
- Small bundle (~15KB)
- Framework agnostic
- Virtual scrolling support

```bash
npm install @tanstack/react-table
```

Setup: `examples/tanstack-basic.tsx`.

### Enterprise: AG Grid
Best for feature-complete solutions:
- Handles millions of rows
- Built-in advanced features
- Community (free) + Enterprise (paid)
- Excel-like user experience

```bash
npm install ag-grid-react
```

Setup: `examples/ag-grid-enterprise.tsx`.

Detailed comparison: `references/library-comparison.md`.

## Design Token Integration

Theme tables consistently with design tokens (CSS custom properties):
- Color tokens: backgrounds, borders, states
- Spacing tokens: cell padding
- Typography tokens: text styling
- Shadow tokens: elevation

Supports light, dark, high-contrast and custom themes.
Token system and theme switching: theming-components skill.

## Working Examples

Start from example matching requirements:

```
examples/simple-responsive-table.tsx   # Basic HTML table
examples/basic-sortable-table.tsx      # Client-side sorting
examples/sortable-filtered-table.tsx   # Sorting and filtering
examples/tanstack-basic.tsx            # TanStack Table setup
examples/paginated-table.tsx           # Pagination
examples/server-side-sorting.tsx       # Server-side sorting
examples/virtual-scrolling.tsx         # Virtualized rows
examples/virtual-scrolling-grid.tsx    # High-performance grid for 100K+ rows
examples/editable-cells.tsx            # Inline editing
examples/table-state-persistence.tsx   # Persisting sort/filter/column state
examples/responsive-patterns.tsx       # Responsive layouts
examples/ag-grid-enterprise.tsx        # AG Grid with grouping and aggregation
```

## Testing Tools

Generate test data:
```bash
python scripts/generate_mock_data.py --rows 100000 --columns 20
```

## Next Steps

1. Determine data volume and feature requirements
2. Pick implementation tier
3. Choose TanStack Table (flexibility) or AG Grid (features)
4. Start from matching example file
5. Add core features progressively
6. Test performance and accessibility
7. Apply responsive strategy for mobile
