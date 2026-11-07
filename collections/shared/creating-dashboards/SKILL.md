---
name: creating-dashboards
description: Build React dashboard UIs (Tremor, react-grid-layout) that combine KPI cards, charts, tables, shared filters, real-time updates and draggable layouts. Use when writing a dashboard as part of a React application; for Grafana use grafana-dashboards, for Datadog dashboards use datadog, for single-chart design use visualizing-data.
---

# Creating Dashboards

## When to Use

Activate for:
- Business intelligence or analytics dashboards
- Executive reporting interfaces
- Real-time monitoring systems
- KPI displays with metrics and trends
- Customizable widget-based layouts
- Filters coordinated across multiple data displays
- Responsive data-heavy interfaces
- Drag-and-drop dashboard editors
- Template-based analytics systems
- Multi-tenant SaaS dashboards

## Core Dashboard Elements

### KPI Card Anatomy
```
┌────────────────────────────┐
│ Revenue (This Month)       │ ← Label with time period
│                            │
│  $1,245,832               │ ← Big number (primary metric)
│  ↑ 15.3% vs last month    │ ← Trend indicator with comparison
│  ▂▃▅▆▇█ (sparkline)       │ ← Mini visualization
└────────────────────────────┘
```

### Widget Container Structure
- Title bar with widget name and actions
- Loading state (skeleton or spinner)
- Error boundary with retry
- Resize handles for adjustable layouts
- Settings menu (export, configure, refresh)

### Dashboard Layout Types

**Fixed Layout**: Designer-defined placement, same for all users
**Customizable Grid**: User drag-and-drop, resizable widgets, saved layouts
**Template-Based**: Pre-built patterns, industry-specific starting points

### Global Dashboard Controls
- Date range picker (affects all widgets)
- Filter panel (coordinated across widgets)
- Refresh controls (manual/auto-refresh)
- Export actions (PDF, image, data)
- Theme switcher (light/dark/custom)

## Implementation Approach

### 1. Choose Dashboard Architecture

**For Quick Analytics Dashboard → Use Tremor**
Pre-built KPI cards, charts and tables, minimal code:
```bash
npm install @tremor/react@3   # legacy npm package, built for Tailwind CSS v3
```
Current Tremor releases are copy-paste components (tremor.so), not this npm package. Check which one project already uses before adding either.

**For Customizable Dashboard → Use react-grid-layout**
Drag-and-drop, resizable widgets, user-defined layouts:
```bash
npm install react-grid-layout@1   # the examples below use the v1 WidthProvider/Responsive API
```
react-grid-layout v2 changed HOC API. If project is on v2, follow its README instead of these snippets.

### 2. Set Up Global State Management

Add filter context for cross-widget coordination:
```tsx
// Dashboard context for shared filters
const DashboardContext = createContext({
  filters: { dateRange: null, categories: [] },
  setFilters: () => {},
  refreshInterval: 30000
});

// Wrap dashboard with provider
<DashboardContext.Provider value={dashboardState}>
  <FilterPanel />
  <WidgetGrid />
</DashboardContext.Provider>
```

### 3. Implement Data Fetching Strategy

**Parallel Loading**: Fetch all widget data at once
**Lazy Loading**: Load visible widgets first, others on scroll
**Cached Updates**: Serve from cache while fetching fresh data

### 4. Configure Real-Time Updates

**Server-Sent Events (Recommended for Dashboards)**: see Real-Time Data Patterns below.

### 5. Apply Responsive Design

Define breakpoints per screen size:
- Desktop (>1200px): Multi-column grid
- Tablet (768-1200px): 2-column layout
- Mobile (<768px): Single column stack

## Quick Start with Tremor

### Basic KPI Dashboard
```tsx
import { Card, Grid, Metric, Text, BadgeDelta, AreaChart } from '@tremor/react';

function QuickDashboard({ data }) {
  return (
    <Grid numItems={1} numItemsSm={2} numItemsLg={4} className="gap-4">
      {/* KPI Cards */}
      <Card>
        <Text>Total Revenue</Text>
        <Metric>$45,231.89</Metric>
        <BadgeDelta deltaType="increase">+12.5%</BadgeDelta>
      </Card>

      <Card>
        <Text>Active Users</Text>
        <Metric>1,234</Metric>
        <BadgeDelta deltaType="decrease">-2.3%</BadgeDelta>
      </Card>

      {/* Chart Widget */}
      <Card className="lg:col-span-2">
        <Text>Revenue Trend</Text>
        <AreaChart
          data={data.revenue}
          index="date"
          categories={["revenue"]}
          valueFormatter={(value) => `$${value.toLocaleString()}`}
        />
      </Card>
    </Grid>
  );
}
```

Full implementation: `examples/tremor-dashboard.tsx`.

## Customizable Dashboard Implementation

### Drag-and-Drop Grid Layout
```tsx
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

function CustomizableDashboard() {
  const [layouts, setLayouts] = useState(getStoredLayouts());

  return (
    <ResponsiveGridLayout
      layouts={layouts}
      breakpoints={{ lg: 1200, md: 996, sm: 768 }}
      cols={{ lg: 12, md: 10, sm: 6 }}
      rowHeight={60}
      onLayoutChange={(layout, layouts) => {
        setLayouts(layouts);
        localStorage.setItem('dashboardLayout', JSON.stringify(layouts));
      }}
      draggableHandle=".widget-header"
    >
      <div key="kpi1">
        <KPIWidget data={kpiData} />
      </div>
      <div key="chart1">
        <ChartWidget data={chartData} />
      </div>
      <div key="table1">
        <TableWidget data={tableData} />
      </div>
    </ResponsiveGridLayout>
  );
}
```

Full example with widget catalog: `examples/customizable-dashboard.tsx`.

## Real-Time Data Patterns

### Server-Sent Events (Recommended)
Best for one-way updates, server to dashboard:
```tsx
function useSSEUpdates(endpoint) {
  useEffect(() => {
    const eventSource = new EventSource(endpoint);

    eventSource.onmessage = (event) => {
      const update = JSON.parse(event.data);
      // Update specific widget or all widgets
      dispatch({ type: 'UPDATE_WIDGET', payload: update });
    };

    return () => eventSource.close();
  }, [endpoint]);
}
```

### WebSocket (For Bidirectional)
Use when dashboard sends commands back to server:
```tsx
const ws = new WebSocket('ws://localhost:3000/dashboard');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateDashboard(data);
};
// Send filter changes to server
ws.send(JSON.stringify({ type: 'FILTER_CHANGE', filters }));
```

### Smart Polling Fallback
For environments without WebSocket/SSE support:
```tsx
function useSmartPolling(fetchData, interval = 30000) {
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused || document.hidden) return;

    const timer = setInterval(fetchData, interval);
    return () => clearInterval(timer);
  }, [isPaused, interval]);

  // Pause when tab inactive
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPaused(document.hidden);
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);
}
```

Detailed patterns, including error handling and reconnection: `references/real-time-updates.md`.

## Performance Optimization

### Lazy Loading Strategy
```tsx
import LazyLoad from 'react-lazyload'; // npm install react-lazyload (or use an IntersectionObserver hook)

function DashboardGrid({ widgets }) {
  return widgets.map(widget => (
    <LazyLoad
      key={widget.id}
      height={widget.height}
      offset={100}
      once
      placeholder={<WidgetSkeleton />}
    >
      <Widget {...widget} />
    </LazyLoad>
  ));
}
```

### Parallel Data Fetching
```tsx
// Fetch all widget data simultaneously
const loadDashboard = async () => {
  const [kpis, charts, tables] = await Promise.all([
    fetchKPIs(),
    fetchChartData(),
    fetchTableData()
  ]);

  return { kpis, charts, tables };
};
```

### Widget-Level Caching
Keep fetched data in React state (or query cache) so refresh re-renders. `useRef` update alone never does.
```tsx
import { useQuery } from '@tanstack/react-query';

function CachedWidget({ id, fetcher, ttl = 60000 }) {
  const { data, refetch } = useQuery({
    queryKey: ['widget', id],
    queryFn: fetcher,
    staleTime: ttl, // serve cached data for `ttl` ms before refetching
  });

  return <Widget data={data} onRefresh={() => refetch()} />;
}
```

Analyze and optimize dashboard performance:
```bash
python scripts/optimize-dashboard-performance.py --config dashboard-config.json
# or estimate without a config: --widgets 12 --auto-refresh-count 4
```

## Cross-Skill Integration

Other skills in this collection; load them for widget internals. They are guidance, not importable modules. Build or install components in user's project.

- **Charts**: `visualizing-data` for chart type choice and chart components (Recharts, Nivo, D3).
- **Data grids**: `building-tables` for sortable, filterable, paginated tables (e.g. TanStack Table).
- **Theming**: `theming-components` for design tokens. Dashboard-specific tokens can map onto existing ones:
```tsx
const dashboardTokens = {
  '--dashboard-bg': 'var(--color-bg-secondary)',
  '--widget-bg': 'var(--color-white)',
  '--widget-shadow': 'var(--shadow-lg)',
  '--kpi-value-size': 'var(--font-size-4xl)',
  '--kpi-trend-positive': 'var(--color-success)',
  '--kpi-trend-negative': 'var(--color-error)'
};
```
- **Filter inputs**: `building-forms` for date-range pickers, multi-selects and other filter controls.

## Library Selection Guide

### Choose Tremor When:
- Dashboards needed quickly
- Pre-styled, professional components wanted
- Project uses Tailwind CSS
- Standard analytics interfaces
- Limited customization needs

### Choose react-grid-layout When:
- Users need custom layouts
- Drag-and-drop required
- Different users need different views
- Dashboard builder tool
- Maximum flexibility first

### Combine Both When:
- Tremor for widget contents (KPIs, charts)
- react-grid-layout for layout management

## Bundled Resources

### Scripts (Token-Free Execution)
- `scripts/generate-dashboard-layout.py` - Generate responsive grid configurations
- `scripts/calculate-kpi-metrics.py` - Calculate trends, comparisons, sparklines
- `scripts/validate-widget-config.py` - Validate widget and filter configurations
- `scripts/optimize-dashboard-performance.py` - Analyze, optimize performance
- `scripts/export-dashboard.py` - Export dashboards to various formats

Run scripts directly without loading into context:
```bash
python scripts/calculate-kpi-metrics.py --data metrics.json --period monthly
```

### References (Detailed Patterns)
- `references/kpi-card-patterns.md` - KPI card patterns and variations
- `references/layout-strategies.md` - Grid systems and responsive approaches
- `references/real-time-updates.md` - WebSocket, SSE and polling implementations
- `references/filter-coordination.md` - Cross-widget filter synchronization
- `references/performance-optimization.md` - Advanced optimization
- `references/library-guide.md` - Tremor and react-grid-layout guides

### Examples (Complete Implementations)
- `examples/sales-dashboard.tsx` - Sales analytics dashboard
- `examples/monitoring-dashboard.tsx` - Real-time monitoring with alerts
- `examples/executive-dashboard.tsx` - Polished executive reporting
- `examples/customizable-dashboard.tsx` - Drag-and-drop with persistence
- `examples/tremor-dashboard.tsx` - Quick Tremor implementation
- `examples/filter-context.tsx` - Global filter coordination

### Assets (Templates & Configurations)
- `assets/dashboard-templates.json` - Pre-built dashboard layouts
- `assets/widget-library.json` - Widget catalog and configurations
- `assets/grid-layouts.json` - Responsive grid configurations
- `assets/kpi-formats.json` - Number formatting rules
- `assets/theme-tokens.json` - Dashboard-specific design tokens

## Dashboard Creation Workflow

1. **Define Requirements**: Fixed or customizable? Real-time or static?
2. **Choose Libraries**: Tremor for speed, react-grid-layout for flexibility
3. **Set Up Structure**: Global state, filter context, layout system
4. **Build Widgets**: KPI cards, charts (visualizing-data), tables (building-tables)
5. **Implement Data Flow**: Fetching strategy, caching, updates
6. **Add Interactivity**: Filters, drill-downs, exports
7. **Optimize Performance**: Lazy loading, parallel fetching, caching
8. **Apply Theming**: theming-components for consistent styling
9. **Test Responsiveness**: Desktop, tablet, mobile breakpoints
10. **Deploy & Monitor**: Track performance, user engagement
