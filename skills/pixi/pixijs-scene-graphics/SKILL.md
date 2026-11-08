---
name: pixijs-scene-graphics
description: "Use this skill when drawing vector shapes and paths in PixiJS v8. Covers the Graphics API: shape-then-fill methods (rect/circle/ellipse/poly/roundRect/star/regularPoly/roundPoly/roundShape/filletRect/chamferRect), path methods (moveTo/lineTo/bezierCurveTo/quadraticCurveTo/arc/arcTo/arcToSvg/closePath), fill/stroke/cut, holes, FillGradient (linear/radial), FillPattern, GraphicsContext sharing, svg import/export, containsPoint hit testing, cloning, clearing, bounds, fillStyle/strokeStyle, draw-time transforms (rotateTransform/scaleTransform/translateTransform/setTransform/save/restore), default styles, GraphicsPath reuse. Triggers on (in PixiJS code): Graphics, GraphicsContext, Graphics rect/circle/poly/roundRect, Graphics fill/stroke/cut, holes, beginHole, FillGradient, FillPattern, moveTo, bezierCurveTo, Graphics svg import, graphicsContextToSvg, GraphicsOptions, containsPoint, Graphics clone/clear/bounds, rotateTransform, translateTransform, setFillStyle, setStrokeStyle, GraphicsPath."
license: MIT
---

`Graphics` is vector-drawing leaf of PixiJS v8 scene graph. v8 API is shape-then-style: draw shape or path with `rect`, `circle`, `moveTo`, etc., then apply `fill` and/or `stroke`. Methods return `this` for chaining. Drawing instructions live on a `GraphicsContext`, shareable between instances.

Assumes scene core concepts (`pixijs-scene-container` skill, `references/scene-core-concepts.md`).

**Related skills:** `pixijs-scene-container` (group graphics with other objects; its `references/scene-core-concepts.md` covers scene graph basics and Graphics as stencil mask), `pixijs-performance` (batching, `cacheAsTexture`). For filters see [PixiJS filters guide](https://pixijs.com/8.x/guides/components/filters).

## Constructor options

All `Container` options (`position`, `scale`, `tint`, `label`, `filters`, `zIndex`, etc.) also valid here. See constructor-options table in `references/scene-core-concepts.md` of `pixijs-scene-container` skill.

Leaf-specific options added by `GraphicsOptions`:

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `context` | `GraphicsContext` | new `GraphicsContext()` | Shared drawing context. Passing one reuses its tessellated geometry across multiple `Graphics` nodes, avoiding duplicate GPU work. If omitted, each `Graphics` creates its own. |
| `roundPixels` | `boolean` | `false` | Rounds final on-screen `x`/`y` to nearest pixel. Crisper pixel-art lines, but loses smooth sub-pixel movement. |

Constructor also takes a `GraphicsContext` as sole argument: `new Graphics(ctx)` is shorthand for `new Graphics({ context: ctx })`.

## Core Patterns

### Shape-then-fill workflow

```ts
const g = new Graphics();

g.rect(10, 10, 200, 100)
  .fill({ color: 0x3498db, alpha: 0.8 })
  .stroke({ width: 3, color: 0x2c3e50 });

g.circle(150, 200, 40).fill(0xe74c3c);
g.roundRect(300, 10, 150, 80, 12).fill(0x2ecc71);
g.poly([0, 0, 60, 0, 30, 50], true).fill(0x9b59b6);
g.star(400, 200, 5, 40, 20, 0).fill(0xf39c12);
g.ellipse(100, 350, 60, 30).fill(0x1abc9c);
```

`fill()` accepts a `FillInput`: color number/string, `{ color, alpha, texture, matrix, textureSpace }`, a `FillGradient`, a `FillPattern`, or a `Texture`. For texture fills, `textureSpace` controls coordinate mapping:

- `'local'` (default): texture scaled to fit each shape's bounding box (normalized 0-1 coordinates).
- `'global'`: texture position/scale relative to Graphics object's coordinate system, shared across all shapes.
- Atlas sub-textures: `'global'` honors frame origin and rotation, so shape drawn at frame's size matches a `Sprite` of that frame. `'local'` maps whole source image; pass a `matrix` targeting frame's region of source, or `renderer.generateTexture()` the frame first.

`FillInput` also supports nested `fill` subfield: a `FillStyle` object can embed a `FillGradient` or `FillPattern` under its `fill` key. It applies alongside outer `color`, `alpha`, `texture`, and `matrix` modifiers.

`stroke()` accepts a color, a `FillGradient`, a `FillPattern`, or a `StrokeStyle` object combining all `FillStyle` keys (`color`, `alpha`, `texture`, `matrix`, `fill`, `textureSpace`) with stroke attributes:

| Attribute | Default | Notes |
| --- | --- | --- |
| `width` | `1` | Stroke width in pixels. |
| `cap` | `'butt'` | One of `'butt'`, `'round'`, `'square'`. End style for open paths. |
| `join` | `'miter'` | One of `'miter'`, `'round'`, `'bevel'`. Corner style. |
| `miterLimit` | `10` | Max miter join extension before bevel fallback. |
| `alignment` | `0.5` | `1` = inside shape, `0.5` = centered, `0` = outside. |
| `pixelLine` | `false` | Aligns 1-pixel lines to pixel grid for crisp output. Graphics-only. |

Strokes can use same gradients and patterns as fills via `fill: gradient` or `texture: tex`:

```ts
const grad = new FillGradient({
  end: { x: 1, y: 0 },
  colorStops: [
    { offset: 0, color: 0xff0000 },
    { offset: 1, color: 0x0000ff },
  ],
});
g.rect(0, 0, 200, 100).stroke({
  width: 8,
  fill: grad,
  join: "round",
  cap: "round",
});
```

`fill()` and `stroke()` can both follow same shape; `stroke()` right after `fill()` reuses that path.

### Advanced shape primitives

```ts
g.regularPoly(100, 100, 50, 6, 0).fill(0x3498db);
g.roundPoly(250, 100, 50, 5, 10).fill(0xe74c3c);
g.chamferRect(350, 50, 100, 80, 15).fill(0x2ecc71);
g.filletRect(500, 50, 100, 80, 15).fill(0x9b59b6);
g.roundShape(
  [
    { x: 50, y: 250, radius: 20 },
    { x: 150, y: 250, radius: 5 },
    { x: 150, y: 350, radius: 10 },
    { x: 50, y: 350, radius: 15 },
  ],
  10,
).fill(0xf39c12);
```

### Holes with cut()

```ts
g.rect(0, 0, 200, 200).fill(0x00ff00).circle(100, 100, 50).cut();
```

`cut()` subtracts current active path from previously drawn fill or stroke. Rules:

- Hole must be **completely inside** target shape. Holes overlapping edges or sitting outside shape will not render correctly, because renderer triangulates with hole as interior boundary.
- `cut()` looks back at up to **last two** instructions. After `fill()` then `stroke()` on same path, first `cut()` adds hole to stroke; second `cut()` adds it to fill underneath.
- After `cut()`, active path resets. Start next shape with `moveTo`, `rect`, etc.
- `cut()` applies to strokes too: `g.rect(...).stroke(...).circle(...).cut()` cuts hole through stroke outline.

Punch multiple holes with one `cut()`: draw several shapes into active path first. Shapes accumulate into one hole path:

```ts
const g = new Graphics();

g.rect(350, 350, 150, 150).fill(0x00ff00);

// Draw three circles into the active path, then cut them all in one call
g.circle(375, 375, 25);
g.circle(425, 425, 25);
g.circle(475, 475, 25);
g.cut();
```

For holes on **separate** filled shapes, give each shape its own `fill()` and matching `cut()`:

```ts
g.rect(0, 0, 100, 100).fill(0x3498db);
g.circle(50, 50, 20).cut(); // hole in the rect

g.rect(120, 0, 100, 100).fill(0xe74c3c);
g.circle(170, 50, 20).cut(); // hole in the second rect
```

`cut()` on shape with existing hole **adds** to hole path, not replacing it. Layers holes additively.

### Paths and complex shapes

```ts
g.moveTo(50, 50)
  .lineTo(200, 50)
  .bezierCurveTo(250, 100, 250, 150, 200, 200)
  .quadraticCurveTo(100, 250, 50, 200)
  .closePath()
  .fill({ color: 0x6c5ce7, alpha: 0.7 })
  .stroke({ width: 2, color: 0xdfe6e9 });
```

Path methods: `moveTo`, `lineTo`, `bezierCurveTo`, `quadraticCurveTo`, `arc`, `arcTo`, `arcToSvg`, `closePath`. Call `beginPath()` to discard current path and start new one.

```ts
// arc(cx, cy, radius, startAngle, endAngle, counterclockwise?)
g.moveTo(80, 50)
  .arc(50, 50, 30, 0, Math.PI)
  .stroke({ width: 4, color: 0x2c3e50 });

// arcTo(x1, y1, x2, y2, radius) — rounded corner between two line segments
g.moveTo(150, 20)
  .arcTo(200, 20, 200, 80, 20)
  .lineTo(200, 80)
  .stroke({ width: 2 });

// arcToSvg(rx, ry, xAxisRotation, largeArcFlag, sweepFlag, x, y) — matches the SVG `A` command
g.moveTo(250, 50).arcToSvg(40, 20, 0, 1, 0, 330, 50).stroke({ width: 2 });
```

### Gradients and patterns

```ts
// Linear gradient
const linear = new FillGradient({
  end: { x: 1, y: 0 },
  colorStops: [
    { offset: 0, color: 0xff0000 },
    { offset: 1, color: 0x0000ff },
  ],
});
g.rect(0, 0, 200, 100).fill(linear);

// Radial gradient. Coordinates are normalized 0-1 in the default "local" space:
// inner circle at the center, outer circle reaching the edges.
const radial = new FillGradient({
  type: "radial",
  center: { x: 0.5, y: 0.5 },
  innerRadius: 0,
  outerCenter: { x: 0.5, y: 0.5 },
  outerRadius: 0.5,
  colorStops: [
    { offset: 0, color: 0xffffff },
    { offset: 1, color: 0x000000 },
  ],
});
g.circle(100, 100, 100).fill(radial);

// Pixel coordinates need textureSpace: "global"; the gradient then spans shapes.
const shared = new FillGradient({
  type: "radial",
  center: { x: 100, y: 100 },
  outerRadius: 100,
  textureSpace: "global",
  colorStops: [
    { offset: 0, color: 0xffffff },
    { offset: 1, color: 0x000000 },
  ],
});
g.rect(0, 0, 200, 200).fill(shared);

const brick = await Assets.load("brick.png");

// Options-object form (preferred)
const pattern = new FillPattern({
  texture: brick,
  repetition: "repeat", // 'repeat' | 'repeat-x' | 'repeat-y' | 'no-repeat'
  textureSpace: "global", // 'global' (default) | 'local'
});

// Legacy positional form is still supported
const pattern2 = new FillPattern(brick, "repeat");

g.rect(0, 120, 200, 100).fill(pattern);
```

`FillGradient` default `type` is `'linear'`, `start {0,0}` to `end {0,1}` (vertical). For radial gradients, set `type: 'radial'` with `center`/`innerRadius` and `outerCenter`/`outerRadius`. `rotation` (radians, default `0`) and `scale` (default `1`) make it elliptical and apply to Graphics only. `textureSpace` defaults to `'local'` (normalized 0-1 shape coordinates); use `'global'` for pixel coordinates shared across shapes.

`FillPattern` takes options object (`{ texture, repetition?, textureSpace? }`) or legacy positional form (`new FillPattern(texture, repetition?)`). `repetition` selects tiling mode. `textureSpace` controls how tiles map to shapes:

- `'global'` (default): tiles repeat continuously across `Graphics` coordinate system, so adjacent shapes share one tiling grid. Best for backgrounds and seamless textures.
- `'local'`: single tile fits each shape's bounds. Combine with `setTransform` to subdivide shape into tile grid.

Note: `FillPattern` defaults `textureSpace` to `'global'`, unlike `'local'` default for texture fills above.

`setTransform(matrix)` copies matrix onto pattern transform to scale, rotate, or offset tiling. Call `setTransform()` with no argument to reset to identity.

Set `textureSpace` and transform on `FillPattern` itself. When pattern is passed inside style object (`fill({ fill: pattern, textureSpace: "local" })`), pattern's own values replace style's `textureSpace` and `matrix`.

### Drawing a texture directly

```ts
const tex = await Assets.load("icon.png");

// Draw the whole texture at (x, y) with optional tint
g.texture(tex, 0xffffff, 20, 20);

// Draw a subregion (dx, dy, dw, dh)
g.texture(tex, 0xff0000, 100, 20, 64, 64);
```

`Graphics.texture(texture, tint?, dx?, dy?, dw?, dh?)` draws single textured rect without `fill()`. For icons that don't need full sprite lifecycle.

### GraphicsContext sharing

```ts
const ctx = new GraphicsContext().rect(0, 0, 50, 50).fill(0xff0000);

const g1 = new Graphics(ctx);
const g2 = new Graphics(ctx);
g2.x = 100;
```

Or assign after construction: `g.context = existingContext`.

### SVG import and export

Parse SVG markup into active context with `svg()`:

```ts
g.svg(`<svg viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="40" fill="red"/>
</svg>`);
```

`svg()` parses `<path>` (with `fill-rule="evenodd"` holes), `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<polygon>`, `<polyline>`, and `<g>` grouping. Styling from `fill`, `stroke`, `stroke-width`, `fill-opacity`, `stroke-opacity`, and `opacity`, as attributes or inline `style`. `<linearGradient>` and `<radialGradient>` definitions in `<defs>` become `FillGradient`s applied through `url(#id)`. `gradientUnits` maps to `textureSpace`; percentage coordinates accepted. Not supported: `transform` attributes, `<style>` blocks, `stroke-linecap`/`stroke-linejoin`/`stroke-dasharray`, `gradientTransform`, `spreadMethod`, `stop-opacity`, `<text>`, `<image>`, `<use>`, `<clipPath>`, `<mask>`, `<pattern>`. Unsupported elements log warning, get skipped. Complex hole geometries may render inaccurately, because Pixi's triangulation is performance-optimized.

Serialize a `Graphics` or `GraphicsContext` back to self-contained SVG document string with `graphicsContextToSvg`:

```ts
import { Graphics, graphicsContextToSvg } from "pixi.js";

const g = new Graphics()
  .rect(0, 0, 100, 50)
  .fill({ color: 0xff0000 })
  .circle(150, 25, 25)
  .stroke({ color: 0x0000ff, width: 4 });

const svgString = graphicsContextToSvg(g, 2);
```

`graphicsContextToSvg(source, precision = 2)` is pure: reads context instructions, returns complete `<svg>` string with auto-computed `viewBox`. Pass a `Graphics` or `GraphicsContext`; `precision` controls decimal places on emitted coordinates. Exports every shape-then-fill primitive (advanced ones like `regularPoly`/`filletRect` fall back to shape-path), all path methods, stroke attributes (`width`, `cap`, `join`, `miterLimit`), `fill-opacity`/`stroke-opacity`, and `FillGradient` (linear and radial) via `<defs>` block. Holes collapse into one `<path>` with `fill-rule="evenodd"`. `FillPattern` and texture fills have no SVG equivalent: patterns fall through to fill's solid `color`, and `texture()` instructions skipped. Exported markup roundtrips through `g.svg(...)` without cleanup, so shapes can be stored and reimported into another `Graphics`.

### Reusing a GraphicsPath

```ts
const arrow = new GraphicsPath()
  .moveTo(0, 0)
  .lineTo(40, 0)
  .lineTo(40, -10)
  .lineTo(60, 10)
  .lineTo(40, 30)
  .lineTo(40, 20)
  .lineTo(0, 20)
  .closePath();

g.path(arrow).fill(0x3498db);
g.translateTransform(80, 0).path(arrow).fill(0xe74c3c);
```

`Graphics.path(graphicsPath)` (and `GraphicsContext.path()`) appends prebuilt `GraphicsPath` onto active path. Build once, draw many times.

### Draw-time transforms

`Graphics` has own transform stack used **while drawing**, separate from `Container` transform applied to rendered output. Drawing methods renamed to avoid clashing with `Container.rotation`, `Container.scale`, `Container.position`:

| Drawing transform | Container transform |
| --- | --- |
| `g.rotateTransform(angle)` | `g.rotation` |
| `g.scaleTransform(x, y?)` | `g.scale.set(x, y)` |
| `g.translateTransform(x, y?)` | `g.position.set(x, y)` |
| `g.setTransform(matrix)` or `setTransform(a,b,c,d,tx,ty)` | `g.setFromMatrix(matrix)` |
| `g.transform(matrix)` or `transform(a,b,c,d,tx,ty)` | n/a |
| `g.getTransform()` / `g.resetTransform()` | n/a |

```ts
const g = new Graphics();

g.translateTransform(100, 100)
  .rotateTransform(Math.PI / 4)
  .rect(-25, -25, 50, 50)
  .fill(0x3498db);

// The square is rotated 45 degrees as it is added to the geometry.
// Setting g.rotation later rotates the entire Graphics on screen.
```

Drawing transform affects all later shape and path commands. Use `save()`/`restore()` to scope it.

### State save/restore

```ts
g.save();
g.translateTransform(100, 100);
g.rotateTransform(Math.PI / 4);
g.rect(0, 0, 50, 50).fill(0xff0000);
g.restore();
```

`save()` pushes drawing transform, fill style, and stroke style onto stack; `restore()` pops them. `Graphics` exposes `save`/`restore` directly, mirroring underlying `GraphicsContext` calls.

### Default styles via setFillStyle / setStrokeStyle

```ts
g.setFillStyle({ color: 0x3498db, alpha: 0.8 }).setStrokeStyle({
  width: 2,
  color: 0x2c3e50,
});

g.rect(0, 0, 100, 100).fill().stroke();
g.circle(150, 50, 40).fill().stroke();
```

`setFillStyle()` and `setStrokeStyle()` set default style for subsequent `fill()` / `stroke()` calls when no argument is passed. Read or replace current style anytime via `fillStyle` and `strokeStyle` getters/setters. Override library-wide defaults by mutating `GraphicsContext.defaultFillStyle` and `GraphicsContext.defaultStrokeStyle` once at startup.

### Hit testing

```ts
const g = new Graphics().star(100, 100, 5, 60, 30).fill(0xf39c12);
g.eventMode = "static";
g.on("pointermove", (e) => {
  if (g.containsPoint(g.toLocal(e.global))) {
    /* over the star, not just its bbox */
  }
});
```

`Graphics.containsPoint(pointInLocalSpace)` runs topology-aware test against every filled and stroked shape in context, including holes. Convert global pointer coordinates with `toLocal()` first. Stroked shapes hit-test against drawn stroke: hit band follows stroke's `width` and `alignment` (`1` inside, `0.5` centered, `0` outside), independent of polygon's winding order.

### Cloning, clearing, and bounds

```ts
const g = new Graphics().rect(0, 0, 100, 100).fill(0xff0000);

const shallow = g.clone(); // shares the same GraphicsContext
const deep = g.clone(true); // creates an independent context

console.log(g.bounds.width); // 100 - geometry bounds before transforms

g.clear(); // wipes active path, instructions, and transform; fill/stroke styles persist
```

- `clone()` returns new `Graphics` sharing source context (cheap, geometry reused). Both update together if context changes.
- `clone(true)` clones context too, so new `Graphics` can be edited independently.
- `bounds` returns geometry bounds before `Container` transform. Useful for layout decisions.
- `clear()` resets context so same `Graphics` can be reused. See **Common Mistakes** below for when to clear versus keep stable geometry.

### GraphicsContext utilities

| Member | Behavior |
| --- | --- |
| `ctx.beginPath()` | Discard current active path, start new one; committed instructions unaffected. |
| `ctx.setFillStyle(style)` / `ctx.fillStyle` | Set or read default fill style for subsequent shapes without calling `fill()`. |
| `ctx.setStrokeStyle(style)` / `ctx.strokeStyle` | Set or read default stroke style for subsequent shapes without calling `stroke()`. |
| `ctx.bounds` | Cached geometry bounds across all fill/stroke/texture instructions. |
| `ctx.clear()` | Wipe instructions, active path, and drawing transform. |
| `ctx.clone()` | Deep copy: instructions, active path, transform, styles, stack. |
| `ctx.containsPoint(point)` | Topology-aware hit test against all filled and stroked shapes (including holes). |
| `ctx.batchMode` | One of `'auto'`, `'batch'`, `'no-batch'`. Forces or disables batching for shapes in this context. |
| `ctx.customShader` | Assign a `Shader` to override default graphics shader. |
| `GraphicsContext.defaultFillStyle` | Static fallback when `fill()` has no arguments and no fill style is set. |
| `GraphicsContext.defaultStrokeStyle` | Static fallback when `stroke()` has no arguments and no stroke style is set. |

`GraphicsContext` is an `EventEmitter` emitting `update`, `destroy`, and `unload` events. Subscribe via `ctx.on('update' | 'destroy' | 'unload', cb)` when tooling or pools must react to context lifecycle changes.

## Common Mistakes

### [CRITICAL] Using v7 beginFill/drawRect/endFill

Wrong:

```ts
const g = new Graphics().beginFill(0xff0000).drawRect(0, 0, 100, 100).endFill();
```

Correct:

```ts
const g = new Graphics().rect(0, 0, 100, 100).fill(0xff0000);
```

v8 replaced "set style, draw, end" with "draw shape, then apply style". `beginFill`/`endFill` remain only as deprecated shims logging a v8 deprecation warning.


### [CRITICAL] Using old shape method names

Wrong:

```ts
g.drawCircle(50, 50, 25);
```

Correct:

```ts
g.circle(50, 50, 25);
```

All `draw*` methods renamed in v8 (old names remain as deprecated shims that log a warning): `drawRect` → `rect`, `drawCircle` → `circle`, `drawEllipse` → `ellipse`, `drawPolygon` → `poly`, `drawRoundedRect` → `roundRect`, `drawStar` → `star`.


### [CRITICAL] Using lineStyle instead of stroke

Wrong:

```ts
g.lineStyle(2, 0xffffff);
g.drawRect(0, 0, 100, 100);
```

Correct:

```ts
g.rect(0, 0, 100, 100).stroke({ width: 2, color: 0xffffff });
```

`lineStyle` is deprecated in v8 (remains as shim that logs a warning). Use `stroke()` after drawing shape.


### [HIGH] Using beginHole/endHole for holes

Wrong:

```ts
g.beginFill(0x00ff00)
  .drawRect(0, 0, 100, 100)
  .beginHole()
  .drawCircle(50, 50, 20)
  .endHole()
  .endFill();
```

Correct:

```ts
g.rect(0, 0, 100, 100).fill(0x00ff00).circle(50, 50, 20).cut();
```

`beginHole`/`endHole` replaced by `cut()`.


### [HIGH] Using GraphicsGeometry instead of GraphicsContext

Wrong:

```ts
const geom = g.geometry;
const clone = new Graphics(geom);
```

Correct:

```ts
const ctx = new GraphicsContext().rect(0, 0, 100, 100).fill(0xff0000);
const g1 = new Graphics(ctx);
const g2 = new Graphics(ctx);
```

`GraphicsGeometry` replaced by `GraphicsContext` in v8. No `.geometry` property.


### [HIGH] Destroying a shared GraphicsContext unexpectedly

```ts
const ctx = new GraphicsContext().rect(0, 0, 50, 50).fill(0xff0000);
const g1 = new Graphics(ctx);
const g2 = new Graphics(ctx);

g1.destroy({ context: true }); // g2 is left holding a destroyed context
```

Destroying shared `GraphicsContext` does not destroy other `Graphics` using it. They keep a reference to destroyed context and stop updating or rendering correctly. When context is passed via constructor, `destroy()` with no args preserves context and detaches instance from it; use `destroy({ context: false })` to be explicit. Only destroy context when all sharing instances are done with it. Self-owned context (not passed via constructor) is still destroyed by `destroy()` with no args.


### [HIGH] Clearing and redrawing Graphics every frame

Graphics are meant to be stable, not dynamic. Calling `clear()` and redrawing every frame rebuilds GPU geometry each time. For dynamic visuals:

- Use `Sprite` with pre-rendered textures and transform changes.
- Use `cacheAsTexture(true)` for complex static graphics.
- For real-time shape changes, consider `Mesh` with custom geometry updates.

Opposite of HTML Canvas 2D, where redrawing each frame is normal. Treat `Graphics` more like SVG elements than canvas draw calls.


### [MEDIUM] Do not nest children inside a Graphics

`Graphics` sets `allowChildren = false`. Adding children logs a deprecation warning and will be a hard error in a future version. Wrap multiple graphics alongside other leaves in plain `Container`:

```ts
const group = new Container();
group.addChild(graphics, sprite);
```


## API Reference

- [Graphics](https://pixijs.download/release/docs/scene.Graphics.html.md)
- [GraphicsOptions](https://pixijs.download/release/docs/scene.GraphicsOptions.html.md)
- [GraphicsContext](https://pixijs.download/release/docs/scene.GraphicsContext.html.md)
- [GraphicsPath](https://pixijs.download/release/docs/scene.GraphicsPath.html.md)
- [graphicsContextToSvg](https://pixijs.download/release/docs/scene.graphicsContextToSvg.html.md)
- [FillGradient](https://pixijs.download/release/docs/scene.FillGradient.html.md)
- [FillPattern](https://pixijs.download/release/docs/scene.FillPattern.html.md)
- [FillStyle](https://pixijs.download/release/docs/scene.FillStyle.html.md)
- [FillInput](https://pixijs.download/release/docs/scene.FillInput.html.md)
