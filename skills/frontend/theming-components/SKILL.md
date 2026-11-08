---
name: theming-components
description: Provides design token system and theming framework for consistent, customizable UI styling. Covers token taxonomy (color, typography, spacing, shadows, borders, motion, z-index), theme switching (CSS custom properties, theme providers), RTL/i18n via CSS logical properties, and accessibility tokens (WCAG contrast, high-contrast themes, reduced motion). Use when implementing design tokens, light/dark or brand themes, or RTL-ready styling; for design-system audits use design-system and for one-off page aesthetics use frontend-design.
---

# Design Tokens & Theming System

Design tokens are **single source of truth** for all visual design decisions.

**Critical architectural principle:**
```
Component Skills (Behavior + Structure) → Use tokens for ALL visual styling
Design Tokens (Styling Variables)       → Define colors, spacing, typography
Theme Files (Token Overrides)           → Light, dark, brand-specific values
```

## Quick Start

### Using Tokens in Components

**Step 1: Reference tokens in component:**

```css
.button {
  background-color: var(--button-bg-primary);
  color: var(--button-text-primary);
  padding-inline: var(--button-padding-inline);
  padding-block: var(--button-padding-block);
  border-radius: var(--button-border-radius);
  transition: var(--transition-fast);
}
```

**Step 2: Themes apply automatically:**

```html
<!-- Light theme -->
<html data-theme="light">
  <button class="button">Primary Button</button>
</html>

<!-- Dark theme (same component, different appearance) -->
<html data-theme="dark">
  <button class="button">Primary Button</button>
</html>
```

**No code changes needed** - theme switching is automatic.

### Basic Theme Switching

```javascript
function setTheme(themeName) {
  document.documentElement.setAttribute('data-theme', themeName);
  localStorage.setItem('theme', themeName);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  setTheme(current === 'dark' ? 'light' : 'dark');
}

// Load saved theme on page load
setTheme(localStorage.getItem('theme') || 'light');
```

## Token Taxonomy (7 Core Categories)

### 1. Color Tokens

**3-tier hierarchy: Primitive → Semantic → Component**

```css
/* Primitive (9-shade scales) */
--color-blue-500: #3B82F6;

/* Semantic (purpose-based) */
--color-primary: var(--color-blue-500);
--color-success: var(--color-green-500);
--color-error: var(--color-red-500);

/* Component-specific */
--button-bg-primary: var(--color-primary);
```

### 2. Spacing Tokens

**4px base scale:**

```css
--space-1: 4px;   --space-2: 8px;   --space-4: 16px;
--space-6: 24px;  --space-8: 32px;  --space-12: 48px;

/* Semantic */
--spacing-sm: var(--space-2);   /* 8px */
--spacing-md: var(--space-4);   /* 16px */
--spacing-lg: var(--space-6);   /* 24px */
```

### 3. Typography Tokens

```css
--font-sans: 'Inter', -apple-system, sans-serif;
--font-mono: 'Fira Code', monospace;

--font-size-sm: 14px;
--font-size-base: 16px;
--font-size-lg: 18px;

--font-weight-normal: 400;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

### 4. Border & Radius Tokens

```css
--border-width-thin: 1px;
--border-width-medium: 2px;

--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-full: 9999px;
```

### 5. Shadow Tokens

```css
--shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.07);
--shadow-md: 0 4px 8px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.12);

--shadow-focus-primary: 0 0 0 3px rgba(59, 130, 246, 0.3);
```

### 6. Motion Tokens

```css
--duration-fast: 150ms;
--duration-normal: 200ms;

--ease-out: cubic-bezier(0, 0, 0.2, 1);
--transition-fast: all var(--duration-fast) var(--ease-out);
```

### 7. Z-Index Tokens

```css
--z-dropdown: 1000;
--z-modal-backdrop: 1040;
--z-modal: 1050;
--z-tooltip: 1070;
```

## Theme Architecture

### Light/Dark Themes

```css
/* themes/light.css */
:root {
  --color-primary: #3B82F6;
  --color-background: #FFFFFF;
  --color-text-primary: #1F2937;
}

/* themes/dark.css */
:root[data-theme="dark"] {
  --color-primary: #60A5FA;
  --color-background: #111827;
  --color-text-primary: #F9FAFB;
}
```

### Custom Brand Theme

```css
:root[data-theme="my-brand"] {
  --color-primary: #FF6B35;
  --font-sans: 'Poppins', sans-serif;
  --radius-md: 12px;
}
```

## CSS Logical Properties (RTL Support)

**Use logical properties for automatic RTL support:**

| Physical (Avoid) | Logical (Use) |
|------------------|---------------|
| `margin-left` | `margin-inline-start` |
| `padding-right` | `padding-inline-end` |
| `text-align: left` | `text-align: start` |

```css
/* Correct - auto-flips in RTL */
.button {
  padding-inline: var(--button-padding-inline);
  margin-inline-start: var(--spacing-sm);
}
```

## Component Integration

**All component skills use this naming convention:**

```
--{component}-{property}-{variant?}-{state?}
```

**Examples:**
```css
--button-bg-primary
--button-bg-primary-hover
--input-border-color-focus
--chart-color-1
```

Components consume semantic and component tokens; theme changes update all components automatically.

## Accessibility

### WCAG 2.1 AA Compliance

- **Normal text**: 4.5:1 contrast minimum
- **Large text (≥ 24px, or ≥ 18.66px bold)**: 3:1 minimum
- **UI components**: 3:1 minimum

### High-Contrast Theme

```css
:root[data-theme="high-contrast"] {
  --color-primary: #0000FF;
  --color-text-primary: #000000;
  /* 7:1 contrast (WCAG AAA) */
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-fast: 0ms;
    --transition-fast: none;
  }
}
```

## Platform Exports (Style Dictionary)

Exports CSS variables, SCSS, iOS Swift, Android XML, JavaScript.

```
JSON Tokens → Style Dictionary → CSS Variables
                               → iOS Swift
                               → Android XML
                               → JavaScript
```

## W3C Token Format

```json
{
  "color": {
    "primary": {
      "$value": "#3B82F6",
      "$type": "color"
    }
  }
}
```

## Scripts

```bash
# Generate color scale from base color
python scripts/generate_color_scale.py --base "#3B82F6"

# Validate token structure
python scripts/validate_tokens.py

# Check WCAG contrast ratios
python scripts/validate_contrast.py

# Build all platforms
npm run build-tokens
```

## References

**Core Systems:**
- `references/color-system.md` - Color scales and semantics
- `references/typography-system.md` - Type scales and fonts
- `references/spacing-system.md` - Spacing scale and rhythm

**Implementation:**
- `references/theme-switching.md` - Light/dark mode, custom themes
- `references/component-integration.md` - How skills use tokens
- `references/logical-properties.md` - RTL support patterns

**Tools & Accessibility:**
- `references/style-dictionary-setup.md` - Multi-platform build
- `references/accessibility-tokens.md` - WCAG compliance

**Progressive disclosure:** SKILL.md has overview and quick start. Details in `references/`.
