---
name: pixijs-performance
description: "Use this skill when profiling or optimizing a PixiJS v8 app for FPS, draw calls, or GPU memory. Covers destroy patterns (cacheAsTexture(false), releaseGlobalResources), GCSystem and TextureGCSystem, PrepareSystem, object pooling, batching rules, BitmapText for dynamic text, culling (Culler, CullerPlugin, cullable, cullArea), resolution/antialias tradeoffs, low-level wins (transient MSAA render textures, render bundles, partial buffer updates). Triggers on (in PixiJS apps): low FPS, jank, draw calls, batching, object pool, GCSystem, PrepareSystem, Culler, cacheAsTexture, GPU memory leak, destroy patterns, render bundle, transient, MSAA, Buffer.update, WebGPU performance, TexturePool, repeatEdgePixels, bind group."
license: MIT
---

Profile first, with browser DevTools Performance and GPU profiling. Once bottleneck is found, apply matching pattern below (destroy, pool, batch, cache, or cull).

## Quick Start

```ts
container.cacheAsTexture(true);
container.updateCacheTexture();
container.cacheAsTexture(false);
container.destroy({ children: true });

import { CullerPlugin, extensions } from "pixi.js";
extensions.add(CullerPlugin);

offscreenContainer.cullable = true;
offscreenContainer.cullArea = new Rectangle(0, 0, 256, 256);

// Tune GC via init options (ms). The `textureGC.*` properties are
// deprecated since 8.15.0 — use these on the Application init instead.
await app.init({ gcMaxUnusedTime: 60_000, gcFrequency: 30_000 });
```

**Related skills:** `pixijs-scene-container` (destroy options), `pixijs-scene-container` (`references/scene-core-concepts.md`: render groups, layers, culling), `pixijs-scene-text` (BitmapText for dynamic content), `pixijs-assets` (atlasing).

## Core Patterns

### Proper destroy with cleanup

```ts
import { Sprite, Assets } from "pixi.js";

const texture = await Assets.load("character.png");
const sprite = new Sprite(texture);

// Destroy sprite only (preserve texture for reuse)
sprite.destroy();

// Destroy sprite AND its texture
sprite.destroy({ children: true, texture: true, textureSource: true });
```

Fully done with loaded asset:

```ts
Assets.unload("character.png");
```

Removes it from cache and unloads GPU resource.

Custom rendering objects clean up same way: call `geometry.destroy()` and `renderTarget.destroy()` on ones you create. Destroying container also destroys its render group's cached batchers.

### Application destroy/recreate cycle

```ts
import { Application } from "pixi.js";

// Correct destroy that cleans global pools
app.destroy({ releaseGlobalResources: true });

const newApp = new Application();
await newApp.init({ width: 800, height: 600 });
```

### Texture garbage collection

`GCSystem` auto-collects unused textures and GPU resources (including WebGPU bind groups). Defaults: check every 30 seconds, remove resources idle 60 seconds. Both options take milliseconds.

```ts
import { Application } from "pixi.js";

const app = new Application();

await app.init({
  gcActive: true,
  gcMaxUnusedTime: 120000, // idle time before cleanup in ms (default: 60000)
  gcFrequency: 60000, // check interval in ms (default: 30000)
});
```

Manual control:

```ts
texture.source.unload(); // immediate GPU memory release
```

### PrepareSystem for GPU upload

Upload textures and graphics to GPU before rendering to avoid first-frame hitches:

```ts
import "pixi.js/prepare";
import { Application, Assets } from "pixi.js";

const app = new Application();
await app.init();

// Don't render until assets are uploaded
app.stop();

const texture = await Assets.load("large-scene.png");

// Upload to GPU ahead of time
await app.renderer.prepare.upload(app.stage);

// Now rendering won't hitch on first frame
app.start();
```

`prepare.upload()` accepts Container (uploads all textures, text, and graphics in subtree) or individual resources.

### cacheAsTexture for performance

`cacheAsTexture()` renders container subtree to one texture, cutting draw calls for complex static content. Internally creates render group and caches result.

**When to use:**

- Many static children (UI panels, decorative backgrounds, complex Graphics)
- Expensive filters (caches filter result)
- Large, rarely changing subtrees

**Tradeoffs:**

- Cached texture costs GPU memory (grows with container size)
- Max texture size depends on GPU (typically 4096x4096 or larger). No PixiJS property exposes it; query backend directly:
- Must call `updateCacheTexture()` after modifying children
- Fragile with masks (masking basics: `pixijs-scene-container`, `references/scene-core-concepts.md`)

```ts
import type { WebGLRenderer, WebGPURenderer } from "pixi.js";

// Available after renderer/app init on both backends
const maxTextureSize = renderer.name === "webgpu"
  ? (renderer as WebGPURenderer).gpu.device.limits.maxTextureDimension2D
  : (renderer as WebGLRenderer).gl.getParameter(WebGL2RenderingContext.MAX_TEXTURE_SIZE);
```

```ts
import { Container, Sprite } from "pixi.js";

const panel = new Container();
// ... add many static children ...

panel.cacheAsTexture(true);

// With options
panel.cacheAsTexture({ resolution: 2, antialias: true });

// Refresh after changes
panel.updateCacheTexture();

// MUST disable before destroying (see Common Mistakes below)
panel.cacheAsTexture(false);
panel.destroy();
```

**Avoid:** repeated on/off toggling (re-caching negates benefit), sparse containers (negligible gain), containers larger than 4096x4096.

### Object recycling

Reuse objects by changing properties, not destroy/recreate:

```ts
import { Sprite, Container, Texture } from "pixi.js";

class BulletPool {
  private _pool: Sprite[] = [];
  private _container: Container;

  constructor(container: Container) {
    this._container = container;
  }

  public get(texture: Texture): Sprite {
    let bullet = this._pool.pop();

    if (!bullet) {
      bullet = new Sprite(texture);
      this._container.addChild(bullet);
    }

    bullet.texture = texture;
    bullet.position.set(0, 0);
    bullet.rotation = 0;
    bullet.scale.set(1);
    bullet.alpha = 1;
    bullet.tint = 0xffffff;
    bullet.blendMode = "normal";
    bullet.visible = true;
    return bullet;
  }

  public release(bullet: Sprite): void {
    bullet.visible = false;
    this._pool.push(bullet);
  }
}
```

GPU resources stay allocated; only scene graph visibility changes.

### Batching optimization

PixiJS batches similar consecutive objects into one draw call. Batch breaks on:

- Object type change (Sprite vs Graphics)
- Texture source change (beyond per-batch texture limit, typically 16)
- Blend mode change
- Topology change

Optimize draw order:

```ts
import { Sprite, Graphics, Container } from "pixi.js";

// 4 draw calls: type alternates
const bad = new Container();
bad.addChild(new Sprite(t1));
bad.addChild(new Graphics().rect(0, 0, 10, 10).fill(0xff0000));
bad.addChild(new Sprite(t2));
bad.addChild(new Graphics().rect(0, 0, 10, 10).fill(0x00ff00));

// 2 draw calls: types grouped
const good = new Container();
good.addChild(new Sprite(t1));
good.addChild(new Sprite(t2));
good.addChild(new Graphics().rect(0, 0, 10, 10).fill(0xff0000));
good.addChild(new Graphics().rect(0, 0, 10, 10).fill(0x00ff00));
```

Same for blend modes: `screen/normal/screen/normal` = 4 draws; `screen/screen/normal/normal` = 2 draws.

### Spritesheets over individual textures

```ts
import { Assets, Sprite } from "pixi.js";

// Load a spritesheet (single texture atlas)
const sheet = await Assets.load("game-atlas.json");

// All frames share one GPU texture; enables batching
const hero = new Sprite(sheet.textures["hero.png"]);
const enemy = new Sprite(sheet.textures["enemy.png"]);
const coin = new Sprite(sheet.textures["coin.png"]);
```

Use `@0.5x` filename suffix on half-resolution sheets so PixiJS auto-scales them.

### Text performance

Text and HTMLText re-render to canvas and re-upload to GPU on every change. Never update them unconditionally per frame:

```ts
import { BitmapText, Text } from "pixi.js";

// Wrong: re-renders canvas + GPU upload every frame
app.ticker.add(() => {
  scoreText.text = `Score: ${score}`;
});

// Correct: use BitmapText for frequently changing content
const scoreText = new BitmapText({
  text: "Score: 0",
  style: { fontFamily: "Arial", fontSize: 24, fill: 0xffffff },
});

app.ticker.add(() => {
  scoreText.text = `Score: ${score}`;
});
```

BitmapText draws from pre-generated glyph atlas. Updates only reposition quads: no canvas re-render, no GPU upload. Use for scores, timers, counters, anything changing often.

If canvas Text is required, update only when value changes:

```ts
app.ticker.add(() => {
  const next = `Score: ${score}`;
  if (scoreText.text !== next) {
    scoreText.text = next;
  }
});
```

Text resolution defaults to renderer resolution. Lower it per text via `text.resolution = 1` to cut GPU memory on high-DPI displays.

### Graphics performance

Graphics are fastest when shape doesn't change (transforms, alpha, tint are fine). Small Graphics (under ~100 points) batch like Sprites. Complex Graphics with hundreds of shapes are slow; convert to textures:

```ts
import { Graphics, Sprite } from "pixi.js";

const complex = new Graphics();
// ... draw complex shape ...

// Render once to texture, use as Sprite
const texture = app.renderer.generateTexture(complex);
const sprite = new Sprite(texture);
```

### Culling

With `cullable` set, PixiJS skips rendering objects outside visible area. Off by default: trades CPU cost (bounds checking) for GPU savings. Culling only runs with `CullerPlugin` registered:

```ts
import { extensions, CullerPlugin, Culler, Rectangle } from "pixi.js";

extensions.add(CullerPlugin); // before Application.init

// Enable on objects that may be off-screen
sprite.cullable = true;

// Optional: a pre-computed cull rectangle avoids per-frame bounds calculation.
// Without cullArea, the Culler uses the object's global bounds instead.
sprite.cullArea = new Rectangle(0, 0, 800, 600);

// Skip culling an entire subtree (static UI, always visible)
uiRoot.cullableChildren = false;

// Or cull manually without the plugin:
Culler.shared.cull(app.stage, app.renderer.screen);
```

`cullableChildren` on container stops culler recursing into descendants; big win for static UI panels with many children. `Culler.shared.cull(container, rect)` runs same logic manually for custom render pipelines. Cull when GPU-bound. Avoid it when CPU-bound: per-object bounds check adds overhead.

### Resolution and antialias tradeoffs

```ts
import { Application } from "pixi.js";

const app = new Application();

// Mobile-friendly: lower resolution, no antialias
await app.init({
  resolution: 1,
  antialias: false,
  backgroundAlpha: 1, // opaque background is faster
});
```

`resolution: 2` quadruples pixel count; on mobile it can halve frame rate.

### Low-level rendering optimizations

```ts
import { RenderTexture } from "pixi.js";

// single-pass antialiased render texture: also discard its MSAA depth/stencil at end of pass
const rt = RenderTexture.create({ width: 1024, height: 1024, antialias: true, transient: true });

// upload only the changed byte range of a large buffer (also works on WebGL)
buffer.update(changedBytes, offsetBytes);

// upload only a texel range of a data texture (end is exclusive)
bufferImageSource.update(100, 116);
```

On tile-based WebGPU GPU (`renderer.device.extensions.tileBased`: every phone GPU and Apple silicon), every antialiased target already discards its multisample colour buffer instead of writing it back. A pass reopening the target restores that buffer from resolved image. Buffer may not be allocated at all when `renderer.device.extensions.transientAttachment` is true. `transient: true` also discards multisample depth/stencil buffer, and colour buffer on other GPUs. Only use it on textures rendered in single pass and never re-entered with `clear: false` or wrapped by filter or mask. For static custom draw sequences on WebGPU, record render bundle once and replay it each frame (custom rendering not covered by these skills).

### Stagger bulk texture destruction

```ts
function staggerDestroy(textures: Texture[], perFrame: number = 5): void {
  let index = 0;
  const ticker = app.ticker;

  const destroy = () => {
    const end = Math.min(index + perFrame, textures.length);

    for (let i = index; i < end; i++) {
      textures[i].destroy(true);
    }
    index = end;

    if (index >= textures.length) {
      ticker.remove(destroy);
    }
  };

  ticker.add(destroy);
}
```

### Filters and masks cost

- Set `container.filterArea = new Rectangle(x, y, w, h)` when bounds are known. Without it, PixiJS measures bounds every frame.
- Release filter memory: `container.filters = null`.
- Full-screen filter textures pool at screen size. Padding (`BlurFilter` default) pushes request past screen, up to next power of two. Set `repeatEdgePixels: true` on full-screen blurs to keep them screen-sized.
- Mask cost (cheapest to most expensive): axis-aligned Rectangle masks (scissor rect) < Graphics masks (stencil buffer) < Sprite/alpha masks (filter pipeline). Hundreds of masks slow rendering regardless of type; prefer rectangle masks for axis-aligned bounds.
- Set `interactiveChildren = false` on containers with no interactive children.
- Set `hitArea` on large containers to skip recursive child hit testing.

### Safe destroy order

Remove from scene before destroying:

```ts
parent.removeChild(sprite);
sprite.destroy();
```

Destroying while render pipeline still holds reference causes null-pointer crashes. If destruction must happen mid-frame, defer it:

```ts
app.ticker.addOnce(() => {
  parent.removeChild(sprite);
  sprite.destroy();
});
```

## Common Mistakes

### [CRITICAL] App destroy without releaseGlobalResources

Wrong:

```ts
app.destroy();
const newApp = new Application();
```

Correct:

```ts
app.destroy({ releaseGlobalResources: true });
const newApp = new Application();
```

Without this flag, old app's stale pooled batches and textures stay in global pools. New app reuses them, causing flickering and visual corruption.

### [HIGH] Interleaving object types in scene graph

Group same object types in child order to minimize batch breaks. Same for blend modes.

### [HIGH] Destroying and recreating objects instead of recycling

Destroy/recreate is expensive: deallocates GPU resources, triggers garbage collection, requires fresh GPU uploads. Reuse objects by updating `texture`, `position`, `visible`, and other properties. Pool frequently spawned/despawned entities.

### [HIGH] Loading many individual textures instead of spritesheets

Each separate texture needs own GPU upload and memory slot, and breaks batching once per-batch texture limit is reached. Spritesheets pack textures into atlases. Avoid textures over 4096px on either axis; they fail on some mobile GPUs.

### [HIGH] Updating Text or HTMLText every frame

Each update re-renders full string to canvas and uploads to GPU. At 60fps, overhead is massive.

### [HIGH] Using complex Graphics instead of textures

Hundreds of complex Graphics objects render slowly. Render complex static shapes to texture with `renderer.generateTexture()` and display as Sprite.

### [MEDIUM] Not staggering bulk texture destruction

Destroying dozens of textures in one frame causes visible freeze. Spread destruction across frames (e.g., 5 per frame via ticker callback).

### [MEDIUM] Not using PrepareSystem for large scenes

Without `renderer.prepare.upload()`, textures upload to GPU on first render, causing frame hitches. For loading screens or scene transitions, upload before displaying. Requires `import 'pixi.js/prepare'` (not included even in default bundle; always import it explicitly).

### [MEDIUM] Using high resolution or antialias without profiling

`resolution: 2` quadruples pixel count. `antialias: true` adds GPU cost. Both degrade mobile performance. Always profile on target hardware before enabling. Source: performance-tips.md

## API Reference

- [GCSystem](https://pixijs.download/release/docs/rendering.GCSystem.html.md)
- [TextureGCSystem](https://pixijs.download/release/docs/rendering.TextureGCSystem.html.md)
- [RenderableGCSystem](https://pixijs.download/release/docs/rendering.RenderableGCSystem.html.md)
- [PrepareSystem](https://pixijs.download/release/docs/rendering.PrepareSystem.html.md)
- [Culler](https://pixijs.download/release/docs/scene.Culler.html.md)
- [CullerPlugin](https://pixijs.download/release/docs/app.CullerPlugin.html.md)
- [Pool](https://pixijs.download/release/docs/utils.Pool.html.md)
