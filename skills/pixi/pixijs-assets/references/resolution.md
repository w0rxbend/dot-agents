# Resolution and Format Detection

Resolver picks best asset variant for current device by pixel density (`@0.5x`, `@1x`, `@2x`) and supported formats (`avif`, `webp`, `png`).

## Quick Start

```ts
await Assets.init({
  texturePreference: {
    resolution: window.devicePixelRatio,
    format: ["avif", "webp", "png"],
  },
});

Assets.add({ alias: "hero", src: "hero@{0.5,1,2}x.{webp,png}" });

const texture = await Assets.load("hero");
```

Resolver expands pattern to six candidates (`hero@0.5x.webp`, `hero@0.5x.png`, `hero@1x.webp`, ...), picks best match by device pixel ratio and format support.

## Core Patterns

### Configuring preferences at init

```ts
await Assets.init({
  texturePreference: {
    resolution: window.devicePixelRatio, // e.g., 2 on retina
    format: ["avif", "webp", "png"], // preferred-first order
  },
});
```

- `resolution`: single number (best-match threshold) or array of acceptable resolutions.
- `format`: preference order. Resolver tries each, uses first one browser supports.

### Resolution patterns in src

```ts
Assets.add({ alias: "bg", src: "bg@{0.5,1,2}x.png" });
```

Expands to `bg@0.5x.png`, `bg@1x.png`, `bg@2x.png`; picks by `texturePreference.resolution`. Encoded resolution sets texture source resolution automatically, so sprite `width` / `height` show logical size whichever file loads.

### Format patterns in src

```ts
Assets.add({ alias: "icon", src: "icon.{avif,webp,png}" });
```

Format detection runs once during `Assets.init()`. Resolver learns browser format support, then picks highest-preference supported format per load.

### Manual resolution override

```ts
Assets.add({
  alias: "sharp",
  src: "sharp.png",
  data: { resolution: 2 },
});
```

If file is at known resolution but lacks `@2x` filename suffix, pass `resolution` in `data` to tell loader. Useful when tooling doesn't produce suffixed filenames.

### Custom retina prefix

```ts
import { Resolver } from "pixi.js";

Resolver.RETINA_PREFIX = /@([0-9\.]+)density/;

Assets.add({ alias: "hero", src: "hero@{1,2}density.png" });
```

Change filename pattern if build pipeline uses different convention. Default is `/@([0-9\.]+)x/`.

### Skipping format detection

```ts
await Assets.init({
  skipDetections: true,
  texturePreference: { format: ["webp"] },
});
```

If you know target browser supports a specific format, `skipDetections: true` skips runtime detection (small init-time saving). Useful for embedded or kiosk deployments with fixed format support.

## Common Mistakes

### [HIGH] Wrong pattern syntax

Wrong:

```ts
Assets.add({ alias: "hero", src: "hero@[1,2]x.png" });
```

Correct:

```ts
Assets.add({ alias: "hero", src: "hero@{1,2}x.png" });
```

Expansion uses `{}` (like shell brace expansion), not `[]`. Square brackets aren't recognized; resolver tries to load literal filename.


### [MEDIUM] Missing fallback format

Wrong:

```ts
Assets.add({ alias: "hero", src: "hero.avif" });
```

Correct:

```ts
Assets.add({ alias: "hero", src: "hero.{avif,png}" });
```

Browser without AVIF support makes loader fail. Always list at least one fallback format all target browsers support.


### [MEDIUM] Mismatch between spritesheet.json `meta.scale` and actual image

In v8, spritesheet `meta.scale` directly sets atlas texture resolution. If JSON says `"1"` but image was exported at 2x, frames render at double intended size. Verify `meta.scale` matches actual image resolution; atlas tools like TexturePacker set it automatically.


## API Reference

- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [Resolver](https://pixijs.download/release/docs/assets.Resolver.html.md)
- [AssetInitOptions](https://pixijs.download/release/docs/assets.AssetInitOptions.html.md)
