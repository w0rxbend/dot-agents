# Compressed Textures

GPU-compressed formats (DDS, KTX, KTX2, Basis) use 4–8x less GPU memory than PNG/JPEG and skip runtime decoding. Use for large textures, asset-heavy games, tight memory budgets. Each format needs side-effect import to register its loader.

## Quick Start

```ts
import "pixi.js/ktx2";
import { Assets, Sprite } from "pixi.js";

const texture = await Assets.load("background.ktx2");

const bg = new Sprite(texture);
app.stage.addChild(bg);
```

## Core Patterns

### Format imports

```ts
import "pixi.js/dds"; // DirectDraw Surface (.dds)
import "pixi.js/ktx"; // KTX (Khronos Texture) v1
import "pixi.js/ktx2"; // KTX v2 (with Basis Universal support)
import "pixi.js/basis"; // Basis Universal (.basis)
```

Each import registers `LoaderParser` for matching extension. Several imports can coexist. Import only formats you use; decoder runtime adds bundle size.

### Format selection matrix

| Format | Platforms | Notes |
| ------ | --------- | ----- |
| DDS    | All       | Legacy desktop formats (DXT, BC). Fast decoder; wide support. |
| KTX    | All       | Older Khronos container. Prefer KTX2 for new projects. |
| KTX2   | All       | Newer container, usually with Basis Universal. GPU-native when available. |
| Basis  | All       | Supercompressed; transcodes to GPU-native format at load. Best for "one file, any platform" workflows. |

Use KTX2 + Basis for new projects unless you specifically need another format.

### With the resolver

```ts
import "pixi.js/ktx2";
import { Assets } from "pixi.js";

Assets.add({
  alias: "background",
  src: "background.{ktx2,webp,png}",
});

const texture = await Assets.load("background");
```

List compressed format first in resolver. Where browser or hardware can't sample it, resolver falls back to WebP or PNG automatically.

### Async decoding

```ts
import "pixi.js/basis";
import { Assets } from "pixi.js";

const texture = await Assets.load("hero.basis");
```

Basis Universal decodes async on worker thread (where supported). Normal `Assets.load` await suffices; loader handles decoding.

## Common Mistakes

### [CRITICAL] Missing the format import

Wrong:

```ts
import { Assets } from "pixi.js";
await Assets.load("background.ktx2");
```

Correct:

```ts
import "pixi.js/ktx2";
import { Assets } from "pixi.js";
await Assets.load("background.ktx2");
```

Without side-effect import, no parser is registered for `.ktx2`. Load silently does nothing (or errors) and returns `undefined`.


### [HIGH] Relying on mipmaps from compressed textures in Canvas2D

Compressed textures need WebGL or WebGPU; Canvas2D backend can't sample them. For Canvas support, add PNG/WebP fallback in resolver format list:

```ts
Assets.add({ alias: "bg", src: "bg.{ktx2,png}" });
```


### [MEDIUM] Large Basis files in WebGL1

Basis Universal transcodes to whatever GPU format device supports. On WebGL1 without extensions, some devices fall back to uncompressed format, losing memory savings. If targeting older hardware, check `renderer.context.supports` for supported compressed formats.


## API Reference

- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [loadKTX2](https://pixijs.download/release/docs/assets.loadKTX2.html.md)
- [TextureSource](https://pixijs.download/release/docs/rendering.TextureSource.html.md)
