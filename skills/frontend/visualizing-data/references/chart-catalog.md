# Complete Chart Type Catalog

## Table of Contents

1. [Comparison Charts](#comparison-charts)
2. [Trend Charts](#trend-charts)
3. [Distribution Charts](#distribution-charts)
4. [Relationship Charts](#relationship-charts)
5. [Composition Charts](#composition-charts)
6. [Flow Charts](#flow-charts)
7. [Network Charts](#network-charts)
8. [Temporal Charts](#temporal-charts)
9. [Multivariate Charts](#multivariate-charts)
10. [Advanced Techniques](#advanced-techniques)

---

## Comparison Charts

### Bar Chart

**Purpose:** Compare values across categories

**When to Use:**
- Sales across products
- Survey results
- Ranking items by value
- 2-20 categories, simple comparisons

**Strengths:**
- Universally understood
- Length gives precise value comparison
- Easy to scan and rank

**Implementation:**
- Sort by value for readability (unless natural order matters)
- Horizontal bars for long category names
- Max 20 categories (filter for more)
- Start y-axis at zero

**Variants:**
- Horizontal: Better for many categories or long labels
- Grouped: Compare multiple series side-by-side
- Stacked: Show composition within categories

**Accessibility:**
- Direct labels on bars
- Color + pattern for grouped bars
- Data table alternative

---

### Lollipop Chart

**Purpose:** Space-efficient alternative to bar charts

**When to Use:**
- Many categories (10-30)
- Emphasize endpoint values
- Cleaner than dense bars
- Modern, minimal look wanted

**Strengths:**
- Better ink-to-data ratio
- Good for rankings

**Implementation:**
- Circle at data point end
- Thin line from baseline to circle
- Sort by value for readability
- Consistent circle size

---

### Slope Graph

**Purpose:** Before/after comparison showing change

**When to Use:**
- Ranking changes between two periods
- Before/after interventions
- Emphasize rate and direction of change
- 5-15 entities, two time points

**Implementation:**
- Two vertical axes (start and end)
- Lines connect same entity across time
- Color-code by direction (up/down)
- Label both endpoints

**Design Pattern:**
```
Before  After
  10 ──────→ 15  Entity A (↑)
  20 ──────→ 18  Entity B (↓)
  15 ──────→ 22  Entity C (↑)
```

---

## Trend Charts

### Line Chart

**Purpose:** Show change over continuous time

**When to Use:**
- Stock prices, sales trends
- Website traffic patterns
- Temperature/weather data
- Max 1-4 series for clarity

**Strengths:**
- Reveals seasonality and cycles
- Handles many data points well

**Implementation:**
- Monotone or smooth interpolation
- Markers for actual data points
- Legend for multi-series

**Variants:**
- Step chart: Discrete value changes
- Multi-line: Compare several trends
- With confidence bands: Show uncertainty

---

### Area Chart

**Purpose:** Emphasize magnitude and volume over time

**When to Use:**
- Total volume/quantity
- Scale of values
- Cumulative totals
- Filled area reinforces message

**Variants:**
- Simple: Single series with fill
- Stacked: Multiple series showing composition
- Normalized (100%): Proportional composition

**When to use stacked:**
- Parts sum to meaningful total
- Composition changes over time
- Comparing category proportions

---

### Stream Graph (ThemeRiver)

**Purpose:** Flowing composition over time with aesthetic emphasis

**When to Use:**
- Proportional change with visual appeal
- Evolving composition (4-10 categories)
- Cultural/music evolution over decades
- Technology adoption patterns
- Presentations where engagement matters

**Strengths:**
- Center baseline reduces perceptual distortion

**Implementation:**
- Center-weighted or symmetric baseline
- Organic, flowing shapes (not sharp edges)
- Place related categories near each other
- Interactive hover to isolate streams
- Try transparency for overlap

**Visual Form:**
```
         ╱════════════════╲
        ╱  Category A      ╲
       ╱────────────────────╲     ← Flowing
      ╱   Category B         ╲       organic
     │─────────────────────────│     shapes
      ╲   Category C         ╱
       ╲────────────────────╱
        ╲  Category D      ╱
         ╲════════════════╱
```

**Cautions:**
- Exact values hard to read
- Baseline ambiguity confuses some users
- Not suited to precise comparison

---

### Sparkline

**Purpose:** Compact inline trend visualization

**When to Use:**
- Dashboard KPIs
- Tables with trend context
- Small multiples in tight space
- Quick trend overview without detail

**Implementation:**
- Minimal: no axes, no labels
- Typical height: 30-50px
- Optional min/max markers
- Often grayscale or single color

---

## Distribution Charts

### Histogram

**Purpose:** Show frequency distribution of continuous data

**When to Use:**
- Data spread
- Skewness, bimodality
- Outlier detection
- Statistical analysis

**Implementation:**
- Bin size rules:
  - Sturges: k = 1 + log2(n)
  - Scott: h = 3.49σn^(-1/3)
  - Freedman-Diaconis: h = 2*IQR*n^(-1/3)
- Typical: 5-20 bins
- Equal-width bins for comparability

---

### Box Plot

**Purpose:** Summary statistics with outlier detection

**When to Use:**
- Compare distributions across groups
- Quick statistical summary
- Spot outliers
- Technical/statistical audiences

**Shows:** Minimum, Q1, median, Q3, maximum, outliers

**Anatomy:**
```
    ╭─────╮        ← Upper adjacent value
    │     │
    │─────│        ← Upper quartile (Q3)
    │  │  │        ← Median
    │─────│        ← Lower quartile (Q1)
    │     │
    ╰─────╯        ← Lower adjacent value
      ●            ← Outliers beyond 1.5×IQR
```

---

### Violin Plot

**Purpose:** Full distribution shape with summary statistics

**When to Use:**
- Compare distributions across categories
- Distribution shape matters as much as summary
- Reveal bimodal or multimodal distributions
- Scientific/technical data with complex distributions

**Strengths:**
- Reveals bimodality that box plots hide

**Implementation:**
- Mirror density estimation around vertical axis
- Include box plot elements (median line, quartiles)
- Optionally add individual data points
- Width shows density at that value

**Example Use Cases:**
- Salary distributions showing bimodal patterns
- Gene expression across experimental conditions
- Response times in treatment groups
- Product ratings showing polarization

**Cautions:**
- Needs more space than box plots
- Often unfamiliar to non-technical audiences
- Less effective with <20 data points

---

### Ridgeline Plot (Joy Plot)

**Purpose:** Compare many distributions efficiently

**When to Use:**
- Distributions across many categories (6-30+)
- Distribution evolution over time
- Temperature patterns by month
- Any data where distribution shape matters

**Strengths:**
- Easier to read than overlapping curves
- Reveals patterns like bimodality, shifts

**Implementation:**
- Stack top to bottom
- Overlap 20-40% for visibility
- Consistent horizontal scale
- Subtle transparency
- Clear labels on left

---

## Relationship Charts

### Scatter Plot

**Purpose:** Explore two-variable relationships

**When to Use:**
- Exploring correlation
- Spotting outliers and clusters
- Finding patterns in two dimensions
- <1000 points (use hexbin for more)

**Implementation:**
- Point size/color can encode third variable (bubble chart)
- Trend line if correlation exists
- Try jitter for overlapping points

---

### Bubble Chart

**Purpose:** Three-variable scatter plot

**When to Use:**
- Relationship + magnitude
- Compare entities across 3 dimensions
- Impactful presentations

**Implementation:**
- Size encodes third variable
- Size by AREA, not radius
- Limit to 20-50 bubbles
- Plan overlap handling

---

### Hexbin Plot

**Purpose:** Handle dense scatter plots with binning

**When to Use:**
- Scatter plots with thousands of overlapping points
- Geographic density visualization
- Individual points matter less than density
- Large datasets (10,000+ points)

**Strengths:**
- Hexagons tile more naturally than squares
- Shows density patterns at multiple scales

**Implementation:**
- Pick bin size from data density
- Color gradient shows density
- Optional contour lines
- Zoom interaction

---

### Connected Scatter Plot

**Purpose:** Two-variable relationship evolving over time

**When to Use:**
- Relationship AND temporal evolution
- Economic analysis (e.g., Phillips curve)
- Before/after with intermediate states
- Cyclical relationship analysis

**Strengths:**
- Reveals loops, spirals, reversals
- Path density shows acceleration/deceleration

**Implementation:**
- Directional arrows or gradients
- Label key points (start, end, inflections)
- Color gradient for temporal encoding
- Annotate major events

---

## Composition Charts

### Pie Chart

**Purpose:** Simple part-to-whole for few categories

**Use ONLY When:**
- 2-6 categories MAXIMUM
- Simple, round percentages
- Non-technical audience
- Single point comparison (not multiple pies)

**Avoid When:**
- >6 categories
- Comparing multiple compositions
- Precise comparison needed
- Similar-sized slices

**Better Alternative:** Horizontal bar chart sorted by value

---

### Treemap

**Purpose:** Hierarchical part-to-whole with nesting

**When to Use:**
- Hierarchical data with size comparison
- Portfolio allocation (sectors → stocks)
- File system disk usage
- Budget breakdown by category
- Market share with sub-segments

**Strengths:**
- Space-efficient
- Displays thousands of items
- Immediate visual size comparison

**Implementation:**
- Squarified algorithm for better aspect ratios
- Color-code by category or performance
- Borders to distinguish levels
- Zoom/drill-down for deep hierarchies
- Label only significant rectangles

---

### Sunburst Diagram

**Purpose:** Radial hierarchical visualization

**When to Use:**
- Hierarchical data with aesthetic emphasis
- Drill-down navigation through levels
- Circular/radial metaphor fits
- Alternative to treemap

**Implementation:**
- Center is root, outer rings are leaves
- Color by category or value
- Click-to-zoom for interactivity
- Breadcrumb trail
- Limit to 4-6 levels

---

### Waterfall Chart

**Purpose:** Sequential cumulative changes

**When to Use:**
- Profit bridges (revenue → costs → profit)
- Variance analysis
- Step-by-step value breakdown
- Financial reporting

**Implementation:**
- Floating bars show incremental changes
- Color-code positive (green) and negative (red)
- Running total at each step
- Final bar shows total

---

## Flow Charts

### Sankey Diagram

**Purpose:** Flow visualization with proportional width

**When to Use:**
- Resource flow and transformation
- Budget allocation through departments
- Energy flow from sources to uses
- Customer journey through website
- Supply chain visualization

**Strengths:**
- Instantly reveals major flows and losses
- Reveals inefficiencies and bottlenecks

**Implementation:**
- Use D3-sankey library
- Nodes = states, Links = flows
- Link width proportional to quantity
- Color-code by category or source
- Hover for exact values

**Structure:**
```
Source A ━━━━━━━━━━━━━━━┓
                       ┃━━━━━→ Destination 1
Source B ━━━━━━┓      ┃
               ┃━━━━━━┛
               ┃━━━━━━━━━━━━━→ Destination 2
Source C ━━━━━━┛
```

**Cautions:**
- Clutters with many nodes
- Crossing flows hurt readability
- Needs careful node ordering

---

### Chord Diagram

**Purpose:** Circular flow showing inter-relationships

**When to Use:**
- Inter-relationships in a network
- Migration patterns between regions
- Trade relationships between countries
- Character co-occurrence

**Strengths:**
- Compact view of full relationship matrix
- Shows bidirectional flows

**Implementation:**
- Use D3-chord library
- Order entities logically around circle
- Color-code by category or cluster
- Ribbon opacity for direction/confidence
- Hover highlighting to follow connections

---

## Network Charts

### Force-Directed Graph

**Purpose:** Network structure and communities

**When to Use:**
- Social networks
- Organizational structures
- Citation networks
- <200 nodes (becomes "hairball" beyond)

**Implementation:**
- Physics simulation (D3-force)
- Node size by importance/degree
- Edge thickness by weight
- Color by community/cluster

**Cautions:**
- Performance degrades >100 nodes
- Non-deterministic layout
- Often hard to interpret
- Consider alternatives for large networks

---

## Temporal Charts

### Gantt Chart

**Purpose:** Task scheduling and project timelines

**When to Use:**
- Project management
- Resource allocation
- Manufacturing schedules
- Sprint planning

**Implementation:**
- Horizontal bars show duration
- Dependencies as arrows
- Color by status or assignee
- Milestones as diamonds

---

### Calendar Heatmap

**Purpose:** Daily patterns over long periods

**When to Use:**
- Daily activity tracking (GitHub-style)
- Seasonality and weekly cycles
- Habit tracking and streaks
- Event frequency patterns

**Strengths:**
- Natural calendar metaphor
- Shows micro (daily) and macro (seasonal)

**Layout:**
```
       M  T  W  T  F  S  S
Jan   ██ ▓▓ ░░ ▓▓ ██ ░░ ░░
      ▓▓ ██ ░░ ▓▓ ▓▓ ██ ░░
Feb   ░░ ▓▓ ██ ░░ ▓▓ ░░ ██

Legend: ░░ Low  ▓▓ Medium  ██ High
```

---

## Multivariate Charts

### Parallel Coordinates

**Purpose:** Explore high-dimensional data (5-15 dimensions)

**When to Use:**
- Patterns across multiple dimensions
- Filtering and brushing multivariate data
- Comparing entity profiles
- Spotting clusters and outliers

**Strengths:**
- Displays hundreds of observations
- Reveals correlations and anti-correlations

**Implementation:**
- Normalize axes to comparable ranges
- Brushing to filter/highlight
- Allow axis reordering
- Transparency for overplotting

**Structure:**
```
Var1  Var2  Var3  Var4  Var5
 │     │     │     │     │
 ├─────┼─────┼─────┼─────┤   ← Data point 1
 ├───────────┼───────────┤   ← Data point 2
 │     │     │     │     │
```

---

### Radar/Spider Chart

**Purpose:** Multivariate profile comparison

**Use Cautiously:**
- Area distortion makes comparison misleading
- Axis order affects perceived patterns
- Exact values hard to read
- Many experts recommend alternatives

**When Acceptable:**
- Familiar domain (gaming, sports stats)
- Comparing 2-3 entities
- Audience expects this format
- 5-8 dimensions maximum

**Better Alternative:** Small multiples of bar charts

---

### Small Multiples (Trellis Plots)

**Purpose:** Compare patterns across many categories

**When to Use:**
- Regional comparisons with consistent metrics
- Time-period analysis (monthly breakdown)
- Faceting reveals more than grouping

**Strengths:**
- Pattern recognition at a glance
- Keeps context while showing variation
- Avoids overcrowding one chart
- Scales to many categories (4-20+ panels)

**Implementation:**
- Keep scales consistent across panels
- 2-6 columns depending on width
- Order by meaningful dimension
- Each panel readable at reduced size

---

## Advanced Techniques

### Animated Transitions & Morphing

**Purpose:** Smooth transformations between states

**When to Use:**
- Before/after comparisons
- Data evolution
- Narrative-driven presentations
- Reducing cognitive load during changes

**Implementation:**
- D3.js transitions with interpolators
- Duration: 500-800ms typical
- Easing: ease-in-out for natural feel
- Keep data keys for object constancy

**Code Pattern:**
```javascript
svg.selectAll('circle')
  .data(newData, d => d.id)
  .transition()
  .duration(750)
  .ease(d3.easeCubicInOut)
  .attr('cx', d => xScale(d.value));
```

**Cautions:**
- Don't overuse (becomes gimmicky)
- Offer skip option for accessibility
- Performance concerns with 1000+ elements

---

### Bubble Timeline

**Purpose:** Events of varying importance over time

**When to Use:**
- Product releases with impact metrics
- Historical events with varying significance
- Milestone visualization

**Implementation:**
- Horizontal time axis
- Circle AREA (not radius) proportional to value
- Labels for major events
- Color by category

---

*Working code examples:*
- `javascript/recharts-examples.md`
- `javascript/d3-patterns.md`
- `python/plotly-examples.md`
