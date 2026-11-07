# Production Quality Checklist

## Pre-Code Checklist

Before writing any Manim code:

- [ ] Narration script written, visual beats marked
- [ ] Scene list with purpose, duration, layout for each
- [ ] Palette colors mapped to meanings (`PRIMARY` = main concept, etc.)
- [ ] `MONO = "Menlo"` set as font constant
- [ ] Target resolution and aspect ratio decided

## Text Quality

### Overlap prevention

```python
# RULE: buff >= 0.5 for edge text
label.to_edge(DOWN, buff=0.5)     # GOOD
label.to_edge(DOWN, buff=0.3)     # BAD — may clip

# RULE: FadeOut previous before adding new at same position
self.play(ReplacementTransform(note1, note2))  # GOOD
self.play(Write(note2))                          # BAD — overlaps note1

# RULE: Reduce font size for dense scenes
# When > 4 text elements visible, use font_size=20 not 28
```

### Width enforcement

Long text overflows frame:

```python
# RULE: Set max width for any text that might be long
text = Text("This is a potentially long description", font_size=22, font=MONO)
if text.width > config.frame_width - 1.0:
    text.set_width(config.frame_width - 1.0)
```

### Font consistency

```python
# RULE: Define MONO once, use everywhere
MONO = "Menlo"

# WRONG: mixing fonts
Text("Title", font="Helvetica")
Text("Label", font="Arial")
Text("Code", font="Courier")

# RIGHT: one font
Text("Title", font=MONO, weight=BOLD, font_size=48)
Text("Label", font=MONO, font_size=20)
Text("Code", font=MONO, font_size=18)
```

## Spatial Layout

### The coordinate budget

Visible frame: about 14.2 wide × 8.0 tall (default 16:9). With mandatory margins:

```
Usable area: x ∈ [-6.5, 6.5], y ∈ [-3.5, 3.5]
Top title zone: y ∈ [2.5, 3.5]
Bottom note zone: y ∈ [-3.5, -2.5]
Main content: y ∈ [-2.5, 2.5], x ∈ [-6.0, 6.0]
```

### Fill the frame

Empty scenes look unfinished. If main content is small, add context:
- Dimmed grid/axes behind content
- Title/subtitle at top
- Source citation at bottom
- Decorative geometry at low opacity

### Maximum simultaneous elements

**Hard limit: 6 actively visible elements.** Beyond that, viewer loses track. If you need more:
- Dim old elements to opacity 0.3
- Remove elements that served their purpose
- Split into two scenes

## Animation Quality

### Variety audit

Check no two consecutive scenes use exact same:
- Animation type (if Scene 3 is all Write, Scene 4 should use FadeIn or Create)
- Color emphasis (rotate palette colors)
- Layout (center, left-right, grid — alternate)
- Pacing (after slow, deliberate Scene 2, Scene 3 can be faster)

### Tempo curve

Good video follows a tempo curve:

```
Slow ──→ Medium ──→ FAST (climax) ──→ Slow (conclusion)

Scene 1: Slow (introduction, setup)
Scene 2: Medium (building understanding)
Scene 3: Medium-Fast (core content, lots of animation)
Scene 4: FAST (montage of applications/results)
Scene 5: Slow (conclusion, key takeaway)
```

### Transition quality

Between scenes:
- **Clean exit**: `self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)`
- **Brief pause**: `self.wait(0.3)` after fadeout, before next scene's first animation
- **Never hard-cut**: always animate transition

## Color Quality

### Dimming on dark backgrounds

Colors vibrant on white look muddy on dark backgrounds (#0D1117, #1C1C1C). Test palette:

```python
# Colors that work well on dark backgrounds:
# Bright and saturated: #58C4DD, #83C167, #FFFF00, #FF6B6B
# Colors that DON'T work: #666666 (invisible), #2244AA (too dark)

# RULE: Structural elements (axes, grids) at opacity 0.15
# Context elements at 0.3-0.4
# Primary elements at 1.0
```

### Color meaning consistency

Color meaning, once assigned, holds for entire video:

```python
# If PRIMARY (#58C4DD) means "the model" in Scene 1,
# it means "the model" in every scene.
# Never reuse PRIMARY for a different concept later.
```

## Data Visualization Quality

### Minimum requirements for charts

- Axis labels on every axis
- Y-axis range starts at 0 (or has clear break indicator)
- Bar/line colors match legend
- Numbers on notable data points (at least maximum and comparison point)

### Animated counters

When showing a changing number:
```python
# GOOD: DecimalNumber with smooth animation
counter = DecimalNumber(0, font_size=48, num_decimal_places=0, font="Menlo")
self.play(counter.animate.set_value(1000), run_time=3, rate_func=rush_from)

# BAD: Text that jumps between values
```

## Pre-Render Checklist

Before running `manim -qh`:

- [ ] All scenes render without errors at `-ql`
- [ ] Preview stills at `-qm` for text-heavy scenes (check kerning)
- [ ] Background color set in every scene (`self.camera.background_color = BG`)
- [ ] `add_subcaption()` or `subcaption=` on every significant animation
- [ ] No text smaller than font_size=18
- [ ] No proportional-font text (use monospace)
- [ ] buff >= 0.5 on all `.to_edge()` calls
- [ ] Clean exit (FadeOut all) at end of every scene
- [ ] `self.wait()` after every reveal
- [ ] Color constants used (no hardcoded hex strings in scene code)
- [ ] All scenes use same quality flag (don't mix `-ql` and `-qh`)

## Post-Render Checklist

After stitching final video:

- [ ] Watch complete video at 1x speed — rushed anywhere?
- [ ] Any moment where two simultaneous animations confuse?
- [ ] Every text label on screen long enough to read?
- [ ] Transitions between scenes smooth (no black frames, no jarring cuts)?
- [ ] Audio in sync with visuals (if using voiceover)?
- [ ] Gibbs-like "first impression" good? First 5 seconds determine if someone keeps watching
