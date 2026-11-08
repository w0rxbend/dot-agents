# Animated GIFs

`Assets.load()` loads animated GIFs and returns `GifSource` with all decoded frames. Pass it to `GifSprite` for playback, looping, frame control. Opt-in via `'pixi.js/gif'` side-effect import.

## Quick Start

```ts
import "pixi.js/gif";
import { Assets, GifSprite } from "pixi.js";

const source = await Assets.load("explosion.gif");
const gif = new GifSprite(source);
app.stage.addChild(gif);
```

## Core Patterns

### Load options via `data`

```ts
const source = await Assets.load({
  src: "pixel-art.gif",
  data: {
    fps: 12,
    scaleMode: "nearest",
    resolution: 2,
    autoGenerateMipmaps: false,
  },
});
```

`data` takes `GifBufferOptions` (extends `CanvasSourceOptions`):

| Option                | Default    | Purpose |
| --------------------- | ---------- | ------- |
| `fps`                 | `30`       | Fallback frame rate when GIF has no per-frame delay metadata |
| `scaleMode`           | `'linear'` | `'nearest'` for pixel art, `'linear'` for smooth scaling |
| `resolution`          | `1`        | Render resolution of decoded frames |
| `autoGenerateMipmaps` | `false`    | Generate mipmaps for downscaling |

Other `CanvasSourceOptions` fields work too.

### GifSprite options

```ts
const gif = new GifSprite({
  source,
  autoPlay: true,
  loop: true,
  animationSpeed: 0.5,
  autoUpdate: true,
  fps: 30,
  onComplete: () => console.log("done"),
  onLoop: () => console.log("looped"),
  onFrameChange: (frame) => console.log(frame),
});
```

Constructor options control playback, independent of load-time `data`.

### Loading from a data URI

```ts
const source = await Assets.load(
  "data:image/gif;base64,R0lGODlhAQABAAAAACw...",
);
```

Parser matches `.gif` extensions and `data:image/gif` URIs. No extra configuration.

### Playback control

```ts
gif.play();
gif.stop();
gif.currentFrame = 5;
gif.animationSpeed = 0.5;
gif.loop = false;

console.log(gif.totalFrames);
console.log(gif.playing);
console.log(gif.progress);
console.log(gif.duration);
```

### Sharing a source across sprites

```ts
const source = await Assets.load("spin.gif");

const a = new GifSprite(source);
const b = new GifSprite(source);

a.animationSpeed = 1;
b.animationSpeed = 0.25;
```

Several `GifSprite` instances can share one `GifSource`, each with own playback state. Textures are shared, so cheap.

### Cleanup

```ts
gif.destroy(); // destroys the sprite, not the source
gif.destroy(true); // destroys the sprite AND the source (breaks other sprites using it)
await Assets.unload("explosion.gif"); // unload through the Assets system
```

Prefer `Assets.unload` unless you know no other sprite shares the same `GifSource`.

## Forcing the GIF parser

If GIF URL lacks extension, force parser:

```ts
const source = await Assets.load({
  src: "https://cdn.example.com/gif/abc123",
  parser: "gif",
  data: { fps: 24 },
});
```

See main `SKILL.md` section "Forcing a parser with `parser`" for all parser IDs.

## Common Mistakes

### [CRITICAL] Missing the GIF import

Wrong:

```ts
import { Assets } from "pixi.js";
await Assets.load("explosion.gif");
```

Correct:

```ts
import "pixi.js/gif";
import { Assets } from "pixi.js";
await Assets.load("explosion.gif");
```

Without `'pixi.js/gif'`, parser isn't registered. Call fails or returns undefined.


### [MEDIUM] Using GIF when a spritesheet would be cheaper

GIF decoding makes one texture per frame: 30 frames, 30 separate uploads. Spritesheet packs all frames into one atlas texture; batches better, uses less GPU memory. Prefer spritesheets for performance-critical game animations; GIFs for convenience and one-off effects.


### [MEDIUM] destroy(true) when other sprites share the source

```ts
const source = await Assets.load("spin.gif");
const a = new GifSprite(source);
const b = new GifSprite(source);

a.destroy(true); // WRONG: also destroys source, breaking sprite b
```

Pass `true` to `destroy` only if nothing else references the `GifSource`. Otherwise call plain `destroy()`, then `Assets.unload()` once source is no longer needed.


## API Reference

- [GifSource](https://pixijs.download/release/docs/gif.GifSource.html.md)
- [GifSprite](https://pixijs.download/release/docs/gif.GifSprite.html.md)
- [GifBufferOptions](https://pixijs.download/release/docs/gif.GifBufferOptions.html.md)
- [GifAsset](https://pixijs.download/release/docs/gif.GifAsset.html.md)
