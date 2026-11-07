# Text (Canvas Text)

Primary text renderer in PixiJS v8. Rasterizes strings to off-screen canvas via native Canvas API, then uploads result as GPU texture. Use `Text` for high-quality typography, styled labels, UI text, and anything where visual fidelity matters more than update speed.

## Quick Start

```ts
const text = new Text({
  text: "Hello PixiJS",
  style: {
    fontFamily: "Arial",
    fontSize: 36,
    fill: 0xffffff,
    stroke: { color: "#4a1850", width: 5 },
    dropShadow: {
      color: "#000000",
      blur: 4,
      distance: 6,
      angle: Math.PI / 6,
    },
  },
  anchor: 0.5,
  x: 400,
  y: 40,
});

app.stage.addChild(text);
```

Text is a leaf (`allowChildren = false`).

## Construction

```ts
const minimal = new Text({ text: "Hello" });

const styled = new Text({
  text: "Styled Text",
  style: { fontSize: 24, fill: 0xff1010 },
  anchor: 0.5,
  resolution: 2,
  roundPixels: true,
});

const crisp = new Text({
  text: "Crisp Text",
  style: { fontSize: 32 },
  textureStyle: { scaleMode: "nearest" },
  autoGenerateMipmaps: true,
});
```

### CanvasTextOptions

Options accepted by `new Text({ ... })`. Concrete `Text` constructor takes `CanvasTextOptions`, which extends base `TextOptions` with canvas-specific `textureStyle` and `autoGenerateMipmaps` fields.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `text` | `TextString` (`string \| number \| { toString(): string }`) | `''` | Text content to display; `'\n'` inserts line break. |
| `style` | `TextStyle \| TextStyleOptions` | `new TextStyle()` | Text style object or options. See TextStyle docs below for field details. |
| `anchor` | `PointData \| number` | `0` | Draw origin in `[0, 1]`; `0.5` is center, `1` is bottom-right. |
| `resolution` | `number` | `null` (auto) | Pixel density of rasterized texture; `null` follows renderer's resolution (setting to `null` at runtime enables auto-resolution; interface type is `number`). Higher = sharper on high-DPI displays. |
| `roundPixels` | `boolean` | `false` | Snap rendered x/y to whole pixels to avoid sub-pixel anti-aliasing. |
| `textureStyle` | `TextureStyle \| TextureStyleOptions` | `undefined` | Scale mode for generated texture (`nearest` or `linear`); every other `TextureStyle` field ignored. (@advanced) |
| `autoGenerateMipmaps` | `boolean` | `TextureSource.defaultOptions.autoGenerateMipmaps` | Generate mipmaps for text texture; improves quality when scaled down. |

All `Container` options (`position`, `scale`, `tint`, `label`, `filters`, `zIndex`, etc.) also valid here. See constructor-options table in `references/scene-core-concepts.md` of `pixijs-scene-container` skill.

## Core Patterns

### TextStyle properties

```ts
const styled = new Text({
  text: "Styled",
  style: {
    fontFamily: "Arial",
    fontSize: 32,
    fontWeight: "bold",
    fontStyle: "italic",
    fill: 0xff1010,
    stroke: { color: "#4a1850", width: 5 },
    dropShadow: {
      color: "#000000",
      blur: 4,
      distance: 6,
      angle: Math.PI / 6,
      alpha: 0.8,
    },
    align: "center",
    wordWrap: true,
    wordWrapWidth: 300,
    lineHeight: 45,
    letterSpacing: 2,
    padding: 4,
  },
});
```

Key TextStyle properties:

- `fontFamily`, `fontSize`, `fontWeight`, `fontStyle`
- `fill`: color, gradient, or pattern (same `FillInput` as `Graphics`)
- `stroke`: `{ color, width }` object
- `dropShadow`: `{ color, blur, distance, angle, alpha }`
- `wordWrap`, `wordWrapWidth`
- `breakWords`: allow breaking mid-word when wrapping. Requires `wordWrap: true`
- `whiteSpace`: `'normal' | 'pre' | 'pre-line'` whitespace handling for multi-line strings
- `align`: `'left'`, `'center'`, `'right'`, `'justify'`; only affects multi-line text
- `textBaseline`: `'alphabetic' | 'top' | 'hanging' | 'middle' | 'ideographic' | 'bottom'`
- `lineHeight`, `letterSpacing`
- `leading`: extra line spacing in pixels on top of `lineHeight`
- `trim`: boolean; crop transparent padding after rasterization (expensive, use only when needed)
- `padding`: extra space around rendered texture; increase when stroke or shadow gets clipped
- `filters`: array of Pixi filters applied to generated text texture at bake time; cheaper than filters on `Text` node for static strings
- `tagStyles`: per-tag inline style overrides

### Tagged text

```ts
const alert = new Text({
  text: "<red>Warning:</red> system <b>overloaded</b>",
  style: {
    fontSize: 24,
    fill: 0xffffff,
    tagStyles: {
      red: { fill: 0xff0000 },
      b: { fontWeight: "bold" },
    },
  },
});
```

Tags parsed only when `tagStyles` has entries; without entries, `<` is treated literally. Nested tags inherit from outer tags via internal style stack.

### Font loading

```ts
await Assets.load({
  src: "my-font.woff2",
  data: { family: "MyFont" },
});

const text = new Text({
  text: "Custom Font",
  style: { fontFamily: "MyFont", fontSize: 36, fill: 0xffffff },
});
```

Supported formats: `woff2` (preferred), `woff`, `ttf`, `otf`. `data` object is forwarded to `FontFace`; valid fields are `family`, `display`, `style`, `weights` (string array, e.g., `['normal', 'bold']`), `stretch`, `unicodeRange`, `featureSettings`, `variant`.

```ts
await Assets.load({
  src: "titan-one.woff",
  data: { family: "Titan One", weights: ["normal", "bold"] },
});
```

### Dynamic content

```ts
app.ticker.add(() => {
  const next = `Score: ${score}`;
  if (scoreText.text !== next) {
    scoreText.text = next;
  }
});
```

Guard text updates with equality check when using `Text` for live values.

### Sharing a TextStyle across instances

```ts
const style = new TextStyle({ fontSize: 24, fill: 0xffffff });

const title = new Text({ text: "Title", style });
const label = new BitmapText({ text: "Label", style });

style.fill = 0xff0000; // both re-render

title.destroy(); // detaches from `style`; `label` keeps using it
```

Any number of `Text`, `BitmapText` and `HTMLText` objects can share one `TextStyle` instance; changing it re-renders all of them. `destroy()` detaches text from style without destroying it. Pass `destroy({ style: true })` (or `destroy(true)`) only when no other text object uses that style, since it destroys shared instance.

### Gradient and pattern fills

```ts
import { FillGradient } from "pixi.js";

const gradient = new FillGradient({
  end: { x: 0, y: 1 },
  colorStops: [
    { color: 0xff0000, offset: 0 },
    { color: 0x0000ff, offset: 1 },
  ],
});

const title = new Text({
  text: "Gradient",
  style: { fontSize: 64, fill: gradient },
});
```

For texture fill, pass a `FillPattern`. Its constructor takes options object; legacy positional form `new FillPattern(texture, repetition)` also accepted.

```ts
import { Assets, FillPattern } from "pixi.js";

const pattern = new FillPattern({
  texture: await Assets.load("bricks.png"),
  repetition: "repeat",
});

const label = new Text({
  text: "PixiJS",
  style: { fontSize: 64, fill: pattern },
});
```

Canvas-rendered text ignores pattern's `textureSpace`; texture tiles in text's pixel space at native size. Use `pattern.setTransform(matrix)` to scale, rotate or offset tiles. `FillPattern` works for `stroke` too, e.g. `style: { stroke: { fill: pattern, width: 10 } }`.

`fill` accepts any `FillInput` that `Graphics` accepts: gradients, patterns, solid colors, arrays of stops.

## Common Mistakes

### [HIGH] Updating Text content every frame

Wrong:

```ts
app.ticker.add(() => {
  scoreText.text = `Score: ${score}`;
});
```

Correct:

```ts
const scoreText = new BitmapText({ text: "Score: 0", style });
app.ticker.add(() => {
  scoreText.text = `Score: ${score}`;
});
```

Every `Text` update re-rasterizes full string and uploads new texture. At 60fps this burns frame budget. Use `BitmapText` for values changing per-frame, or at minimum guard with equality check against previous string.


### [HIGH] Using positional constructor args

Wrong:

```ts
const text = new Text("Hello", { fontSize: 24 });
```

Correct:

```ts
const text = new Text({ text: "Hello", style: { fontSize: 24 } });
```

v8 `Text` uses options object. v7 `(string, style)` signature not supported.


### [MEDIUM] Stroke or shadow getting clipped at edges

Wrong:

```ts
const text = new Text({
  text: "Hello",
  style: { stroke: { color: "red", width: 10 } },
});
```

Correct:

```ts
const text = new Text({
  text: "Hello",
  style: { stroke: { color: "red", width: 10 }, padding: 10 },
});
```

Underlying canvas is sized from text metrics; heavy strokes or drop-shadows render past those bounds and get clipped. Add `padding` to style to enlarge texture.


## API Reference

- [Text](https://pixijs.download/release/docs/scene.Text.html.md)
- [TextStyle](https://pixijs.download/release/docs/text.TextStyle.html.md)
- [TextOptions](https://pixijs.download/release/docs/text.TextOptions.html.md)
- [AbstractText](https://pixijs.download/release/docs/scene.AbstractText.html.md)
