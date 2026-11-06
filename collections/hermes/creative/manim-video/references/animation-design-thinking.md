# Animation Design Thinking

## Should I animate this?

**Animate when:**
- Sequence unfolds over time (algorithm steps, derivation, pipeline stages)
- Spatial relationships change (transformation, deformation, rotation)
- Built from parts (construction, assembly, accumulation)
- Comparing states (before/after, method A vs method B)
- Temporal evolution is the point (training curves, wave propagation, gradient descent)

**Show static when:**
- Single labeled diagram (circuit, anatomy, architecture overview)
- Motion would distract from spatial layout
- Viewer must study it carefully (dense table, reference chart)
- Already intuitive from well-labeled figure

**Rule of thumb:** Explained as "first X, then Y, then Z"? Animate. Explained by pointing at parts of one picture? Show static.

## Decomposing a concept into animation

### Step 1: Write the narration first

Write narration before code. It determines:
- **Order**: which concept comes first
- **Duration**: time each idea gets
- **Visuals**: what viewer must SEE while HEARING each sentence

Narration says "the gradient points uphill"? Show gradient arrow at that moment. Mismatched visual and audio split viewer attention.

### Step 2: Identify visual beats

Beat: moment where something changes on screen. Mark each beat in narration:

```
"Consider a function f of x."         → [BEAT: axes + curve appear]
"At this point..."                     → [BEAT: dot appears on curve]
"...the slope is positive."            → [BEAT: tangent line drawn]
"So the gradient tells us to go left." → [BEAT: arrow points left, dot moves]
```

Each beat is one `self.play()` call or small group of simultaneous animations.

### Step 3: Choose the right tool per beat

| Visual need | Manim approach |
|-------------|----------------|
| Object appears first time | `Create`, `Write`, `FadeIn`, `GrowFromCenter` |
| Object becomes another | `Transform`, `ReplacementTransform`, `FadeTransform` |
| Draw attention to existing object | `Indicate`, `Circumscribe`, `Flash`, `ShowPassingFlash` |
| Maintain continuous relationship | `add_updater`, `always_redraw`, `ValueTracker` |
| Object leaves scene | `FadeOut`, `Uncreate`, `ShrinkToCenter` |
| Static context staying visible | `self.add()` (no animation) |

## Pacing: the universal mistake is too fast

### Timing rules

| Content type | Minimum on-screen time |
|-------------|----------------------|
| New equation appearing | 2.0s animation + 2.0s pause |
| New concept label | 1.0s animation + 1.0s pause |
| Key insight ("aha moment") | 2.5s animation + 3.0s pause |
| Supporting annotation | 0.8s animation + 0.5s pause |
| Scene transition (FadeOut all) | 0.5s animation + 0.3s pause |

### Breathing room

Add `self.wait()` after every reveal. Viewer needs time to:
1. Read new text
2. Connect it to what's on screen
3. Anticipate what comes next

**No wait = viewer always behind you.**

### Tempo variation

Vary tempo:
- **Slow build** for core concepts (long run_time, long pauses)
- **Quick succession** for supporting details (short run_time, minimal pauses)
- **Dramatic pause** before key reveal (extra `self.wait(2.0)` before the "aha")
- **Rapid montage** for "and this applies to X, Y, Z..." sequences (`LaggedStart` with tight lag_ratio)

## Narration synchronization

### The "see then hear" principle

Show visual slightly BEFORE narration describes it. Viewer sees circle, THEN hears "consider a circle": visual primes the concept.

### Practical timing

```python
# Scene duration should match narration duration.
# If narration for this scene is 8 seconds:
# Total animation run_times + total self.wait() times = ~8 seconds.

# Use manim-voiceover for automatic sync:
with self.voiceover(text="The gradient points downhill") as tracker:
    self.play(GrowArrow(gradient_arrow), run_time=tracker.duration)
```

## Equation decomposition strategy

### The "dim and reveal" pattern

Building complex equation step by step:
1. Show full equation dimmed at `opacity=0.2` (sets expectation of destination)
2. Highlight first term at full opacity
3. Explain it
4. Highlight next term, dim first to `0.5` (now context)
5. Repeat until full equation is bright

Better than building left-to-right: viewer always sees destination.

### Term ordering

Animate terms in order viewer needs them, not equation order. For `E = mc²`:
- Show `E` (what we want to know)
- Then `m` (input)
- Then `c²` (constant that makes it work)
- Then `=` (connects them)

## Architecture and pipeline diagrams

### Box granularity

Most common mistake: too many boxes. Five clearly labeled boxes beat twelve abbreviated ones.

**Rule:** If two consecutive boxes could be labeled "X" and "process X output," merge them into one box.

### Animation strategy

Build pipelines left-to-right (or top-to-bottom), arrows connecting boxes:
1. First box appears alone; explain it
2. Arrow grows from first to second: "the output feeds into..."
3. Second box appears; explain it
4. Repeat

Then show data flow: `ShowPassingFlash` along arrows, or colored dot traversing path.

### The zoom-and-return pattern

For complex systems:
1. Show full overview (all boxes, small)
2. Zoom into one box (`MovingCameraScene.camera.frame.animate`)
3. Expand that box into internal components
4. Zoom back out to overview
5. Zoom into next box

## Common design mistakes

1. **Animating everything at once.** Viewer tracks 1-2 simultaneous animations. More, and nothing registers.
2. **No visual hierarchy.** Same opacity/size/color everywhere: nothing stands out. Use opacity layering.
3. **Equations without context.** Lone equation means nothing. Always show geometric/visual interpretation first or simultaneously.
4. **Skipping the "why."** Showing HOW a transformation works, not WHY it matters. Add sentence/label stating purpose.
5. **Identical pacing throughout.** Every animation at run_time=1.5, every wait at 1.0. Vary it.
6. **Forgetting the audience.** High schoolers need different pacing and complexity than PhD students. Decide audience during planning.
