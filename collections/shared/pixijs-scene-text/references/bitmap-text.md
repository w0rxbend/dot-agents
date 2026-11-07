# BitmapText

Text rendered from pre-generated glyph texture atlas. Changing text string only repositions quads: no canvas re-render, no GPU upload per change. Use `BitmapText` for scores, timers, gameplay labels and any frequently changing text. Trade-off: limited styling, fixed glyph set, pixel-perfect only at font's native size (unless you use MSDF).

## Quick Start

```ts
const score = new BitmapText({
  text: "Score: 0",
  style: {
    fontFamily: "Arial",
    fontSize: 32,
    fill: 0xffffff,
  },
});

app.stage.addChild(score);

app.ticker.add(() => {
  score.text = `Score: ${Math.floor(performance.now() / 100)}`;
});
```

## Construction

```ts
const minimal = new BitmapText({ text: "Score: 0" });

const styled = new BitmapText({
  text: "Hello",
  style: { fontFamily: "GameFont", fontSize: 48, fill: 0xff0000 },
  anchor: 0.5,
  roundPixels: true,
});
```

### BitmapTextOptions

`BitmapText`'s constructor accepts base `TextOptions` directly (no extra bitmap-specific fields). Fields match `references/text.md`.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `text` | `TextString` | `''` | Text content. Same as `Text`. |
| `style` | `TextStyle \| TextStyleOptions` | `new TextStyle()` with `fill = 0xffffff` | Shared TextStyle type; respects fields like `fontFamily`, `fontSize`, `fill`, `stroke`, `align`, `wordWrap`, `wordWrapWidth` and `lineHeight`. Gradients as fill and filters are not respected. See TextStyle reference in `references/text.md`. |
| `anchor` | `PointData \| number` | `0` | Same as `Text`. |
| `resolution` | `number \| null` | `null` | Accepted but ignored at runtime; set resolution on `BitmapFont` via `BitmapFont.install({ resolution })` instead. Non-null value logs warning. |
| `roundPixels` | `boolean` | `false` | Same as `Text`. |

All `Container` options (`position`, `scale`, `tint`, `label`, `filters`, `zIndex`, etc.) also valid here. See constructor-options table in `references/scene-core-concepts.md` of `pixijs-scene-container` skill.

> `BitmapText` does NOT accept `textureStyle` or `autoGenerateMipmaps`; those are specific to canvas `Text` and `HTMLText`. Control atlas texture style at font install via `BitmapFont.install({ textureStyle })`.

## Core Patterns

### Dynamic fonts (system font -> runtime atlas)

System font without `BitmapFont.install`: first `BitmapText` with given `fontFamily` + `fontSize` generates atlas lazily. Later `BitmapText` instances reuse it. System also scales existing close-match size instead of re-generating.

### Pre-installed fonts

```ts
import { BitmapFont } from "pixi.js";

BitmapFont.install({
  name: "GameFont",
  style: {
    fontFamily: "Arial",
    fontSize: 48,
    fill: 0xffffff,
    stroke: { color: "#000000", width: 2 },
  },
});

const title = new BitmapText({
  text: "Level 1",
  style: { fontFamily: "GameFont", fontSize: 48, fill: 0x00ff00 },
});
```

`BitmapFont.install` pre-generates atlas, so first `BitmapText` render has no setup cost. Use for known fixed styles in a game.

#### Install options

| Option | Purpose |
| --- | --- |
| `chars` | Character set to pre-render. Accepts string, nested ranges or preset: `BitmapFontManager.ALPHA`, `BitmapFontManager.NUMERIC`, `BitmapFontManager.ALPHANUMERIC`, `BitmapFontManager.ASCII`. Essential for non-ASCII, CJK or restricted charsets. |
| `resolution` | Texture atlas resolution. Default `1`. Use `window.devicePixelRatio` for HiDPI displays. |
| `padding` | Glyph padding inside atlas. Default `4`. Raise to avoid bleeding at large scales. |
| `skipKerning` | Skip kerning metadata to save memory and install time. Default `false`. |
| `textureStyle` | `TextureStyle`/`TextureStyleOptions` override for generated atlas (e.g. `{ scaleMode: 'nearest' }` for pixel fonts). |
| `dynamicFill` | Allow runtime tinting via `BitmapText.tint`. Requires font `style.fill` to be white, no stroke, no drop shadow, or drop shadow with color `0x000000` (black). Idiomatic way to color bitmap text without generating new atlas per color. |

```ts
import { BitmapFont, BitmapFontManager } from "pixi.js";

BitmapFont.install({
  name: "UIFont",
  chars: BitmapFontManager.ALPHANUMERIC,
  resolution: window.devicePixelRatio,
  padding: 8,
  skipKerning: true,
  textureStyle: { scaleMode: "nearest" },
  dynamicFill: true,
  style: { fontFamily: "Arial", fontSize: 32, fill: 0xffffff },
});

const hp = new BitmapText({
  text: "100",
  style: { fontFamily: "UIFont", fill: "red" },
});
const mp = new BitmapText({
  text: "50",
  style: { fontFamily: "UIFont", fill: "blue" },
});
```

### Loaded bitmap fonts (FNT / XML)

```ts
import "pixi.js/text-bitmap";
import { Assets, BitmapText } from "pixi.js";

await Assets.load("fonts/arcade.fnt");

const arcade = new BitmapText({
  text: "HIGH SCORE",
  style: { fontFamily: "arcade", fontSize: 36 },
});
```

Load `.fnt` or `.xml` files (AngelCode BMFont format) via Assets. Generate them from `.ttf` / `.otf` with [AssetPack](https://pixijs.io/assetpack/).

### MSDF / SDF fonts for crisp scaling

Multi-channel Signed Distance Field (MSDF) fonts stay sharp at any size. Generate with [AssetPack](https://pixijs.io/assetpack/) (Pixi's own asset pipeline; takes `.ttf` or `.otf`, emits `.fnt` + atlas) or [msdf-bmfont](https://msdf-bmfont.donmccurdy.com/). Load via Assets; detected automatically when FNT file declares a distanceField section.

```ts
await Assets.load("fonts/msdf-hero.fnt");

const heading = new BitmapText({
  text: "Title",
  style: { fontFamily: "msdf-hero", fontSize: 120 },
});

heading.scale.set(2);
```

MSDF fonts trade CPU rendering time for custom fragment shader.

### Word wrap

```ts
const paragraph = new BitmapText({
  text: "A long wrapped paragraph of bitmap text",
  style: {
    fontFamily: "Arial",
    fontSize: 24,
    wordWrap: true,
    wordWrapWidth: 300,
    lineHeight: 30,
  },
});
```

Standard TextStyle wrapping properties work. Line-height and alignment (`align: 'center' | 'left' | 'right'`) apply to wrapped output.

## Common Mistakes

### [HIGH] Not importing `pixi.js/text-bitmap` in custom builds

Wrong (custom build with `skipExtensionImports: true`):

```ts
import { Assets } from "pixi.js";
await Assets.load("font.fnt");
```

Correct:

```ts
import "pixi.js/text-bitmap";
import { Assets } from "pixi.js";
await Assets.load("font.fnt");
```

Without side-effect import, asset loader does not recognize `.fnt` and `.xml` files; call silently succeeds but returns raw data instead of `BitmapFont`.


### [MEDIUM] Setting `resolution` on BitmapText

Wrong:

```ts
text.resolution = 2;
```

`BitmapText` ignores `resolution` and logs warning. Effective resolution is baked into `BitmapFont` at install time. For higher resolution, install font with larger `fontSize` and scale text down.


### [MEDIUM] Missing characters silently dropped

If font atlas lacks a glyph (e.g., rare Unicode character), glyph is silently skipped with no visible error. Text may look incomplete. For unknown or user-generated content, fall back to canvas `Text` or `HTMLText`.


### [HIGH] Using BitmapText for CJK or emoji-heavy content

CJK (Chinese/Japanese/Korean), Arabic and emoji-heavy strings need thousands of glyphs. Bitmap atlas holding all of them exceeds GPU texture-size limits. Use `Text` or `HTMLText` for unpredictable or very large character sets.


## API Reference

- [BitmapText](https://pixijs.download/release/docs/scene.BitmapText.html.md)
- [BitmapFont](https://pixijs.download/release/docs/text.BitmapFont.html.md)
- [BitmapFontManager](https://pixijs.download/release/docs/text.BitmapFontManager.html.md)
- [AbstractBitmapFont](https://pixijs.download/release/docs/text.AbstractBitmapFont.html.md)
