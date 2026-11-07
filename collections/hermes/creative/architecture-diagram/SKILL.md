---
name: architecture-diagram
description: "Dark-themed SVG architecture/cloud/infra diagrams as HTML."
version: 1.0.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [design-md, claude-design]
---

# Architecture Diagram Skill

Generate dark-themed technical architecture diagrams as standalone HTML files with inline SVG. No external tools, API keys or rendering libraries: write HTML file, open in browser.

## Scope

**Best suited for:**
- Software system architecture (frontend / backend / database layers)
- Cloud infrastructure (VPC, regions, subnets, managed services)
- Microservice / service-mesh topology
- Database + API map, deployment diagrams
- Any tech-infra subject fitting dark, grid-backed aesthetic

**Look elsewhere first for:**
- Physics, chemistry, math, biology, other scientific subjects
- Physical objects (vehicles, hardware, anatomy, cross-sections)
- Floor plans, narrative journeys, educational / textbook-style visuals
- Hand-drawn whiteboard sketches (use whiteboard tool such as Excalidraw)
- Animated explainers (consider animation skill)

Prefer more specialized skill for subject if available. If none fits, use this skill as general SVG diagram fallback. Output keeps dark tech aesthetic described below.

Based on [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT).

## Workflow

1. User describes system architecture (components, connections, technologies)
2. Generate HTML file following design system below
3. Save with `write_file` to `.html` file (e.g. `~/architecture-diagram.html`)
4. User opens in any browser. No build step

### Output Location

Save diagrams to user-specified path, else default to current working directory:
```
./[project-name]-architecture.html
```

### Preview

After saving, suggest user open it:
```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## Design System & Visual Language

### Color Palette (Semantic Mapping)

Categorize components with these `rgba` fills and hex strokes:

| Component Type | Fill (rgba) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **Backend** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **Database** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/Cloud** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **Security** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **External** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

### Typography & Background
- **Font:** JetBrains Mono (Monospace) from Google Fonts. Keep `monospace` fallback in `font-family` so it renders offline
- **Sizes:** 12px (Names), 9px (Sublabels), 8px (Annotations), 7px (Tiny labels)
- **Background:** Slate-950 (`#020617`) with subtle 40px grid pattern

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

## Technical Implementation Details

### Component Rendering
Components are rounded rectangles (`rx="6"`) with 1.5px strokes. Use **double-rect masking technique** so arrows do not show through semi-transparent fills:
1. Draw opaque background rect (`#0f172a`)
2. Draw semi-transparent styled rect on top

### Connection Rules
- **Z-Order:** Draw arrows *early* in SVG (after grid) so they render behind component boxes
- **Arrowheads:** Define via SVG markers
- **Security Flows:** Dashed lines in rose color (`#fb7185`)
- **Boundaries:**
  - *Security Groups:* Dashed (`4,4`), rose color
  - *Regions:* Large dashed (`8,4`), amber color, `rx="12"`

### Spacing & Layout Logic
- **Standard Height:** 60px (Services); 80-120px (Large components)
- **Vertical Gap:** Minimum 40px between components
- **Message Buses:** Must sit *in the gap* between services, not overlapping them
- **Legend Placement:** **CRITICAL.** Must sit outside all boundary boxes. Find lowest Y-coordinate of all boundaries. Place legend at least 20px below it.

## Document Structure

Generated HTML file uses four-part layout:
1. **Header:** Title with pulsing dot indicator and subtitle
2. **Main SVG:** Diagram inside rounded border card
3. **Summary Cards:** Grid of three cards below diagram for high-level details
4. **Footer:** Minimal metadata

### Info Card Pattern
```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

## Output Requirements
- **Single File:** One self-contained `.html` file
- **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts)
- **No JavaScript:** Pure CSS for any animations (like pulsing dots)
- **Compatibility:** Must render correctly in any modern web browser

## Template Reference

Load full HTML template for exact structure, CSS, and SVG component examples:

```
skill_view(name="architecture-diagram", file_path="templates/template.html")
```

Template has working examples of every component type (frontend, backend, database, cloud, security), arrow styles (standard, dashed, curved), security groups, region boundaries, and legend.
