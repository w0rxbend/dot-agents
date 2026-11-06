# Troubleshooting Reference

> **See also:** composition.md · architecture.md · shaders.md · scenes.md · optimization.md

## Quick Diagnostic

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All black output | tonemap gamma too high, or no effects rendering | Lower gamma to 0.5, check scene_fn returns non-zero canvas |
| Washed out / too bright | Linear brightness multiplier instead of tonemap | Replace `canvas * N` with `tonemap(canvas, gamma=0.75)` |
| ffmpeg hangs mid-render | stderr=subprocess.PIPE deadlock | Redirect stderr to file |
| "read-only" array error | broadcast_to view without .copy() | Add `.copy()` after broadcast_to |
| PicklingError | Lambda or closure in SCENES table | Define all fx_* at module level |
| Random dark holes in output | Font missing Unicode glyphs | Validate palettes at init |
| Audio-visual desync | Frame timing accumulation | Use integer frame counter, compute t fresh each frame |
| Single-color flat output | Hue field shape mismatch | Make h,s,v arrays all (rows,cols) before hsv2rgb |
| Text unreadable over busy bg | No text/background contrast | Use `apply_text_backdrop()` (composition.md) + `reverse_vignette` shader (shaders.md) |
| Text garbled/mirrored | Kaleidoscope or mirror shader on text scene | **Never apply kaleidoscope, mirror_h/v/quad/diag to scenes with readable text**. Radial folding destroys legibility. Use only on background layers or text-free scenes |

## NumPy Broadcasting

### The `broadcast_to().copy()` Trap

Hue field generators often return broadcast views: shape `(1, cols)` or `(rows, 1)`, broadcast to `(rows, cols)`. Views are **read-only**. Downstream in-place edits (e.g., `h %= 1.0`) make numpy raise:

```
ValueError: output array is read-only
```

**Fix**: Always `.copy()` after `broadcast_to()`:

```python
h = np.broadcast_to(h, (g.rows, g.cols)).copy()
```

Matters most in `_render_vf()`: hue arrays flow through `hsv2rgb()`.

### The `+=` vs `+` Trap

In-place operators also fail on mismatched operand shapes:

```python
# FAILS if result is (rows,1) and operand is (rows, cols)
val += np.sin(g.cc * 0.02 + t * 0.3) * 0.5

# WORKS — creates a new array
val = val + np.sin(g.cc * 0.02 + t * 0.3) * 0.5
```

Mixing array shapes: use `+`, not `+=`.

### Shape Mismatch in `hsv2rgb()`

`hsv2rgb(h, s, v)` needs identical shapes for all three arrays. `h` `(1, cols)` with `s` `(rows, cols)` crashes or gives wrong output.

**Fix**: Broadcast and copy all inputs to `(rows, cols)` first.

---

## Blend Mode Pitfalls

### Overlay Crushes Dark Inputs

`overlay(a, b) = 2*a*b` when `a < 0.5`. Two 0.12 inputs give `2 * 0.12 * 0.12 = 0.03`, darker than either.

**Impact**: Dark layers (typical ASCII art) give near-black output.

**Fix**: Use `screen` for dark sources. It always brightens: `1 - (1-a)*(1-b)`.

### Colordodge Division by Zero

`colordodge(a, b) = a / (1 - b)`. `b = 1.0` (pure white pixels) divides by zero.

**Fix**: Add epsilon: `a / (1 - b + 1e-6)`. `BLEND_MODES` should include this.

### Colorburn Division by Zero

`colorburn(a, b) = 1 - (1-a) / b`. `b = 0` (pure black pixels) divides by zero.

**Fix**: Add epsilon: `1 - (1-a) / (b + 1e-6)`.

### Multiply Always Darkens

`multiply(a, b) = a * b`. Operands in [0,1], so result always <= min(a,b). Never use multiply for feedback blend: frame goes black within a few frames.

**Fix**: Use `screen` for feedback, or `add` with low opacity.

---

## Multiprocessing

### Pickling Constraints

`ProcessPoolExecutor` pickles function arguments, limiting what workers receive:

| Can Pickle | Cannot Pickle |
|-----------|---------------|
| Module-level functions (`def fx_foo():`) | Lambdas (`lambda x: x + 1`) |
| Dicts, lists, numpy arrays | Closures (functions defined inside functions) |
| Class instances (with `__reduce__`) | Instance methods |
| Strings, numbers | File handles, sockets |

**Impact**: Every scene function in SCENES table must be module-level `def`. Lambda or closure gives:

```
_pickle.PicklingError: Can't pickle <function <lambda> at 0x...>
```

**Fix**: Define all scene functions at module top level. Lambdas inside `_render_vf()` as val_fn/hue_fn are fine: they run inside the worker, never pickled across processes.

### macOS spawn vs Linux fork

macOS `multiprocessing` defaults to `spawn` (full serialization). Linux defaults to `fork` (copy-on-write):

- **macOS**: Feature arrays serialized per worker (~57KB for 30s video, scales with duration). Each worker re-imports whole module.
- **Linux**: Feature arrays shared via COW. Workers inherit parent memory.

**Impact**: On macOS, module-level code (like `detect_hardware()`) runs in every worker. Side effects (e.g., subprocess calls) happen N+1 times.

### Per-Worker State Isolation

Each worker creates its own:
- `Renderer` instance (with fresh grid cache)
- `FeedbackBuffer` (feedback doesn't cross scene boundaries)
- Random seed (`random.seed(hash(seg_id) + 42)`)

So:
- Particle state doesn't carry between scenes (expected)
- Feedback trails reset at scene cuts (expected)
- `random.seed()` does NOT seed `np.random`: separate RNGs

**Fix for deterministic noise**: Use `np.random.RandomState(seed)` explicitly:

```python
rng = np.random.RandomState(hash(seg_id) + 42)
noise = rng.random((rows, cols))
```

---

## Brightness Issues

### Dark Scenes After Tonemap

Scene still dark after tonemap? Check:

1. **Gamma too high**: Lower gamma (0.5-0.6) for scenes with destructive post-processing
2. **Shader destroying brightness**: Solarize, posterize or contrast in shader chain can undo tonemap. Move destructive shaders earlier, or raise gamma.
3. **Feedback with multiply**: Darkens every frame. Switch to screen or add.
4. **Overlay blend in scene**: Scene function uses `blend_canvas(..., "overlay", ...)` on dark layers? Switch to screen.

### Diagnostic: Test-Frame Brightness

```bash
python reel.py --test-frame 10.0
# Output: Mean brightness: 44.3, max: 255
```

Mean < 20 needs attention. Common fixes:
- Lower gamma in SCENES entry
- Switch internal blend modes from overlay/multiply to screen/add
- Raise value field multipliers (e.g., `vf_plasma(...) * 1.5`)
- Check shader chain for aggressive solarize or threshold

### v1 Brightness Pattern (Deprecated)

Old pattern used linear multiplier:

```python
# OLD — don't use
canvas = np.clip(canvas.astype(np.float32) * 2.0, 0, 255).astype(np.uint8)
```

Fails because:
- Dark scenes (mean 8): `8 * 2.0 = 16`, still dark
- Bright scenes (mean 130): `130 * 2.0 = 255`, clipped, lost detail

Use `tonemap()` instead. See `composition.md` § Adaptive Tone Mapping.

---

## ffmpeg Issues

### Pipe Deadlock

#1 production bug, from `stderr=subprocess.PIPE`:

```python
# DEADLOCK — stderr buffer fills at 64KB, blocks ffmpeg, blocks your writes
pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
```

**Fix**: Always redirect stderr to file:

```python
stderr_fh = open(err_path, "w")
pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL, stderr=stderr_fh)
```

### Frame Count Mismatch

Frames written to pipe not matching ffmpeg's expectation (from `-r` and duration) can cause:
- Missing frames at end
- Wrong duration
- Audio-video desync

**Fix**: Compute frame count explicitly: `n_frames = int(duration * FPS)`. Don't use `range(int(start*FPS), int(end*FPS))` without verifying total matches.

### Concat Fails with "unsafe file name"

```
[concat @ ...] Unsafe file name
```

**Fix**: Always use `-safe 0`:
```python
["ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_path, ...]
```

---

## Font Issues

### Cell Height (macOS Pillow)

`textbbox()` and `getbbox()` give wrong heights on some macOS Pillow versions. Use `getmetrics()`:

```python
ascent, descent = font.getmetrics()
cell_height = ascent + descent  # correct
# NOT: font.getbbox("M")[3]  # wrong on some versions
```

### Missing Unicode Glyphs

Not all fonts cover all Unicode characters. Palette character missing from font renders blank or as tofu box: dark hole in output.

**Fix**: Validate at init:

```python
all_chars = set()
for pal in [PAL_DEFAULT, PAL_DENSE, PAL_RUNE, ...]:
    all_chars.update(pal)

valid_chars = set()
for c in all_chars:
    if c == " ":
        valid_chars.add(c)
        continue
    img = Image.new("L", (20, 20), 0)
    ImageDraw.Draw(img).text((0, 0), c, fill=255, font=font)
    if np.array(img).max() > 0:
        valid_chars.add(c)
    else:
        log(f"WARNING: '{c}' (U+{ord(c):04X}) missing from font")
```

### Platform Font Paths

| Platform | Common Paths |
|----------|-------------|
| macOS | `/System/Library/Fonts/Menlo.ttc`, `/System/Library/Fonts/Monaco.ttf` |
| Linux | `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf` |
| Windows | `C:\Windows\Fonts\consola.ttf` (Consolas) |

Always probe multiple paths, fall back gracefully. See `architecture.md` § Font Selection.

---

## Performance

### Slow Shaders

Some shaders use Python loops and run very slow at 1080p:

| Shader | Issue | Fix |
|--------|-------|-----|
| `wave_distort` | Per-row Python loop | Use vectorized fancy indexing |
| `halftone` | Triple-nested loop | Vectorize with block reduction |
| `matrix rain` | Per-column per-trail loop | Accumulate index arrays, bulk assign |

### Render Time Scaling

Render much slower than expected? Check:
1. Grid count: each extra grid adds ~100-150ms/frame for init
2. Particle count: cap at quality-appropriate limits
3. Shader count: each adds 2-25ms
4. Accidental Python loops in effects (should be numpy only)

---

## Common Mistakes

### Using `r.S` vs the `S` Parameter

v2 scene protocol passes `S` (state dict) as explicit parameter. `S` IS `r.S`: same object. Both work:

```python
def fx_scene(r, f, t, S):
    S["counter"] = S.get("counter", 0) + 1   # via parameter (preferred)
    r.S["counter"] = r.S.get("counter", 0) + 1  # via renderer (also works)
```

### Forgetting to Handle Empty Feature Values

Audio features default to 0.0 on silent audio. Use `.get()` with sensible defaults:

```python
energy = f.get("bass", 0.3)  # default to 0.3, not 0
```

Default 0 blanks effects during silence.

### Writing New Files Instead of Editing Existing State

Common particle-system bug: new arrays every frame instead of updating persistent state.

```python
# WRONG — particles reset every frame
S["px"] = []
for _ in range(100):
    S["px"].append(random.random())

# RIGHT — only initialize once, update each frame
if "px" not in S:
    S["px"] = []
# ... emit new particles based on beats
# ... update existing particles
```

### Not Clipping Value Fields

Value fields should be [0, 1]. Outside range, `val2char()` produces index errors:

```python
# WRONG — vf_plasma() * 1.5 can exceed 1.0
val = vf_plasma(g, f, t, S) * 1.5

# RIGHT — clip after scaling
val = np.clip(vf_plasma(g, f, t, S) * 1.5, 0, 1)
```

`_render_vf()` clips automatically. Custom scenes must clip explicitly.

## Brightness Best Practices

- Dense animated backgrounds: never flat black, always fill grid
- Vignette minimum clamped to 0.15 (not 0.12)
- Bloom threshold 130 (not 170): more pixels contribute to glow
- FeedbackBuffer decay minimum 0.5: below that, feedback fades too fast to see
- Value field floor: `vf * 0.8 + 0.05`, so no cell is truly zero
- Per-scene gamma overrides: default 0.75, solarize 0.55, posterize 0.50, bright scenes 0.85

**Quick checklist before full render:**
1. Render 3 test frames (start, middle, end)
2. Check `canvas.mean() > 8` after tonemap
3. Check no scene is visually flat black
4. Verify per-section variation (different bg/palette/color per scene)
5. Confirm shader chain includes bloom (threshold 130)
6. Confirm vignette strength ≤ 0.25
