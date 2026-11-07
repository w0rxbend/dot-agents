---
name: guiding-users
description: Implements onboarding and help systems including product tours, interactive tutorials, tooltips, checklists, help panels, and progressive disclosure patterns. Use when building first-time experiences, feature discovery, guided walkthroughs, contextual help, setup flows, or user activation features. Provides timing strategies, accessibility patterns (keyboard, screen readers, reduced motion), and metrics for measuring onboarding success.
---

# Guiding Users Through Onboarding and Help Systems

## When to Use

Use for:
- First-time user experiences or product tours
- Feature discovery and announcements
- Interactive tutorials or guided tasks
- Tooltips, hints or contextual help
- Setup flows or completion checklists
- Help panels or documentation systems
- Progressive disclosure patterns
- Measuring onboarding effectiveness and user activation
- Onboarding accessibility

## Quick Decision Framework

Pick guidance mechanism by user state and content type:

```
First-time user          → Product Tour (step-by-step)
New feature launch       → Feature Spotlight (tooltip + animation)
Complex workflow         → Interactive Tutorial (guided tasks)
Account setup            → Checklist (progress tracking)
Contextual help needed   → Tooltip/Hint system
Ongoing support          → Help Panel (sidebar/searchable)
Feature unlock           → Progressive Disclosure
```

Detailed selection criteria: `references/selection-framework.md`.

## Core Guidance Mechanisms

### Product Tours

Step-by-step walkthroughs of key features:
- Sequential spotlights with modal overlays
- Progress indicators (Step 2 of 5)
- Skip, Previous and Next controls
- Dismiss and resume
- Context-sensitive activation

Full example: `examples/first-time-tour.tsx`.
Patterns and best practices: `references/product-tours.md`.

### Feature Spotlights

Announce new features to existing users:
- Pulsing hotspot animations
- Contextual tooltip with arrow
- "Got it" acknowledgment
- Auto-dismiss after first view
- Non-blocking overlay

Example: `examples/feature-spotlight.tsx`.
Patterns: `references/tooltips-hints.md`.

### Interactive Tutorials

Guided task completion with validation:
- "Complete these tasks to get started"
- Checkbox completion tracking
- Celebration animations on completion
- Sandbox mode with sample data
- Undo and reset

Example: `examples/guided-tutorial.tsx`.
Patterns: `references/interactive-tutorials.md`.

### Setup Checklists

Track multi-step onboarding progress:
- Visual progress indicators (3/4 complete)
- Direct links to each task
- Profile completion percentages
- Achievement badges and gamification
- Persistent until completed

Example: `examples/setup-checklist.tsx`.
Patterns: `references/checklists.md`.

### Contextual Tooltips and Hints

Just-in-time help when needed:
- Hover- or click-triggered tooltips
- Progressive hint levels (1, 2, 3)
- "Need help?" assistance triggers
- Context-aware suggestions
- Keyboard-accessible

Example: `examples/contextual-help.tsx`.
Full patterns: `references/tooltips-hints.md`.

### Help Panels

Full help systems:
- Sidebar or drawer interface
- Contextual help for current page
- Search help articles and docs
- Video tutorials and demos
- Contact support integration
- Collapsible and resizable

Example: `examples/help-panel.tsx`.
Patterns: `references/help-systems.md`.

## Timing and Triggering Strategies

### When to Show Onboarding

Triggers:
- First login (always)
- Right after signup
- New feature launch (to existing users)
- User appears stuck (smart triggering on inactivity)
- User explicitly requests help

### When NOT to Show Onboarding

Avoid showing when:
- User is mid-task or focused
- Shown every session (annoying)
- Before allowing free exploration
- Tour exceeds 7 steps (too long)
- User already dismissed or completed

**Auto-dismiss timing:**
- Simple tooltips: 5-7 seconds
- Feature announcements: 10-15 seconds or manual dismiss
- Tours: user-controlled, no auto-dismiss
- Persistent hints: until user acknowledges

Detailed guidelines: `references/timing-strategies.md`.

## Progressive Disclosure Patterns

Show only what's needed, when needed:

**Techniques:**
1. **Accordion Help**: Collapsed by default, expand for details
2. **"Learn More" Links**: Optional deep-dive content
3. **Advanced Settings**: Hidden behind "Show advanced" toggle
4. **Gradual Feature Introduction**: Unlock features as user progresses
5. **Contextual Hints**: Show based on user actions

Implementation patterns: `references/progressive-disclosure.md`.

## Accessibility Requirements

### Keyboard Navigation

Essential keyboard support:
- Tab through tour steps and controls
- ESC dismisses tours and tooltips
- Arrow keys for Previous/Next
- Enter/Space activates buttons
- Visible focus indicators

### Screen Reader Support

ARIA patterns for announcements:
- Announce step number and total (Step 2 of 5)
- Read tooltip and help content
- Describe highlighted UI elements
- Announce progress completion
- Alert on errors or blockers

### Reduced Motion

Respect `prefers-reduced-motion`:
- Disable pulsing animations
- Instant transitions instead of animations
- Remove parallax and complex effects
- Keep functionality without motion

To check accessibility, run automated browser scan (for example `@axe-core/playwright` against page with tour open). Then verify keyboard-only navigation, screen-reader announcements and reduced motion by hand; automated scanners do not cover those. Do not report tour as accessible until both are done.

Full implementation: `references/accessibility-patterns.md`.

## Library Recommendations

### Primary: react-joyride (Feature-Rich, Accessible)

**Library:** `react-joyride` (github.com/gilbarbara/react-joyride)

Best for comprehensive product tours:
- WAI-ARIA compliant out of the box
- Full keyboard navigation
- Highly customizable styling
- Programmatic control
- Localization
- Active maintenance

```bash
npm install react-joyride
```

Full setup: `examples/joyride-tour.tsx`.

### Alternative: driver.js (Lightweight, Modern)

Best for minimal bundle size:
- Vanilla JavaScript (framework agnostic)
- ~5KB gzipped
- Modern API design
- No dependencies

```bash
npm install driver.js
```

### Alternative: intro.js (Classic, Proven)

Best for traditional tours:
- Battle-tested
- Wide browser support
- JSON-based tour configuration
- Extensive plugin ecosystem

```bash
npm install intro.js
```

Detailed analysis and selection criteria: `references/library-comparison.md`.

## Design Token Integration

Style all onboarding components with project design tokens for consistent theming (see theming-components skill):

**Token categories used:**
- **Colors**: Tour spotlight, overlay, tooltip backgrounds, hotspot colors
- **Spacing**: Tour padding, tooltip spacing, arrow size
- **Typography**: Title sizes, body text, help content
- **Borders**: Border radius for modals and tooltips
- **Shadows**: Elevation for tour spotlights and tooltips
- **Motion**: Transition durations, pulse animations

Supports light, dark, high-contrast and custom brand themes.

## Measuring Success

### Key Metrics

Track:
- Tour completion rate (target: >60%)
- Time to first value (faster = better)
- Feature adoption rate post-tour
- Support ticket reduction
- User activation rate (completed key actions)
- Drop-off points in tours

### Optimization Strategies

Iterate on data:
- A/B test tour length (shorter often better)
- Test different messaging and copy
- Measure drop-off at each step
- Simplify steps with high abandonment
- Add skip options for returning users
- Personalize by user type

To analyze onboarding metrics, compute per-step reach and drop-off from analytics events (tour_started, step_viewed, tour_completed, tour_skipped). Use analytics tool or short query over exported events.

Full analytics implementation: `references/measuring-success.md`.

## Anti-Patterns to Avoid

❌ **Forced Tours**: Requiring tour completion before product use
❌ **No Skip Option**: Users cannot explore independently
❌ **Wall of Text**: Long explanations instead of visuals
❌ **Blocking Everything**: Preventing interaction during tours
❌ **No Context**: Generic tips without specific relevance

## Implementation Workflow

### Step 1: Map User Journey

Identify key moments:
1. First login and account creation
2. Core value delivery (aha moment)
3. Feature discovery points
4. Potential confusion or abandonment
5. Achievement and progress milestones

### Step 2: Choose Guidance Mechanisms

Match mechanisms to moments:
- First login → Product tour (3-5 steps max)
- Core features → Interactive tutorial
- Setup requirements → Checklist
- New features → Spotlight + tooltip
- Ongoing help → Help panel

### Step 3: Implement with Progressive Enhancement

Build incrementally:
1. Start with essential guidance only: one critical flow (usually first-time experience)
2. Add contextual help based on user behavior
3. Add analytics to measure effectiveness
4. Iterate on data
5. A/B test variations

### Step 4: Test Accessibility

Verify compliance:
- Keyboard navigation works fully
- Screen reader announces properly
- Reduced motion preference honored
- Focus management correct
- ARIA labels descriptive

Run automated scan (e.g. `@axe-core/playwright`) with each tour step visible. Do manual keyboard and screen-reader checks above. Report which checks were actually run.

### Step 5: Monitor and Optimize

Track and improve:
- Monitor completion rates
- Find drop-off points
- Test with real users, gather feedback
- A/B test improvements

## Working Examples

Start with example matching use case:

```
first-time-tour.tsx           # Product walkthrough with react-joyride
feature-spotlight.tsx         # New feature announcement
guided-tutorial.tsx           # Interactive task completion
setup-checklist.tsx           # Multi-step onboarding progress
contextual-help.tsx           # Tooltips and progressive hints
help-panel.tsx                # Sidebar help with search
celebration-animation.tsx     # Completion feedback
```

## Resources

### Assets (Templates and Configs)
- `assets/celebration-animations/` - Success animations and confetti
- `assets/tour-templates.json` - Reusable tour configurations
- `assets/message-templates.json` - Tooltip and hint copy templates
- `assets/timing-config.json` - Recommended timing values

## Cross-Skill Integration

Works with other component skills:

- **Forms**: Guided form completion, validation hints
- **Dashboards**: Feature tours, widget explanations
- **Tables**: Data grid tutorials, feature discovery
- **AI Chat**: Chat interface walkthroughs
- **Navigation**: Menu and navigation guidance
- **Feedback**: Success celebrations, progress notifications
