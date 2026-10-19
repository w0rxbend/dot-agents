---
name: implementing-drag-drop
description: Implements drag-and-drop and sortable interfaces with React/TypeScript including kanban boards, sortable lists, drop-zone interactions, and reorderable grids. Use when building interactive UIs requiring direct manipulation, spatial organization, or touch-friendly reordering; for file upload handling (chunking, S3, progress, media processing) use managing-media.
---

# Drag-and-Drop & Sortable Interfaces

## Purpose

This skill helps implement drag-and-drop interactions and sortable interfaces using modern React/TypeScript libraries. It covers accessibility-first approaches, touch support, and performance optimization for creating intuitive direct manipulation UIs.

## When to Use

Invoke this skill when:
- Building Trello-style kanban boards with draggable cards between columns
- Creating sortable lists with drag handles for priority ordering
- Implementing file upload zones with visual drag-and-drop feedback
- Building reorderable grids for dashboard widgets or galleries
- Creating visual builders with node-based interfaces
- Implementing any UI requiring spatial reorganization through direct manipulation

## Core Patterns

### Sortable Lists
Reference `references/dnd-patterns.md` for:
- Vertical lists with drag handles
- Horizontal lists for tab/carousel reordering
- Grid layouts with 2D dragging
- Auto-scrolling near edges

### Kanban Boards
Reference `references/kanban-implementation.md` for:
- Multi-column boards with cards
- WIP limits and swimlanes
- Card preview on hover
- Column management (add/remove/collapse)

### File Upload Zones
Reference `references/file-dropzone.md` for the drag-and-drop interaction of a dropzone:
- Visual feedback states
- File type validation
- Multi-file handling

For the upload itself (chunked and resumable uploads, S3 direct upload, progress, image/video processing), use the `managing-media` skill.

### Accessibility
Reference `references/accessibility-dnd.md` for:
- Keyboard navigation patterns
- Screen reader announcements
- Alternative UI approaches
- ARIA attributes

## Library Selection

### Primary: dnd-kit
Modern, accessible, and performant drag-and-drop for React.

Reference `references/library-guide.md` for:
- Library comparison (dnd-kit vs alternatives)
- Installation and setup
- Core concepts and API
- Migration from react-beautiful-dnd

### Key Features
- Built-in accessibility support
- Touch, mouse, and keyboard input
- Zero dependencies (~10KB core)
- Highly customizable
- TypeScript native

## Implementation Workflow

### Step 1: Analyze Requirements
Determine the drag-and-drop pattern needed:
- Simple list reordering → Sortable list pattern
- Multi-container movement → Kanban pattern
- File handling → Dropzone pattern
- Complex interactions → Visual builder pattern

### Step 2: Set Up Library
Install required packages:
```bash
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

### Step 3: Implement Core Functionality
Use examples as starting points:
- `examples/sortable-list.tsx` for basic lists
- `examples/kanban-board.tsx` for multi-column boards
- `examples/file-dropzone.tsx` for file uploads
- `examples/grid-reorder.tsx` for grid layouts

### Step 4: Add Accessibility
Reference `references/accessibility-dnd.md` to:
- Implement keyboard navigation
- Add screen reader announcements
- Provide alternative controls
- Test with assistive technologies

Verify with real tooling: run axe-core (for example `@axe-core/playwright` in an end-to-end test) on the rendered page, test keyboard-only drag with Playwright (`page.keyboard.press('Space')`, arrow keys), and try a screen reader (VoiceOver, NVDA).

### Step 5: Optimize Performance
For lists with >100 items:
- Reference `references/performance-optimization.md`
- Implement virtual scrolling
- Use the helpers in `scripts/calculate_drop_position.js` (browser functions, import them into client code) for drop-index and auto-scroll calculations

### Step 6: Style with Design Tokens
Apply theming using the `theming-components` skill:
- Reference design token variables
- Implement drag states (hovering, dragging, dropping)
- Add visual feedback and animations

## Mobile & Touch Support

Reference `references/touch-support.md` for:
- Long press to initiate drag
- Preventing scroll during drag
- Touch-friendly hit areas (44px minimum)
- Gesture conflict resolution

## State Management

Reference `references/state-management.md` for:
- Managing drag state in React
- Optimistic updates
- Undo/redo functionality
- Persisting order changes

## Scripts

### Calculate Drop Position
`scripts/calculate_drop_position.js` exports browser helpers (they take DOM elements and cursor coordinates) to:
- Determine valid drop zones
- Calculate insertion indices
- Handle edge cases

### Generate Configuration
Run `scripts/generate_dnd_config.js` to:
- Create dnd-kit configuration
- Set up sensors and modifiers
- Configure animations


## Examples

Each example includes complete TypeScript code with accessibility:

### Sortable List
`examples/sortable-list.tsx`
- Vertical list with drag handles
- Keyboard navigation (Space/Enter to grab, arrows to move)
- Screen reader announcements

### Kanban Board
`examples/kanban-board.tsx`
- Multiple columns with draggable cards
- Card movement between columns
- Column management features
- WIP limits

### File Dropzone
`examples/file-dropzone.tsx`
- Drag files onto a drop target (upload handling: see `managing-media`)
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
- Type definitions for drag state
- Event handler types
- Configuration interfaces

### Configuration Schema
`assets/dnd-config-schema.json` defines:
- Valid configuration options
- Sensor settings
- Animation parameters

## Best Practices

### Visual Feedback
- Show drag handles (⋮⋮) to indicate draggability
- Change cursor (grab → grabbing)
- Display drop zone placeholders
- Make dragged items semi-transparent
- Highlight valid drop targets

### Performance
- Use CSS transforms, not position properties
- Apply `will-change: transform` for animations
- Throttle drag events for large lists
- Implement virtual scrolling when needed

### Accessibility First
- Always provide keyboard alternatives
- Include screen reader announcements
- Test with NVDA/JAWS/VoiceOver
- Provide non-drag alternatives (buttons/forms)

### Error Handling
- Show invalid drop feedback
- Implement undo functionality
- Auto-save after successful drops
- Handle network failures gracefully

## Common Pitfalls

### Avoid These Issues
- Forgetting keyboard navigation
- Missing touch support
- Not preventing scroll during drag
- Ignoring accessibility
- Poor performance with large lists

### Solutions
Reference the appropriate guide for each issue:
- Accessibility → `references/accessibility-dnd.md`
- Touch → `references/touch-support.md`
- Performance → `references/performance-optimization.md`
- State → `references/state-management.md`

## Testing Checklist

Before deployment, verify:
- [ ] Keyboard navigation works completely
- [ ] Screen readers announce all actions
- [ ] Touch devices can drag smoothly
- [ ] Performance acceptable with expected data volume
- [ ] Visual feedback clear and responsive
- [ ] Undo/redo functionality works
- [ ] Alternative UI provided for accessibility
- [ ] Works across all target browsers

## Next Steps

After implementing basic drag-and-drop:
1. Add advanced features (auto-scroll, multi-select)
2. Implement gesture support for mobile
3. Add animation polish with Framer Motion
4. Create custom drag preview components
5. Build complex interactions (nested dragging)