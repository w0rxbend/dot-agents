# Renderers: WebGPU, WebGL, and Canvas

PixiJS v8 ships three renderers: `WebGPURenderer` (fastest where available), `WebGLRenderer` (broad compatibility, WebGL2), `CanvasRenderer` (last-resort 2D Canvas backend). `autoDetectRenderer` (used internally by `Application.init`) picks best available backend from preference list.

**Status:** `WebGLRenderer` recommended for production. `WebGPURenderer` feature-complete but still experimental; browser implementations inconsistent. `CanvasRenderer`: fallback for environments without WebGL/WebGPU, reduced feature set.

## Quick Start

```ts
const app = new Application();

await app.init({
  preference: ["webgpu", "webgl"],
  width: 800,
  height: 600,
  background: 0x222233,
  antialias: true,
});

document.body.appendChild(app.canvas);
```

`preference`: single string (try it first, then default order) or array (only these, in this order; others excluded). Default order when `preference` is not set: `webgl`, `webgpu`, `canvas`.

## Core Patterns

### Preference forms

```ts
// Single string: try webgpu first, fall back through defaults
await app.init({ preference: "webgpu" });

// Array: only try listed backends in order
await app.init({ preference: ["webgpu", "webgl"] });

// Array acts as a blocklist; anything not listed is excluded
await app.init({ preference: ["webgl"] }); // never uses webgpu or canvas

// Force canvas (legacy-only environments)
await app.init({ preference: ["canvas"] });
```

### Per-renderer options

```ts
await app.init({
  width: 800,
  height: 600,
  webgpu: { antialias: true, powerPreference: "high-performance" },
  webgl: { antialias: true, premultipliedAlpha: false },
  canvasOptions: { backgroundAlpha: 0 },
});
```

Common options at top level. Renderer-specific options go in `webgpu`, `webgl` or `canvasOptions`. Only selected renderer's options apply; rest discarded.

### Systems and pipes

Each renderer has fixed set of `System`s (lifecycle services: textures, buffers, state, events, filters, masks) plus `RenderPipe`s (per-renderable instruction builders: sprite, graphics, mesh, particle, text, tiling-sprite).

- `Systems` run once per renderer lifecycle, manage GPU state.
- `RenderPipes` run every frame, one per renderable type. Each batches instructions for its object class, flushes them to GPU.

Custom renderable: implement `RenderPipe` and `BatchableX` class, register both via extensions. These skills do not cover it further; see [RenderPipe API](https://pixijs.download/release/docs/rendering.RenderPipe.html.md).

### Lazy-loading backend-specific systems and pipes

Systems and pipes needed by only one backend can stay out of main bundle. Register renderer loader (`ExtensionType.WebGLLoader`, `ExtensionType.WebGPULoader` or `ExtensionType.CanvasLoader`) whose `load()` dynamic-imports the registering module. During `init`, renderer awaits every loader for its own backend: after environment extensions load, before creating systems and pipes. Loaders for other backends never run.

```ts
import { extensions, ExtensionType } from "pixi.js";

extensions.add({
  extension: { type: ExtensionType.WebGLLoader, name: "my-plugin" },
  load: () => import("./gl/register"), // registers WebGL systems and pipes on import
});
```

Loader names unique per backend; second loader with same name ignored. Loaders run concurrently. Registered systems and pipes are ordered by own `priority`, not by loader completion. `skipExtensionImports: true` skips loaders too, so custom builds import backend modules directly.

### Direct renderer construction

```ts
import { WebGLRenderer } from "pixi.js";

const renderer = new WebGLRenderer();
await renderer.init({ width: 800, height: 600 });
```

Most apps use `Application.init` or `autoDetectRenderer()`. Construct specific renderer directly when target environment known (tests, tooling, editor integrations).

### `renderer.render()` options

`.render()` accepts `Container` or options object:

```ts
// shorthand: just render the stage
renderer.render(app.stage);

// options form: control clearing, transform, or a render target
renderer.render({
  container: app.stage,
  clear: true,
  transform: new Matrix(),
});

// render into a mip level, array layer, cube face or 3D slice of a texture
renderer.render({
  container: myContainer,
  target: renderTexture,
  mipLevel: 1,
  layer: 0,
});

// store the capture in screen orientation (for 3D UVs)
renderer.render({ container: scene3d, target: renderTexture, flipY: true });
```

`container`: scene root to draw. `target`: separate destination (e.g. `RenderTexture`). `mipLevel > 0` suits custom LOD systems or manual mipmap generation. `flipY` defaults to `false`; set it to store texture render un-flipped, winding adjusted so back-face culling still works. `layer` selects array layer, cube face or depth slice of 3D `TextureSource` (`depth`); pass source itself as `target`.

### Render targets

```ts
import { CLEAR, RenderTarget, Texture, TextureSource } from "pixi.js";

const depthSource = new TextureSource({ width: 512, height: 512, format: "depth24plus-stencil8" });

const target = new RenderTarget({
  colorAttachments: [{ texture: new TextureSource({ width: 512, height: 512 }), loadOp: "clear" }],
  depthStencilAttachment: { texture: depthSource, depthLoadOp: "clear" },
});

renderer.render({ container, target });

// bind directly from custom render code; always use the options object
renderer.renderTarget.push({ target, clear: CLEAR.COLOR, mipLevel: 0 });
renderer.renderTarget.pop();

const saved = renderer.renderTarget.getBindState();
renderer.renderTarget.bind(saved); // replays without clearing

// copy the depth attachment into another depth-format texture (WebGL2 and WebGPU)
const depthCopy = new Texture({
  source: new TextureSource({ width: 512, height: 512, format: "depth24plus-stencil8" }),
});
renderer.renderTarget.copyDepthTexture(target, depthCopy, { x: 0, y: 0 }, { width: 512, height: 512 });
```

- `RenderTarget` takes WebGPU-style `colorAttachments`/`depthStencilAttachment` or older `colorTextures`/`depth`/`stencil`/`depthStencilTexture` options. `colorTextures: 0` with `depth: true` makes a depth-only target.
- Positional `bind(target, clear, ...)` and `push(...)` are deprecated since 8.20.0. `pop()` throws when stack is empty.
- `copyDepthTexture` needs WebGL2 or WebGPU and a depth-format destination. Next render into destination target must clear color only (`clear: CLEAR.COLOR`), or copied depth is lost.
- Destroy targets you constructed with `target.destroy()`; renderer releases GPU objects it built for them.

### Resizing, texture generation, and interop

```ts
renderer.resize(window.innerWidth, window.innerHeight);

const texture = renderer.generateTexture(displayObject);

// Mixing PixiJS with Three.js (or any other WebGL/WebGPU library)
threeRenderer.resetState();
threeRenderer.render(scene, camera);

pixiRenderer.resetState();
pixiRenderer.render({ container: stage });
```

Call `resetState()` before each library renders. Each leaves GPU state (bound textures, blend modes, active shaders) that conflicts with the other. Without `resetState()`, objects can disappear or blend wrong.

### Destroying a renderer

```ts
renderer.destroy();
```

Releases GPU resources, systems, pipes and event listeners. Destroyed renderer cannot render again.

### Renderer selection at runtime

```ts
console.log(app.renderer.name); // 'webgl', 'webgpu', or 'canvas'
```

After `init`, `app.renderer` is concrete class. Branch on backend with `app.renderer.name` (string). `app.renderer.type` is numeric id for internal dispatch; prefer `name` in user code.

### Supports check

```ts
if (await isWebGPUSupported()) {
  // ok to prefer webgpu
}

if (isWebGLSupported()) {
  // ok to prefer webgl
}

// after init, WebGPU-only capability flags
if (renderer.name === "webgpu") {
  renderer.device.extensions.transientAttachment; // GPUTextureUsage.TRANSIENT_ATTACHMENT available
  renderer.limits.supportsOverrideConstants; // pipeline constants vs. source-baked overrides
}
```

Both helpers exported from `pixi.js`. Use to tell user which backend will be used before calling `app.init`.

### Context and device loss

```ts
// both renderers recover on their own; only render bundles need re-recording
if (!renderer.encoder.isBundleValid(bundle)) {
  bundle = record();
}
```

WebGL renderer restores itself after `webglcontextrestored`. WebGPU renderer requests new device when browser reports `GPUDevice.lost`, rebuilds GPU resources on next render. PixiJS neither restores nor destroys device passed through WebGPU `gpu` option. Render bundle recorded on lost device fails `isBundleValid` and must be re-recorded.

## Common Mistakes

### [HIGH] Expecting WebGPU everywhere

Wrong:

```ts
await app.init({ preference: ["webgpu"] });
```

Correct:

```ts
await app.init({ preference: ["webgpu", "webgl"] });
```

WebGPU not yet available on all browsers. Array preference of only `['webgpu']` fails init on unsupported browsers (no fallback). Always include `'webgl'` fallback unless WebGPU support verified upstream.

### [MEDIUM] Assuming CanvasRenderer supports everything

CanvasRenderer does not support filters, masks beyond basic clipping, compressed textures or custom shaders. Last resort for environments that cannot run WebGL. For full feature parity, target WebGL or WebGPU.

## API Reference

- [autoDetectRenderer](https://pixijs.download/release/docs/rendering.autoDetectRenderer.html.md)
- [AbstractRenderer](https://pixijs.download/release/docs/rendering.AbstractRenderer.html.md)
- [WebGLRenderer](https://pixijs.download/release/docs/rendering.WebGLRenderer.html.md)
- [WebGPURenderer](https://pixijs.download/release/docs/rendering.WebGPURenderer.html.md)
- [CanvasRenderer](https://pixijs.download/release/docs/rendering.CanvasRenderer.html.md)
- [RenderTarget](https://pixijs.download/release/docs/rendering.RenderTarget.html.md)
- [RenderTargetSystem](https://pixijs.download/release/docs/rendering.RenderTargetSystem.html.md)
