---
name: implementing-drag-drop
description: Implements drag-and-drop and sortable interfaces with React/TypeScript including kanban boards, sortable lists, drop-zone interactions, and reorderable grids. Use when building interactive UIs requiring direct manipulation, spatial organization, or touch-friendly reordering; for file upload handling (chunking, S3, progress, media processing) use managing-media.
---

# Drag-and-Drop & Sortable Interfaces

## When to Use

Invoke for:
- Trello-style kanban boards with cards draggable between columns
- Sortable lists with drag handles for priority ordering
- File upload zones with visual drag-and-drop feedback
- Reorderable grids for dashboard widgets or galleries
- Visual builders with node-based interfaces
- Any UI needing spatial reorganization through direct manipulation

## Core Patterns

### Sortable Lists
See `references/dnd-patterns.md` for:
- Vertical lists with drag handles
- Horizontal lists for tab/carousel reordering
- Grid layouts with 2D dragging
- Auto-scroll near edges

### Kanban Boards
See `references/kanban-implementation.md` for:
- Multi-column boards with cards
- WIP limits and swimlanes
- Card preview on hover
- Column management (add/remove/collapse)

### File Upload Zones
See `references/file-dropzone.md` for dropzone drag-and-drop interaction:
- Visual feedback states
- File type validation (client-side is UX only; server re-validates)
- Multi-file handling

For upload itself (chunked and resumable uploads, S3 direct upload, progress, image/video processing), use `managing-media` skill.

### Accessibility
See `references/accessibility-dnd.md` for:
- Keyboard navigation patterns
- Screen reader announcements
- Alternative UI approaches
- ARIA attributes

## Library Selection

### Primary: dnd-kit
Built-in accessibility support; touch, mouse, and keyboard input; zero dependencies (~10KB core); highly customizable; TypeScript native.

See `references/library-guide.md` for:
- Library comparison (dnd-kit vs alternatives)
- Installation and setup
- Core concepts and API
- Migration from react-beautiful-dnd

## Implementation Workflow

### Step 1: Analyze Requirements
Pick drag-and-drop pattern:
- Simple list reordering: sortable list pattern
- Multi-container movement: kanban pattern
- File handling: dropzone pattern
- Complex interactions: visual builder pattern

### Step 2: Set Up Library
Install packages:
```bash
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

### Step 3: Implement Core Functionality
Start from examples:
- `examples/sortable-list.tsx` for basic lists
- `examples/kanban-board.tsx` for multi-column boards
- `examples/file-dropzone.tsx` for file uploads
- `examples/grid-reorder.tsx` for grid layouts

### Step 4: Add Accessibility
Use `references/accessibility-dnd.md`.

Verify with real tooling. Run axe-core (for example `@axe-core/playwright` in end-to-end test) on rendered page. Test keyboard-only drag with Playwright (`page.keyboard.press('Space')`, arrow keys). Try a screen reader (VoiceOver, NVDA).

### Step 5: Optimize Performance
For lists over 100 items:
- See `references/performance-optimization.md`
- Implement virtual scrolling
- Use helpers in `scripts/calculate_drop_position.js` (browser functions; import into client code) for drop-index and auto-scroll calculations

### Step 6: Style with Design Tokens
Theme with `theming-components` skill:
- Use design token variables
- Implement drag states (hovering, dragging, dropping)
- Add visual feedback and animations

## Mobile & Touch Support

See `references/touch-support.md` for:
- Long press to start drag
- Preventing scroll during drag
- Touch-friendly hit areas (44px minimum)
- Gesture conflict resolution

## State Management

See `references/state-management.md` for:
- Managing drag state in React
- Optimistic updates
- Undo/redo
- Persisting order changes

## Scripts

### Calculate Drop Position
`scripts/calculate_drop_position.js` exports browser helpers (take DOM elements and cursor coordinates) to:
- Find valid drop zones
- Calculate insertion indices
- Handle edge cases

### Generate Configuration
Run `scripts/generate_dnd_config.js` to:
- Create dnd-kit configuration
- Set up sensors and modifiers
- Configure animations

## Examples

Each has complete TypeScript code with accessibility:

### Sortable List
`examples/sortable-list.tsx`
- Vertical list with drag handles
- Keyboard navigation (Space/Enter to grab, arrows to move)
- Screen reader announcements

### Kanban Board
`examples/kanban-board.tsx`
- Multiple columns with draggable cards
- Card movement between columns
- Column management
- WIP limits

### File Dropzone
`examples/file-dropzone.tsx`
- Drag files onto drop target (upload handling: see `managing-media`)
- Visual feedback states
- File type validation
- Upload progress

### Grid Reorder
`examples/grid-reorder.tsx`
- 2D grid dragging
- Auto-layout on drop
- Responsive breakpoints

## Assets

### TypeScript Types
`assets/drag-state-types.ts` provides:
- Drag state type definitions
- Event handler types
- Configuration interfaces

### Configuration Schema
`assets/dnd-config-schema.json` defines:
- Valid configuration options
- Sensor settings
- Animation parameters

## Best Practices

### Visual Feedback
- Show drag handles (⋮⋮) to signal draggability
- Change cursor from grab to grabbing
- Show drop zone placeholders
- Make dragged items semi-transparent
- Highlight valid drop targets

### Performance
- Use CSS transforms, not position properties
- Apply `will-change: transform` for animations
- Throttle drag events for large lists

### Accessibility First
- Always provide keyboard alternatives
- Include screen reader announcements
- Test with NVDA/JAWS/VoiceOver
- Provide non-drag alternatives (buttons/forms)

### Error Handling
- Show invalid drop feedback
- Implement undo
- Auto-save after successful drops
- Handle network failures gracefully

## Testing Checklist

Before deployment, verify:
- [ ] Keyboard navigation works fully
- [ ] Screen readers announce all actions
- [ ] Touch devices drag smoothly
- [ ] Performance acceptable at expected data volume
- [ ] Visual feedback clear and responsive
- [ ] Undo/redo works
- [ ] Alternative UI provided for accessibility
- [ ] Works in all target browsers

## Next Steps

After basic drag-and-drop:
1. Add advanced features (auto-scroll, multi-select)
2. Add mobile gesture support
3. Polish animation with Framer Motion
4. Create custom drag preview components
5. Build complex interactions (nested dragging)
