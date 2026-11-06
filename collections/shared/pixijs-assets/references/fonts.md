# Fonts

PixiJS loads two font kinds via `Assets`: web fonts (TTF/OTF/WOFF/WOFF2) via `loadWebFont`, bitmap fonts (FNT/XML) via `loadBitmapFont`. Web fonts serve `Text` and `HTMLText`. Bitmap fonts serve `BitmapText`, for GPU-friendly rendering without runtime text layout.

## Web fonts

### Quick Start

```ts
await Assets.load("fonts/titan-one.woff2");

const text = new Text({
  text: "Hello world",
  style: { fontFamily: "Titan One", fontSize: 48 },
});
```

After load, use derived family name in any `TextStyle`. PixiJS registers font with browser `FontFaceSet`, so DOM elements and Canvas can use it too.

### Family name derivation

```ts
// Loaded URL               → Derived family name
// fonts/titan-one.woff     → 'Titan One'
// fonts/open_sans.ttf      → 'Open Sans'
// fonts/my-custom-font.otf → 'My Custom Font'
```

Default family: filename without extension, dashes and underscores become spaces, title-cased. Override with `data.family`.

### Load options via `data`

```ts
await Assets.load({
  alias: "hero-font",
  src: "fonts/hero.woff2",
  data: {
    family: "HeroFont",
    weights: ["normal", "bold"],
    style: "italic",
    display: "swap",
    unicodeRange: "U+0000-00FF",
    stretch: "expanded",
    featureSettings: '"liga" 1',
  },
});
```

`data` fields map directly to FontFace descriptors:

| Option            | Purpose |
| ----------------- | ------- |
| `family`          | Override derived family name |
| `weights`         | Weights to register. One `FontFace` per weight, all on same URL. Valid values: `'normal'`, `'bold'`, `'100'`–`'900'` |
| `style`           | `'normal'`, `'italic'`, `'oblique'` |
| `display`         | CSS `font-display` (`'auto'`, `'block'`, `'swap'`, `'fallback'`, `'optional'`) |
| `unicodeRange`    | Restrict covered codepoints |
| `stretch`         | `'normal'`, `'condensed'`, `'expanded'`, etc. |
| `variant`         | CSS font-variant value |
| `featureSettings` | OpenType feature settings like `'"liga" 1, "dlig" 1'` |

### Loading multiple weights

```ts
await Assets.load({
  src: "fonts/inter.woff2",
  data: {
    family: "Inter",
    weights: ["400", "700"],
  },
});
```

One URL registers several weights. Use for variable fonts, or when your platform lets one file satisfy several weights.

### Supported extensions

`.ttf`, `.otf`, `.woff`, `.woff2`. WOFF2 is smallest and supported in all current browsers. Prefer it unless targeting very old environments.

## Bitmap fonts

### Quick Start

```ts
import "pixi.js/text-bitmap";

await Assets.load("fonts/arial.fnt");

const text = new BitmapText({
  text: "Score: 9999",
  style: { fontFamily: "Arial", fontSize: 32 },
});
```

### Supported formats

| Extension | Format             |
| --------- | ------------------ |
| `.fnt`    | BMFont text or XML |
| `.xml`    | BMFont XML         |

Parser sniffs content to choose text or XML.

### Texture page loading

```ts
// my-font.fnt references my-font_0.png, my-font_1.png
await Assets.load("fonts/my-font.fnt");
```

`.fnt` data names page images by filename. Parser resolves them relative to `.fnt` URL and loads them. Search params on `.fnt` URL (e.g. cache busting) carry over to page texture URLs.

### Signed Distance Field (SDF) fonts

Parser detects distance field metadata in `.fnt`, then enables `linear` scale mode and disables mipmaps. Caller configures nothing. SDF fonts stay crisp at any size, so one bitmap font serves many sizes.

### Accessing the BitmapFont instance

```ts
await Assets.load({ alias: "arial", src: "fonts/arial.fnt" });

const font = Assets.get("arial");
console.log(font.chars);
console.log(font.fontFamily);
```

Cached asset is `BitmapFont`. `Assets.get('arial')` and `Assets.get('arial-bitmap')` both return it; `Assets.get('Arial-bitmap')` works if `fontFamily` matches.

## Forcing the font parser

If font URL lacks extension, force loader:

```ts
await Assets.load({
  src: "https://cdn.example.com/fonts/abc123",
  parser: "web-font",
  data: { family: "Hero", weights: ["400", "700"] },
});

await Assets.load({
  src: "https://cdn.example.com/fonts/hero-bmfont",
  parser: "bitmap-font",
});
```

See main `SKILL.md` section "Forcing a parser with `parser`" for all parser IDs.

## Common Mistakes

### [HIGH] Forgetting the bitmap-font import

Wrong:

```ts
import { Assets, BitmapText } from "pixi.js";
await Assets.load("arial.fnt");
const text = new BitmapText({ text: "Hi", style: { fontFamily: "Arial" } });
app.stage.addChild(text);
```

Correct:

```ts
import "pixi.js/text-bitmap";
import { Assets, BitmapText } from "pixi.js";
await Assets.load("arial.fnt");
const text = new BitmapText({ text: "Hi", style: { fontFamily: "Arial" } });
app.stage.addChild(text);
```

`Assets.load('arial.fnt')` succeeds in default bundle and returns `BitmapFont`, but `'pixi.js/text-bitmap'` registers `CanvasBitmapTextPipe` and `BitmapTextPipe`. Without it, `BitmapText` renders nothing or errors at render time.


### [HIGH] Using Text before the font is loaded

Wrong:

```ts
const text = new Text({ text: "Hi", style: { fontFamily: "Hero" } });
Assets.load("fonts/hero.woff2");
```

Correct:

```ts
await Assets.load("fonts/hero.woff2");
const text = new Text({ text: "Hi", style: { fontFamily: "Hero" } });
```

If family isn't registered yet, browser falls back to system font and `Text` caches that fallback style. Reloading font doesn't repaint existing Text objects.


### [MEDIUM] Family name mismatch

Without `data.family`, family derives from filename: `my_hero_font.woff` becomes `'My Hero Font'`. Use exactly that in `TextStyle.fontFamily`, or set `data.family` explicitly.


## API Reference

- [loadWebFont](https://pixijs.download/release/docs/assets.loadWebFont.html.md)
- [loadBitmapFont](https://pixijs.download/release/docs/assets.loadBitmapFont.html.md)
- [LoadFontData](https://pixijs.download/release/docs/assets.LoadFontData.html.md)
- [BitmapFont](https://pixijs.download/release/docs/scene.BitmapFont.html.md)
