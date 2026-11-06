# SVG Loading

PixiJS loads `.svg` two ways: rasterized to texture (fast, fixed resolution) or parsed into `GraphicsContext` (scalable vector, reusable across `Graphics` instances).

## Quick Start

```ts
const svgTexture = await Assets.load("icon.svg");
const sprite = new Sprite(svgTexture);

const svgContext = await Assets.load({
  src: "icon.svg",
  data: { parseAsGraphicsContext: true },
});
const graphic = new Graphics(svgContext);
```

Default: rasterize to texture at native size. Pass `parseAsGraphicsContext: true` in `data` to parse as vector geometry instead.

## Core Patterns

### Texture mode (default)

Browser's native SVG-to-image pipeline rasterizes it to bitmap, then it uploads as `Texture`. Batches like regular sprite. Rasterization happens once; scaling beyond that resolution pixelates.

### Graphics mode

```ts
const context = await Assets.load({
  src: "logo.svg",
  data: { parseAsGraphicsContext: true },
});

const small = new Graphics(context);
small.scale.set(0.5);

const large = new Graphics(context);
large.scale.set(3);
```

Parses into `GraphicsContext` (compiled list of fill/stroke instructions). Both `Graphics` instances share one context: cheap, and both stay crisp at any scale.

### Resolution for sharper texture mode

```ts
const icon = await Assets.load({
  src: "icon.svg",
  data: { resolution: 2 },
});
```

In texture mode, `resolution` in `data` rasterizes at higher density. Pair with `autoGenerateMipmaps` for smooth downscaling. Doesn't apply in Graphics mode.

### Global default

```ts
import { loadSvg } from "pixi.js";

loadSvg.config.parseAsGraphicsContext = true;
```

Flips default mode globally. Later `Assets.load('*.svg')` calls parse as Graphics unless asset's `data` options override.

### What Graphics mode parses

Graphics mode reads `<path>` (including `fill-rule="evenodd"` holes), `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<polygon>`, `<polyline>`, and `<g>`. Styling comes from `fill`, `stroke`, `stroke-width`, `fill-opacity`, `stroke-opacity`, and `opacity` attributes or inline `style="..."`. Fills and strokes can reference `<linearGradient>` and `<radialGradient>` definitions through `url(#id)`; `gradientUnits` and percentage coordinates are honored. Not supported: `transform` attributes, `<style>` blocks, `stroke-dasharray`/`stroke-linecap`/`stroke-linejoin`, `gradientTransform`, `spreadMethod`, `stop-opacity`, `<text>`, `<image>`, `<use>`, `<clipPath>`, `<mask>`, `<pattern>`, and filters. Unsupported elements are skipped with console warning. Texture mode has none of these limits; browser rasterizes the file.

### When to use which mode

| Mode                                      | Best for | Cost |
| ----------------------------------------- | -------- | ---- |
| Texture (default)                         | Icons at known size, backgrounds, complex SVGs | One-time rasterization; fast per-frame; pixelates when scaled |
| Graphics (`parseAsGraphicsContext: true`) | Scalable icons, UI elements, runtime modification | Higher initial parse cost; crisp at any scale; shared contexts |

Same SVG at several sizes: Graphics mode usually faster (parse once, scale cheaply). One fixed-size SVG: texture mode is simpler and batches with other sprites.

## Common Mistakes

### [HIGH] Expecting scalability in texture mode

Wrong:

```ts
const icon = await Assets.load("icon.svg");
const sprite = new Sprite(icon);
sprite.scale.set(5); // pixelates
```

Correct (if you need scaling):

```ts
const context = await Assets.load({
  src: "icon.svg",
  data: { parseAsGraphicsContext: true },
});
const graphic = new Graphics(context);
graphic.scale.set(5); // crisp
```

Or rasterize at higher resolution:

```ts
const icon = await Assets.load({
  src: "icon.svg",
  data: { resolution: 5 },
});
```

Texture mode freezes at rasterization. Use Graphics mode or high `resolution` when final size isn't known upfront.


### [MEDIUM] External references in SVG files

SVGs referencing external images via `<image href="...">` may fail to load if reference is cross-origin without CORS headers. Inline image data as base64 or serve everything from same origin.


### [MEDIUM] CSS in `<style>` elements

Graphics mode does not read `<style>` blocks or class selectors at all. Only presentation attributes and inline `style="..."` are parsed, so class-styled shapes get default black fill. Move styling inline, or use texture mode for full CSS fidelity.


## API Reference

- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [LoadSVGConfig](https://pixijs.download/release/docs/assets.LoadSVGConfig.html.md)
- [Graphics](https://pixijs.download/release/docs/scene.Graphics.html.md)
- [GraphicsContext](https://pixijs.download/release/docs/scene.GraphicsContext.html.md)
