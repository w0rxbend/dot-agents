---
name: implementing-search-filter
description: Implements search and filter interfaces for both frontend (React/TypeScript) and backend (Python) with debouncing, query management, and database integration. Use when adding search functionality, building filter UIs, implementing faceted search, or optimizing search performance.
---

# Search & Filter Implementation

## When to Use

- Product search with category and price filters
- Autocomplete/typeahead search
- Faceted search interfaces with dynamic counts
- Search in data tables or lists
- Advanced boolean search for power users
- Backend search with SQLAlchemy or Django ORM
- Elasticsearch for full-text search
- Search performance via debouncing and caching
- Accessible search experiences

## Core Components

### Frontend Search Patterns

**Search Input with Debouncing**
- 300ms debounce for performance
- Loading states during search
- Clear button (X) to reset
- Keyboard shortcuts (Cmd/Ctrl+K)
- See `references/search-input-patterns.md`

**Autocomplete/Typeahead**
- Suggestion dropdown with keyboard navigation
- Highlight matched text in suggestions
- Recent searches and popular items
- Debounce to prevent request flooding
- See `references/autocomplete-patterns.md`

**Filter UI Components**
- Checkbox filters for multi-select
- Range sliders for numeric values
- Dropdown filters for single selection
- Filter chips showing active selections
- See `references/filter-ui-patterns.md`

### Backend Query Patterns

**Database Query Building**
- Dynamic query construction with SQLAlchemy
- Django ORM filter chaining
- Indexes on search columns
- Full-text search in PostgreSQL
- See `references/database-querying.md`

**Elasticsearch Integration**
- Document indexing strategies
- Query DSL for complex searches
- Faceted aggregations
- Relevance scoring and boosting
- See `references/elasticsearch-integration.md`

**API Design**
- RESTful search endpoints
- Query parameter validation
- Cursor or offset pagination
- Response caching strategies
- See `references/api-design.md`

## Implementation Workflows

### Client-Side Search (<1000 items)

1. Load data into memory
2. Write filter functions in JavaScript
3. Debounce search on text input
4. Update results instantly
5. Keep filter state in React

### Server-Side Search (>1000 items)

1. Design search API endpoint
2. Validate and sanitize query parameters
3. Build database query dynamically
4. Paginate
5. Return results with metadata
6. Cache frequent queries

### Hybrid Approach

1. Filter client-side for immediate feedback
2. Fetch server results in background
3. Merge and deduplicate results
4. Update UI progressively
5. Cache recent searches locally

## Performance Optimization

### Frontend Optimization

**Debouncing Implementation**
- Use `debounce` from lodash or custom implementation
- Cancel pending requests on new input
- Show skeleton loaders during fetch
- Script: `scripts/debounce_calculator.js`

**Query Parameter Management**
- Sync filters with URL for shareable searches
- Use React Router or Next.js for URL state
- Compress complex queries
- See `references/query-parameter-management.md`

### Backend Optimization

**Query Optimization**
- Create fitting database indexes
- Find bottlenecks with query analyzers
- Cache query results
- Script: `scripts/generate_filter_query.py`

**Validation & Security**
- Validate all search inputs (types, lengths, allowlists)
- Prevent SQL injection with bound parameters (ORM or placeholders) and allowlisted sort/filter fields; never string-build SQL. Regex blocklists are backstop only
- Rate limit search endpoints
- Script: `scripts/validate_search_params.py`

## Accessibility Requirements

### ARIA Patterns

- Use `role="search"` for search regions
- Use `aria-live` for result updates
- Label filters clearly
- Support keyboard-only navigation

### Keyboard Support

- Tab through all interactive elements
- Arrow keys navigate autocomplete
- Escape closes dropdowns
- Enter selects/submits

## Technology Stack

### Frontend Libraries

**Primary: Downshift (Autocomplete)**
- Accessible autocomplete primitives
- Headless/unstyled, flexible
- WAI-ARIA compliant
- Install: `npm install downshift`

**Alternative: React Select**
- Full-featured select/filter component
- Built-in async search
- Multi-select support

### Backend Technologies

**Python/SQLAlchemy**
- Relationship loading optimization
- Query result pagination

**Python/Django**
- Django Filter backend
- Django REST Framework filters
- Full-text search with PostgreSQL

**Elasticsearch (Python)**
- elasticsearch-py client
- `elasticsearch.dsl` for query building (bundled in elasticsearch-py 8.18+; formerly separate elasticsearch-dsl package)

## Bundled Resources

### References
- `references/performance-optimization.md` - Performance tips
- `references/library-comparison.md` - Library evaluation

### Scripts
- `scripts/generate_filter_query.py` - Build parameterized SQL (sql + params) and ES queries
- `scripts/validate_search_params.py` - Validate inputs
- `scripts/debounce_calculator.js` - Calculate debounce timing

### Examples
- `examples/product-search.tsx` - E-commerce search
- `examples/autocomplete-search.tsx` - Autocomplete implementation
- `examples/sqlalchemy_search.py` - SQLAlchemy patterns
- `examples/fastapi_search.py` - FastAPI search endpoint
- `examples/django_filter_backend.py` - Django filters

### Assets
- `assets/filter-config-schema.json` - Filter configuration
- `assets/search-api-spec.json` - OpenAPI specification
