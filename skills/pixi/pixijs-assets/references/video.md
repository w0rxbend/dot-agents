# Video Textures

`Assets.load()` loads videos and returns regular `Texture`. On a `Sprite`, it paints current video frame each render. Use for backgrounds, cutscenes, any animated surface driven by video source.

Supported extensions: `.mp4`, `.m4v`, `.webm`, `.ogg`, `.ogv`, `.h264`, `.avi`, `.mov`. Browser support varies; always provide fallback format.

## Quick Start

```ts
const videoTex = await Assets.load("intro.mp4");
const sprite = new Sprite(videoTex);
app.stage.addChild(sprite);
```

Texture wraps `VideoSource`. Video plays automatically unless `data` sets `autoPlay: false`.

## Core Patterns

### Load options via `data`

```ts
const texture = await Assets.load({
  src: "city.mp4",
  data: {
    autoPlay: false,
    loop: true,
    muted: true,
    preload: true,
    playsinline: true,
    updateFPS: 30,
    alphaMode: "premultiply-alpha-on-upload",
  },
});
```

`data` accepts `VideoSourceOptions` fields. Defaults come from `VideoSource.defaultOptions`.

| Option        | Default                | Purpose |
| ------------- | ---------------------- | ------- |
| `autoLoad`    | `true`                 | Start downloading as soon as assigned |
| `autoPlay`    | `true`                 | Start playing once `canplay` fires |
| `loop`        | `false`                | Restart at end |
| `muted`       | `true`                 | Required for autoplay on most browsers |
| `playsinline` | `true`                 | Prevents iOS fullscreen takeover |
| `preload`     | `false`                | Await `canplaythrough` before resolving |
| `updateFPS`   | `0`                    | Texture update rate. `0` updates every render frame |
| `crossorigin` | `true`                 | CORS mode for cross-origin URLs |
| `alphaMode`   | auto-detected          | `'no-premultiply-alpha'` for straight alpha |
| `mime`        | derived from extension | Force MIME type when URL lacks extension |

### Format fallback

```ts
Assets.add({
  alias: "clip",
  src: "clip.{webm,mp4}",
});

const texture = await Assets.load("clip");
```

Resolver picks first listed format browser supports. WebM and MP4 together cover all current browsers.

### Mobile autoplay

iOS and mobile Chrome only autoplay muted, inline video. Set both `muted: true` and `playsinline: true`, or playback stalls on first frame until user taps.

### Manual playback control

```ts
const texture = await Assets.load({
  src: "boss-fight.mp4",
  data: { autoPlay: false, preload: true },
});

const videoSource = texture.source as VideoSource;

startButton.on("pointertap", () => {
  videoSource.resource.play();
});
```

With `autoPlay: false`, take `VideoSource` from `texture.source` and call `.play()`, `.pause()`, or `.currentTime =` on its `resource` (the `HTMLVideoElement`). Pair with `preload: true` to guarantee first frame uploads before `play()`.

### Updating at a fixed rate

```ts
await Assets.load({
  src: "background.mp4",
  data: { updateFPS: 15 },
});
```

`updateFPS` caps how often GPU texture re-uploads from video element. `0` re-uploads every render tick (smoothest; highest cost). `15` caps at 15 uploads per second, saving bandwidth on static-ish video backgrounds.

## Forcing the video parser

If video URL lacks extension (e.g., CDN signed URL or blob), loader can't pick parser by test. Force it with top-level `parser` field:

```ts
const texture = await Assets.load({
  src: "https://cdn.example.com/stream/abc123",
  parser: "video",
  data: { mime: "video/mp4" },
});
```

See main `SKILL.md` section "Forcing a parser with `parser`" for all parser IDs.

## Common Mistakes

### [HIGH] Autoplay without mute on mobile

Wrong:

```ts
await Assets.load({ src: "ad.mp4", data: { autoPlay: true } });
```

Correct:

```ts
await Assets.load({
  src: "ad.mp4",
  data: { autoPlay: true, muted: true, playsinline: true },
});
```

Mobile browsers block autoplay with sound. Promise resolves, but video stays frozen on frame 0 until user interacts.


### [MEDIUM] Expecting sprite.texture to update itself

`Sprite` shows current video frame automatically; `VideoSource` re-uploads every render. No need to call `update()` yourself. If playback looks frozen, check video element is playing (`videoSource.resource.paused` should be `false`).


### [MEDIUM] Missing CORS for cross-origin video

Cross-origin video without `Access-Control-Allow-Origin` headers taints canvas; most WebGL operations (`readPixels`, snapshots) then fail silently. Serve with CORS headers, or pass `data: { crossorigin: false }` and accept texture can't be extracted.


## API Reference

- [VideoSource](https://pixijs.download/release/docs/rendering.VideoSource.html.md)
- [VideoSourceOptions](https://pixijs.download/release/docs/rendering.VideoSourceOptions.html.md)
- [loadVideoTextures](https://pixijs.download/release/docs/assets.loadVideoTextures.html.md)
- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
