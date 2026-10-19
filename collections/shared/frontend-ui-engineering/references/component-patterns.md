# Component Patterns: Compound Components and List Virtualization

Read this when a component needs a flexible multi-part API (tabs, accordions, menus, selects) or when a list or table may render hundreds of rows or more. Examples are React + TypeScript; adapt to the project's framework and existing primitives first. If the project already uses a headless library (Radix, React Aria, Headless UI, Ark), use its component instead of hand-rolling one.

## Compound components

Use when consumers need to arrange the parts of one widget freely (`<Tabs><TabList><Tab/></TabList><TabPanel/></Tabs>`) while the parent owns the shared state. Share state through a context that fails loudly when a part is used outside its parent, and put the ARIA wiring in the parts so every consumer gets it.

```tsx
import { createContext, useContext, useId, useState, type ReactNode } from 'react';

type TabsCtx = { active: string; setActive: (id: string) => void; baseId: string };
const TabsContext = createContext<TabsCtx | null>(null);

function useTabs(part: string): TabsCtx {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error(`<${part}> must be rendered inside <Tabs>`);
  return ctx;
}

export function Tabs({ defaultTab, children }: { defaultTab: string; children: ReactNode }) {
  const [active, setActive] = useState(defaultTab);
  const baseId = useId();
  return <TabsContext.Provider value={{ active, setActive, baseId }}>{children}</TabsContext.Provider>;
}

export function TabList({ label, children }: { label: string; children: ReactNode }) {
  return <div role="tablist" aria-label={label}>{children}</div>;
}

export function Tab({ id, children }: { id: string; children: ReactNode }) {
  const { active, setActive, baseId } = useTabs('Tab');
  const selected = active === id;
  return (
    <button
      role="tab"
      id={`${baseId}-tab-${id}`}
      aria-selected={selected}
      aria-controls={`${baseId}-panel-${id}`}
      tabIndex={selected ? 0 : -1}
      onClick={() => setActive(id)}
    >
      {children}
    </button>
  );
}

export function TabPanel({ id, children }: { id: string; children: ReactNode }) {
  const { active, baseId } = useTabs('TabPanel');
  if (active !== id) return null;
  return (
    <div role="tabpanel" id={`${baseId}-panel-${id}`} aria-labelledby={`${baseId}-tab-${id}`} tabIndex={0}>
      {children}
    </div>
  );
}
```

Complete the keyboard contract before shipping: Left/Right arrow keys move between tabs, Home/End jump to first/last (WAI-ARIA Authoring Practices "Tabs" pattern). Memoize the context value (`useMemo`) if the provider re-renders often.

When not to use: a widget with one fixed layout is simpler as a single component with props.

## Virtualizing long lists

Render only the rows in view when a list can reach hundreds-plus items or each row is expensive. Measure first (React Profiler, Performance panel); pagination or simpler rows may be enough. Example with `@tanstack/react-virtual` (check the installed major version's docs):

```tsx
import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';

export function VirtualList<T>({ items, renderRow }: { items: T[]; renderRow: (item: T) => React.ReactNode }) {
  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72,  // estimated row height in px
    overscan: 5,             // extra rows rendered above/below the viewport
  });

  return (
    <div ref={parentRef} style={{ height: 600, overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((row) => (
          <div
            key={row.key}
            data-index={row.index}
            ref={virtualizer.measureElement}  // measures rows of variable height
            style={{ position: 'absolute', top: 0, left: 0, width: '100%', transform: `translateY(${row.start}px)` }}
          >
            {renderRow(items[row.index])}
          </div>
        ))}
      </div>
    </div>
  );
}
```

Trade-offs to check:
- Browser find-in-page and screen readers only see rendered rows; provide search/filter and announce the total count (`aria-rowcount` / `aria-setsize` + `aria-posinset` where applicable).
- Keep scroll position and focus stable when items are inserted or the list refetches; use stable keys from data IDs when rows can reorder (`getItemKey`).
- Fixed-height rows are cheaper: drop `measureElement` when every row has the same height.
