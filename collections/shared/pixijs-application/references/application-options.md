# ApplicationOptions reference

Every option `app.init(options)` accepts. Options come from three type sources merged into one interface:

- `AutoDetectOptions` → base renderer options (width/height/resolution/etc.)
- `PixiMixins.ApplicationOptions` → plugin options (`resizeTo`, `autoStart`, `sharedTicker`, `culler`)
- System defaults → each renderer system (background, view, hello, GC, context, backbuffer, events, graphics) contributes own options

Options with no default stay unset unless passed. `Partial<ApplicationOptions>` means everything is optional.


## View / canvas

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `width` | `number` | `800` | Initial width in CSS pixels. |
| `height` | `number` | `600` | Initial height in CSS pixels. |
| `canvas` | `ICanvas` | — | Existing `HTMLCanvasElement` (or `OffscreenCanvas`) to render into instead of creating one. |
| `view` | `ICanvas` | — | **Deprecated since 8.0.0.** Alias for `canvas`. |
| `resolution` | `number` | `1` | Device pixel ratio. Set to `window.devicePixelRatio` for HiDPI. |
| `autoDensity` | `boolean` | `false` | Scale canvas CSS dimensions so `width`/`height` stay in CSS pixels while backing store matches `resolution`. Only honored on `HTMLCanvasElement` (ignored on `OffscreenCanvas`). |
| `antialias` | `boolean` | `false` | GPU MSAA where supported. On WebGL, only affects main context. Use `useBackBuffer: true` for antialiased filtering. |
| `depth` | `boolean` | — | Allocate depth buffer for main view. Always on for WebGL. Needed for z-ordered rendering. |
| `transient` | `boolean` | `false` | WebGPU only, with `antialias`. Discard canvas's multisample depth/stencil buffer at end of each pass, plus its colour buffer on GPUs that aren't tile-based (tile-based GPUs already discard colour). Only for apps that never reopen canvas pass while still needing depth or stencil: no filters or masks popping back onto it, no render with `clear: false`. |

```ts
await app.init({
  width: 1280,
  height: 720,
  resolution: window.devicePixelRatio,
  autoDensity: true,
  antialias: true,
});
```

## Background

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `backgroundColor` | `ColorSource` | `0x000000` | Canvas clear color. Accepts hex, CSS string, `[r, g, b, a]`, or any `ColorSource`. |
| `background` | `ColorSource` | — | Alias for `backgroundColor`. If both set, `background` wins. |
| `backgroundAlpha` | `number` | `1` | Clear alpha, `0`–`1`. **Cannot be changed after init**: backing canvas is allocated with or without alpha support based on this value. Set `< 1` now if transparency may ever be needed. |
| `clearBeforeRender` | `boolean` | `true` | Clear target before each frame. Disable only if you draw full-frame background yourself (e.g. full-screen sprite). |

```ts
await app.init({
  backgroundColor: 0x1099bb,
  backgroundAlpha: 1,
});
```

## Renderer preference

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `preference` | `'webgl' \| 'webgpu' \| 'canvas' \| RendererPreference[]` | `'webgl'` | Preferred renderer. String: try first, then fall back through default priority (`webgl` → `webgpu` → `canvas`). Array: try only listed renderers, in order. See ["Array form"](#preference-array-form) below. |
| `webgl` | `Partial<WebGLOptions>` | — | Applied **only** when WebGL renderer is selected. Merged over top-level options. |
| `webgpu` | `Partial<WebGPUOptions>` | — | Applied **only** when WebGPU renderer is selected. |
| `canvasOptions` | `Partial<CanvasOptions>` | — | Applied **only** when Canvas2D renderer is selected. |

### preference: array form

Array `preference` restricts `autoDetectRenderer` to exactly listed renderers, in given order. Any renderer not in array is **excluded entirely**; array doubles as blocklist.

```ts
// Try WebGPU first, then fall back to WebGL. Never use Canvas2D.
await app.init({ preference: ["webgpu", "webgl"] });

// Only ever use Canvas2D (e.g. in a WebGL-disabled environment).
await app.init({ preference: ["canvas"] });

// Skip WebGPU entirely while keeping the default webgl → canvas fallback order.
await app.init({ preference: ["webgl", "canvas"] });
```

String form instead falls through **full** default priority if first choice fails:

```ts
// Tries webgpu, then webgl, then canvas — all three are candidates.
await app.init({ preference: "webgpu" });
```

Use array to guarantee a renderer is never picked (e.g. WebGPU broken on target device, or to forbid Canvas2D's feature subset).


## Shared rendering

Apply to every renderer type.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `roundPixels` | `boolean` | `false` | Round vertex positions to whole pixels at shader time. Eliminates subpixel shimmer for pixel-art but blurs smooth motion. |
| `skipExtensionImports` | `boolean` | `false` | Disable automatic import of default extensions. With `true`, import needed subsystems manually (`import 'pixi.js/accessibility'`, `'pixi.js/app'`, `'pixi.js/events'`, …). Renderer loader extensions (`WebGLLoader`/`WebGPULoader`/`CanvasLoader`) are skipped too, so import backend-specific plugin modules yourself. For custom tree-shaken builds. |
| `hello` | `boolean` | `false` | Log PixiJS version and renderer type banner to console on init. |
| `failIfMajorPerformanceCaveat` | `boolean` | `false` | Fail WebGL context creation if browser reports major performance issues (blocklisted GPU, software fallback). Set `true` for high-performance apps that should refuse slow paths. |

```ts
await app.init({
  roundPixels: true,
  hello: true,
});
```

## Graphics

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `bezierSmoothness` | `number` | `0.5` | Curve tessellation for Graphics bezier paths. Higher is smoother (more triangles). |

```ts
await app.init({
  bezierSmoothness: 0.75,
});
```

## Ticker (TickerPluginOptions)

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `autoStart` | `boolean` | `true` | Start render loop automatically after `init()` resolves. `false` stops `app.render()` running each frame, but **does not** stop `Ticker.shared` if `sharedTicker: true` is set. |
| `sharedTicker` | `boolean` | `false` | Use `Ticker.shared` instead of per-Application ticker. Useful for syncing multiple apps. Loses per-app control over start/stop. |

See `pixijs-ticker` for ticker API itself.

```ts
await app.init({
  autoStart: false,
  sharedTicker: false,
});

function loop() {
  app.renderer.render(app.stage);
  requestAnimationFrame(loop);
}
loop();
```

## Resize (ResizePluginOptions)

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `resizeTo` | `Window \| HTMLElement` | `null` | Element renderer auto-resizes to match. `window` resizes to viewport. Element uses `clientWidth`/`clientHeight`. Leave `null` to opt out of auto-resize. |

Plugin listens for `resize` events on `window` and calls `renderer.resize()`. Reassign `app.resizeTo` at runtime if needed. Call `app.resize()`, `app.queueResize()` or `app.cancelResize()` from user code.

```ts
await app.init({
  resizeTo: window,
});
```

## Culler (CullerPluginOptions)

Opt-in plugin (must `extensions.add(CullerPlugin)` to activate).

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `culler.updateTransform` | `boolean` | `false` (effectively) | Must be set explicitly to `true` to run transform updates before culling. Otherwise PixiJS skips transform updates, and cull bounds may lag one frame for moving objects. |

```ts
import { CullerPlugin, extensions } from "pixi.js";

extensions.add(CullerPlugin);

await app.init({
  culler: { updateTransform: true },
});
```

## Events

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `eventMode` | `'none' \| 'passive' \| 'auto' \| 'static' \| 'dynamic'` | `'passive'` | Default interaction mode for every container. See `pixijs-events`. |
| `eventFeatures.move` | `boolean` | `true` | Fire `pointermove`/`mousemove`/`touchmove` + `pointerover`/`pointerout`. |
| `eventFeatures.globalMove` | `boolean` | `true` | Fire `globalpointermove`/`globalmousemove`/`globaltouchmove` regardless of hit target. Expensive; turn off if not needed. |
| `eventFeatures.click` | `boolean` | `true` | Fire `pointerdown`/`pointerup`/`click`/`tap`. |
| `eventFeatures.wheel` | `boolean` | `true` | Fire `wheel`. |

```ts
await app.init({
  eventMode: "static",
  eventFeatures: {
    move: true,
    globalMove: false,
    click: true,
    wheel: true,
  },
});
```

## Accessibility

Pass on top-level init options.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `accessibilityOptions.enabledByDefault` | `boolean` | `false` | Enable accessibility overlays immediately instead of waiting for Tab key. |
| `accessibilityOptions.debug` | `boolean` | `false` | Show accessibility overlay divs visibly for debugging. |
| `accessibilityOptions.activateOnTab` | `boolean` | `true` | Activate overlays when user presses Tab. |
| `accessibilityOptions.deactivateOnMouseMove` | `boolean` | `true` | Deactivate overlays when mouse moves. |

Accessibility not covered by these skills. Import `'pixi.js/accessibility'`. Full API: [PixiJS accessibility guide](https://pixijs.com/8.x/guides/components/accessibility).

```ts
await app.init({
  accessibilityOptions: {
    enabledByDefault: true,
    activateOnTab: true,
    deactivateOnMouseMove: true,
  },
});
```

## WebGL-only options

Applied when WebGL renderer is selected.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `context` | `WebGL2RenderingContext \| null` | `null` | Use existing WebGL context instead of creating one. Useful for hand-managing context or integrating with other renderers. |
| `powerPreference` | `'high-performance' \| 'low-power'` | `undefined` | Hint browser which GPU to pick on multi-GPU systems. If omitted, PixiJS internally passes `'default'` to GPU context. `'default'` is not settable from user code. |
| `premultipliedAlpha` | `boolean` | `true` | Tell compositor drawing buffer holds premultiplied-alpha colors. Changing it affects blending math. |
| `preserveDrawingBuffer` | `boolean` | `false` | Keep drawing buffer between frames. Required for `canvas.toDataURL()` or `canvas.toBlob()` to capture arbitrary frames. |
| `preferWebGLVersion` | `1 \| 2` | `2` | Preferred WebGL version. PixiJS v8 designed for WebGL2; WebGL1 is legacy fallback. |
| `multiView` | `boolean` | `false` | Enable rendering to multiple canvases from one renderer. |
| `useBackBuffer` | `boolean` | `false` | Render to intermediate texture instead of directly to canvas. Required for advanced blend modes and filters that sample backdrop. Enables `antialias` on back buffer independently from main context. |

```ts
await app.init({
  preference: "webgl",
  webgl: {
    preferWebGLVersion: 2,
    useBackBuffer: true,
    powerPreference: "high-performance",
  },
});
```

## WebGPU-only options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `powerPreference` | `'high-performance' \| 'low-power'` | `undefined` | Hint for `requestAdapter()`. |
| `forceFallbackAdapter` | `boolean` | `false` | Force software/fallback adapter. For testing only. |
| `gpu` | `{ adapter, device }` | — | Use pre-created `GPUAdapter` + `GPUDevice` pair. Useful for sharing device between engines. |

```ts
await app.init({
  preference: ["webgpu", "webgl"],
  webgpu: {
    powerPreference: "high-performance",
  },
});
```

## Garbage collection

All time values in milliseconds.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `gcActive` | `boolean` | `true` | Enable unified renderer garbage collector. |
| `gcMaxUnusedTime` | `number` | `60000` | How long resource can stay unused before GC collects it. |
| `gcFrequency` | `number` | `30000` | How often GC sweep runs. |

### Deprecated (GC — prefer the unified options above)

`TextureGCSystem` and `RenderableGCSystem` still accept these. Passing them works during deprecation window but logs warnings.

| Option | Deprecated since | Replacement |
| --- | --- | --- |
| `textureGCActive` | 8.15.0 | `gcActive` |
| `textureGCMaxIdle` | 8.15.0 | `gcMaxUnusedTime` (note: old option is frames; new API is ms) |
| `textureGCCheckCountMax` | 8.15.0 | `gcFrequency` (frames → ms) |
| `textureGCAMaxIdle` | 8.3.0 | `textureGCMaxIdle` (typo fix) → now `gcMaxUnusedTime` |
| `renderableGCActive` | 8.15.0 | `gcActive` |
| `renderableGCMaxUnusedTime` | 8.15.0 | `gcMaxUnusedTime` |
| `renderableGCFrequency` | 8.15.0 | `gcFrequency` |

```ts
await app.init({
  gcActive: true,
  gcMaxUnusedTime: 60_000,
  gcFrequency: 30_000,
});
```

## Per-renderer overrides

`webgl`, `webgpu`, and `canvasOptions` merge over top-level options once selected renderer is known:

```ts
await app.init({
  antialias: false,
  webgl: { antialias: true, useBackBuffer: true },
  webgpu: { antialias: true },
  canvasOptions: {
    /* canvas-specific */
  },
});
```

If WebGL wins, renderer sees `antialias: true` + `useBackBuffer: true`. If WebGPU wins, only `antialias: true`. Three sub-keys are stripped before options reach renderer.
