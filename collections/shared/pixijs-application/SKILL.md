---
name: pixijs-application
description: "Use this skill when creating and configuring a PixiJS v8 Application. Covers new Application() + async app.init() options (width, height, background, antialias, resolution, autoDensity, preference, resizeTo, autoStart, sharedTicker, canvas, useBackBuffer, powerPreference, eventFeatures, accessibilityOptions, gcActive, bezierSmoothness, webgl/webgpu/canvasOptions per-renderer overrides), app.stage/renderer/canvas/screen/domContainerRoot access, ResizePlugin, TickerPlugin, CullerPlugin (cullable, cullArea), custom ApplicationPlugin via ExtensionType.Application, start/stop lifecycle, and app.destroy() with releaseGlobalResources. Triggers on (in PixiJS code): PixiJS Application, app.init, app.stage, app.renderer, app.canvas, app.screen, app.domContainerRoot, ApplicationOptions, ApplicationPlugin, ExtensionType.Application, resizeTo, sharedTicker, skipExtensionImports, preferWebGLVersion, preserveDrawingBuffer, cullable, CullerPlugin, app.start, app.stop, app.destroy, releaseGlobalResources."
license: MIT
---

`Application`: convenience wrapper owning renderer, root `stage` Container, canvas, Ticker/Resize plugins. All configuration goes to async `app.init()`, which creates renderer via `autoDetectRenderer`.

## Quick Start

```ts
import { Application } from "pixi.js";

const app = new Application();

await app.init({
  resizeTo: window,
  background: "#1099bb",
  antialias: true,
  preference: "webgl",
  autoDensity: true,
  resolution: window.devicePixelRatio,
});

document.body.appendChild(app.canvas);
```

**Related skills:** `pixijs-core-concepts` (renderers, render pipeline), `pixijs-ticker` (render loop detail), `pixijs-scene-container` (working with `app.stage`). Non-browser setups (Web Worker, SSR, strict CSP) summarized in `pixijs-core-concepts` (Decision guide).

## Core Patterns

### Lifecycle: construct, init, render, destroy

```ts
import { Application } from "pixi.js";

const app = new Application();

await app.init({ width: 800, height: 600 });
document.body.appendChild(app.canvas);

// ... run scene, ticker drives app.render() automatically ...

app.destroy(
  { removeView: true, releaseGlobalResources: true },
  { children: true, texture: true, textureSource: true },
);
```

- `new Application()` allocates instance but creates nothing.
- `app.init(options)` is async. Builds renderer, wires plugins.
- TickerPlugin calls `app.render()` every frame once init resolves (unless `autoStart: false`).
- `app.destroy(rendererDestroyOptions, stageDestroyOptions)` — first argument forwards to `renderer.destroy()`. Pass `true` or `{ removeView: true }` to remove canvas from DOM. Add `releaseGlobalResources: true` to drain global pools (batches, texture caches) when re-creating app in same tab. Omitting it usually causes flickering and stale textures after re-init (see `pixijs-performance`).

### Key init options

```ts
await app.init({
  width: 800,
  height: 600,
  background: 0x1099bb,
  backgroundAlpha: 1,

  antialias: true,
  resolution: window.devicePixelRatio,
  autoDensity: true,

  preference: "webgpu",

  autoStart: true,
  sharedTicker: false,

  resizeTo: window,

  canvas: document.querySelector("#game-canvas") as HTMLCanvasElement,
});
```

Full option list in [references/application-options.md](references/application-options.md): view/canvas, background, renderer preference (including array form), ticker, resize, culler, events, accessibility, WebGL/WebGPU context flags, Graphics bezier smoothness, GC, and per-renderer overrides (`webgl` / `webgpu` / `canvasOptions`).

### Application properties

```ts
app.stage; // root Container; add all display objects here
app.renderer; // the WebGL/WebGPU/Canvas renderer instance
app.canvas; // the HTMLCanvasElement (insert it into the DOM yourself)
app.screen; // Rectangle describing the visible area in CSS pixels
app.domContainerRoot; // HTMLDivElement that holds DOMContainer overlays
```

`app.stage` is plain `Container`. Scene graph detail (transforms, addChild, destroy): see `pixijs-scene-container`. Renderer-level operations (extract, generateTexture, custom systems): see `pixijs-core-concepts`. Custom render pipes not covered by these skills; see [RenderPipe API](https://pixijs.download/release/docs/rendering.RenderPipe.html.md). Append `app.domContainerRoot` next to `app.canvas` to pin DOM elements to scene nodes (see [DOMContainer API](https://pixijs.download/release/docs/scene.DOMContainer.html.md); requires `import 'pixi.js/dom'`).

### ResizePlugin

Set `resizeTo` at init (or reassign `app.resizeTo` later). Plugin then listens for `resize` event and calls `renderer.resize()` with target element's client size. Combine with `autoDensity: true` and `resolution: window.devicePixelRatio` for high-DPI output.

```ts
await app.init({ resizeTo: window });

app.resizeTo = document.querySelector("#game-container") as HTMLElement;

app.resize(); // immediate resize to the target's current size
app.queueResize(); // defer the resize to the next animation frame
app.cancelResize(); // drop a pending queueResize
```

Plugin keeps canvas matched to target; `app.screen` and `app.canvas.width/height` update in response. Read them after resize to place UI.

- `app.queueResize()` — coalesces rapid calls by deferring to next frame. `window.resize` listener uses it internally to skip redundant work.
- `app.cancelResize()` — cancels queued resize. Call before tearing down own layout code that triggered `queueResize`.

### Ticker basics

TickerPlugin creates `app.ticker` and registers `app.render()` on it at `UPDATE_PRIORITY.LOW`. Control loop with `app.start()`/`app.stop()`. Add callbacks with `app.ticker.add` / `app.ticker.addOnce`:

```ts
app.ticker.add((ticker) => {
  sprite.rotation += 0.01 * ticker.deltaTime;
});

app.ticker.addOnce(() => {
  console.log("runs once on the next frame, then removes itself");
});

app.stop(); // pause the render loop (e.g. tab hidden)
app.start(); // resume
```

Callback receives `Ticker` instance. Read `ticker.deltaTime` for frame-rate-independent multiplier (~1.0 at 60fps), `ticker.deltaMS` for real milliseconds, `ticker.FPS` for current frame rate. See `pixijs-ticker` for priorities, FPS capping, `onRender`, shared vs private tickers, and v8 callback signature change.

### Manual render loop

```ts
await app.init({ autoStart: false, width: 800, height: 600 });
document.body.appendChild(app.canvas);

function frame() {
  updateScene();
  app.render();
  requestAnimationFrame(frame);
}
frame();
```

`autoStart: false` keeps TickerPlugin from auto-starting ticker. Call `app.render()` yourself (or `app.renderer.render({ container: app.stage })`, same effect). For registered ticker callbacks to fire, call `app.ticker.update()` in loop. TickerPlugin's registered callback already renders stage, so then omit separate `app.render()` call.

### CullerPlugin (opt-in)

CullerPlugin skips rendering containers outside `app.renderer.screen`. Not registered by default. Add it before creating app:

```ts
import {
  Application,
  Container,
  Sprite,
  extensions,
  CullerPlugin,
  Rectangle,
} from "pixi.js";

extensions.add(CullerPlugin);

const app = new Application();
await app.init({ width: 800, height: 600 });

const world = new Container();
world.cullable = true; // this container is culled when its bounds leave the screen
world.cullableChildren = true; // default; set `false` to skip recursing into children

const tile = Sprite.from("tile.png");
tile.cullable = true;
world.addChild(tile);
app.stage.addChild(world);
```

Containers not culled unless `cullable` set. Override default bounds check with `container.cullArea = new Rectangle(x, y, w, h)` when child bounds are expensive to compute. Plugin wraps `app.render()` so `Culler.shared.cull(app.stage, app.renderer.screen)` runs before every frame. See `pixijs-performance` for when culling pays off.

### Custom Application plugins

Extend `Application` by registering class with `static init`, `static destroy`, and `static extension = ExtensionType.Application`. Both run with `this` bound to Application instance, so `this.renderer` and `this.stage` are available.

```ts
import {
  Application,
  ExtensionType,
  extensions,
  type ApplicationOptions,
} from "pixi.js";

class FpsOverlay {
  public static extension = ExtensionType.Application;

  public static init(this: Application, options: Partial<ApplicationOptions>) {
    // runs inside app.init() after the renderer is created
    // attach props/methods to `this` to expose them on the app
  }

  public static destroy(this: Application) {
    // runs inside app.destroy() — tear down anything you attached
  }
}

extensions.add(FpsOverlay);
```

Plugins initialize in registration order, destroy in reverse. For typed plugin options, extend `PixiMixins.ApplicationOptions`:

```ts
declare global {
  namespace PixiMixins {
    interface ApplicationOptions {
      fpsOverlay?: { visible?: boolean };
    }
  }
}

await app.init({ fpsOverlay: { visible: true } });
```

Built-in `ResizePlugin`, `TickerPlugin`, and opt-in `CullerPlugin` use same contract. With `skipExtensionImports: true`, register needed built-ins yourself (`extensions.add(ResizePlugin, TickerPlugin)`).

## Common Mistakes

### [CRITICAL] Passing options to the constructor

Wrong:

```ts
const app = new Application({ width: 800, height: 600 });
document.body.appendChild(app.canvas);
```

Correct:

```ts
const app = new Application();
await app.init({ width: 800, height: 600 });
document.body.appendChild(app.canvas);
```

In v8 `Application` constructor takes no arguments. Options passed there are ignored and log deprecation warning. Renderer is only created inside async `init()` call.


### [HIGH] Using app.view instead of app.canvas

Wrong:

```ts
document.body.appendChild(app.view);
```

Correct:

```ts
document.body.appendChild(app.canvas);
```

`app.view` renamed to `app.canvas` in v8. Old getter still works but emits deprecation warning.


### [MEDIUM] Touching app.canvas or app.renderer before init resolves

Wrong:

```ts
const app = new Application();
document.body.appendChild(app.canvas);
app.init({ width: 800, height: 600 });
```

Correct:

```ts
const app = new Application();
await app.init({ width: 800, height: 600 });
document.body.appendChild(app.canvas);
```

`app.renderer`, `app.canvas`, and `app.screen` only usable once `init()` promise resolves. Before that, `app.renderer` is `undefined`. `app.canvas` / `app.screen` getters throw `TypeError` because they read from missing renderer.


## API Reference

- [Application](https://pixijs.download/release/docs/app.Application.html.md)
- [ApplicationOptions](https://pixijs.download/release/docs/app.ApplicationOptions.html.md)
- [ApplicationPlugin](https://pixijs.download/release/docs/app.ApplicationPlugin.html.md)
- [ResizePlugin](https://pixijs.download/release/docs/app.ResizePlugin.html.md)
- [ResizePluginOptions](https://pixijs.download/release/docs/app.ResizePluginOptions.html.md)
- [TickerPlugin](https://pixijs.download/release/docs/app.TickerPlugin.html.md)
- [TickerPluginOptions](https://pixijs.download/release/docs/app.TickerPluginOptions.html.md)
- [CullerPlugin](https://pixijs.download/release/docs/app.CullerPlugin.html.md)
- [autoDetectRenderer](https://pixijs.download/release/docs/rendering.autoDetectRenderer.html.md)
