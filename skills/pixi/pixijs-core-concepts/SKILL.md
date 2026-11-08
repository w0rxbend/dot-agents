---
name: pixijs-core-concepts
description: "Use this skill when understanding how PixiJS v8 renders frames: the systems-and-pipes renderer, the render loop, and how the library adapts to different environments. Covers WebGLRenderer/WebGPURenderer/CanvasRenderer selection, renderer.render() pipeline, environment detection, rendering into RenderTextures and RenderTargets (flipY, mipLevel, layer, bind/push/pop, copyDepthTexture), WebGL context loss and WebGPU device loss recovery, and pointers to per-topic deep dives. Triggers on (in PixiJS code): PixiJS renderer, WebGLRenderer, WebGPURenderer, CanvasRenderer, PixiJS render loop, render pipeline, renderer systems, PixiJS environments, autoDetectRenderer, RenderTexture, RenderTarget, render to texture, flipY, mipLevel, layer, 3D texture, depth slice, renderTarget.bind, copyToTexture, copyDepthTexture, depth-only, WebGLLoader, WebGPULoader, CanvasLoader, RendererLoader, lazy-load renderer systems, code splitting, context lost, webglcontextlost, device lost, GPUDevice.lost."
license: MIT
---

How PixiJS v8 draws pixels: renderer picks GPU backend, render loop drives per-frame work, environment layer adapts to browser, Web Worker or SSR. Scene graph (Containers, transforms, destroy): see `pixijs-scene-container` and its `references/scene-core-concepts.md`.

## Quick Start

```ts
console.log(app.renderer.name); // 'webgl' | 'webgpu' | 'canvas'

app.ticker.add((ticker) => {
  sprite.rotation += 0.01 * ticker.deltaTime;
});

const tex = app.renderer.extract.texture({ target: app.stage });

app.renderer.render({ container: app.stage });
```

`app.renderer` is `WebGLRenderer`, `WebGPURenderer` or `CanvasRenderer`, picked by `autoDetectRenderer`. TickerPlugin calls `renderer.render()` automatically; call it manually only with `autoStart: false`. Backend selection happens in `Application.init({ preference })`.

**Related skills:** `pixijs-application` (Application setup and lifecycle), `pixijs-ticker` (per-frame logic, priorities, FPS capping), `pixijs-scene-container` (scene graph basics).

## Topics

| Topic               | Reference                                              | When                                                      |
| ------------------- | ------------------------------------------------------ | --------------------------------------------------------- |
| Choosing a backend  | [references/renderers.md](references/renderers.md)     | Preference forms, per-renderer options, systems and pipes |
| Per-frame execution | [references/render-loop.md](references/render-loop.md) | Priority order, time units, manual rendering              |

Non-browser targets (`DOMAdapter`, `WebWorkerAdapter`, custom adapters, strict CSP): see Decision guide below. No separate environments skill in this collection.

## Decision guide

- **Setting up an Application?** Start with `pixijs-application`. This skill covers renderer internals.
- **Choosing between WebGL and WebGPU?** Use preference `['webgpu', 'webgl']`: WebGPU fastest where available, WebGL reliable fallback. See `references/renderers.md`.
- **Running in a Web Worker?** Call `DOMAdapter.set(WebWorkerAdapter)` before `app.init`. Pass `OffscreenCanvas` (from main thread via `transferControlToOffscreen()`) as `canvas` option. Real-DOM features (pointer events from canvas, `DOMContainer`, accessibility overlays) not available in a worker; forward input from main thread yourself. See [WebWorkerAdapter API](https://pixijs.download/release/docs/environment.WebWorkerAdapter.html.md).
- **Need manual control over when rendering happens?** Set `autoStart: false`, call `app.renderer.render({ container: app.stage })` from own loop. See `references/render-loop.md`.
- **Integrating with a physics library?** Add update at `UPDATE_PRIORITY.HIGH` so physics runs before render at `LOW`. See `references/render-loop.md`.
- **Writing a custom renderable?** Implement `RenderPipe`, register via extensions (outline in `references/renderers.md`; full detail not covered by these skills, see [RenderPipe API](https://pixijs.download/release/docs/rendering.RenderPipe.html.md)).
- **Rendering into a texture or a custom render target?** Pass `target` to `renderer.render()`, or build `RenderTarget` with explicit color and depth attachments. See `references/renderers.md`.
- **Running under strict CSP?** Import `'pixi.js/unsafe-eval'` before creating renderer; replaces shader and uniform code generation needing `new Function`.

## Quick concepts

### Renderer = systems + pipes

Renderer built from `Systems` (lifecycle services: textures, buffers, state, filters, masks) and `RenderPipes` (per-renderable instruction builders: sprite, graphics, mesh, particle, text, tiling). Renderer loader extensions (`WebGLLoader`, `WebGPULoader`, `CanvasLoader`) can dynamic-import backend-specific systems and pipes. See `references/renderers.md`.

### The render loop

`TickerPlugin` registers `app.render()` at `UPDATE_PRIORITY.LOW`, so callbacks at `NORMAL` or `HIGH` run before draw.

### Environments

`DOMAdapter` abstracts every DOM call PixiJS makes (canvas creation, image loading, fetch, XML parsing). Swap with `DOMAdapter.set(WebWorkerAdapter)` for Workers, or implement custom `Adapter` for Node/SSR. Must be done before `Application.init`.

## Common Mistakes

### [HIGH] Accessing app.renderer before init() resolves

Wrong:

```ts
const app = new Application();
app.init({ width: 800, height: 600 });
console.log(app.renderer.name); // TypeError: app.renderer is undefined until init() resolves
```

Correct:

```ts
const app = new Application();
await app.init({ width: 800, height: 600 });
console.log(app.renderer.name); // 'webgl' | 'webgpu' | 'canvas'
```

`Application.init()` is async. `app.renderer`, `app.canvas` and `app.screen` do not exist until promise resolves.

### [HIGH] Setting DOMAdapter after Application.init

Wrong:

```ts
const app = new Application();
await app.init({ width: 800, height: 600 });
DOMAdapter.set(WebWorkerAdapter); // too late — init already allocated resources
```

Correct:

```ts
DOMAdapter.set(WebWorkerAdapter);
const app = new Application();
await app.init({ width: 800, height: 600 });
```

Adapter abstracts DOM calls renderer makes during construction (canvas creation, image loading, fetch). Swap it before `init()`, or wrong adapter gets baked into renderer.

### [MEDIUM] Treating `preference` as a guarantee

Wrong:

```ts
await app.init({ preference: "webgpu" });
// assume WebGPU is active
useWebGPUOnlyFeature(app.renderer);
```

Correct:

```ts
await app.init({ preference: "webgpu" });
if (app.renderer.name === "webgpu") {
  useWebGPUOnlyFeature(app.renderer);
}
```

`preference` is a hint, not a demand. If browser lacks WebGPU, PixiJS falls back to WebGL (or Canvas). Always branch on `renderer.name` for backend-specific code.

## API Reference

- [autoDetectRenderer](https://pixijs.download/release/docs/rendering.autoDetectRenderer.html.md)
- [AbstractRenderer](https://pixijs.download/release/docs/rendering.AbstractRenderer.html.md)
- [WebGLRenderer](https://pixijs.download/release/docs/rendering.WebGLRenderer.html.md)
- [WebGPURenderer](https://pixijs.download/release/docs/rendering.WebGPURenderer.html.md)
- [CanvasRenderer](https://pixijs.download/release/docs/rendering.CanvasRenderer.html.md)
- [Application](https://pixijs.download/release/docs/app.Application.html.md)
- [DOMAdapter](https://pixijs.download/release/docs/environment.DOMAdapter.html.md)
