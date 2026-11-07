# HTMLText

Text rendered via SVG `<foreignObject>` wrapping an HTML fragment. Gives full HTML/CSS box model for typography (real `<b>`, `<i>`, `<br>`, `<div>`, line-breaks, nested styles, emoji), rasterized to texture. Use `HTMLText` for rich formatting, mixed content, inline custom tags, or markup canvas `Text` class can't express.

## Quick Start

```ts
const rich = new HTMLText({
  text: "<b>Bold</b> and <i>italic</i> text",
  style: {
    fontFamily: "Arial",
    fontSize: 24,
    fill: 0x333333,
    wordWrap: true,
    wordWrapWidth: 400,
  },
});

app.stage.addChild(rich);
```

`HTMLText` is a leaf. Uses `HTMLTextStyle`: `TextStyle` minus `leading`, `textBaseline`, `trim` and `filters` (SVG rendering path does not support those four).

## Construction

```ts
const minimal = new HTMLText({ text: "<b>Hello</b>" });

const styled = new HTMLText({
  text: "<i>Styled</i>",
  style: { fontSize: 24, fill: 0xffffff },
  anchor: 0.5,
  resolution: 2,
  autoGenerateMipmaps: true,
  textureStyle: { scaleMode: "linear" },
});
```

### HTMLTextOptions

`HTMLText` extends base `TextOptions` (typed with `HTMLTextStyle` / `HTMLTextStyleOptions` as style) and adds HTML-specific fields. Inherited `text`, `style`, `anchor`, `resolution` and `roundPixels` behave as in `references/text.md`. Table lists only HTMLText-specific additions.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `style` | `HTMLTextStyle \| HTMLTextStyleOptions` | `new HTMLTextStyle()` | HTML text style object or options. Matches `TextStyle` minus `leading`, `textBaseline`, `trim` and `filters`. Adds `cssOverrides` for raw CSS injection. |
| `textureStyle` | `TextureStyle \| TextureStyleOptions` | `undefined` | Scale mode for generated texture (`nearest` or `linear`); every other `TextureStyle` field ignored. (@advanced) |
| `autoGenerateMipmaps` | `boolean` | `TextureSource.defaultOptions.autoGenerateMipmaps` | Generate mipmaps for text texture; improves quality when scaled down. |

All `Container` options (`position`, `scale`, `tint`, `label`, `filters`, `zIndex`, etc.) also valid here. See constructor-options table in `references/scene-core-concepts.md` of `pixijs-scene-container` skill.

> `textureStyle` and `autoGenerateMipmaps` are also runtime instance properties, but are read only when a new texture is generated for the text (text, style or resolution change); `onViewUpdate()` alone does not regenerate it.

## Core Patterns

### Custom tags via `tagStyles`

```ts
const message = new HTMLText({
  text: "<warning>Low power</warning> <custom>Press any key</custom>",
  style: {
    fontFamily: "Arial",
    fontSize: 28,
    fill: 0xffffff,
    tagStyles: {
      warning: { fill: 0xff3333, fontWeight: "bold" },
      custom: { fill: 0x66ccff, fontStyle: "italic" },
    },
  },
});
```

`tagStyles` maps custom (or standard) HTML tag names to style overrides. Inheritance is automatic; nested `<warning>` inside `<custom>` inherits outer style. Standard tags like `<b>`, `<i>`, `<u>`, `<br>` work as expected.

### Raw CSS overrides

```ts
const styled = new HTMLText({
  text: "Underlined shadowed text",
  style: { fontSize: 24, fill: 0xffffff },
});

styled.style.addOverride("text-decoration: underline");
styled.style.addOverride("text-shadow: 2px 2px 4px rgba(0,0,0,0.5)");
```

For CSS properties without `TextStyle` equivalent, use `addOverride` to inject raw CSS. Use for `text-decoration`, `text-transform`, `letter-spacing` beyond what TextStyle exposes, and any other CSS property supported inside SVG `<foreignObject>`.

### Word wrap

```ts
const wrapped = new HTMLText({
  text: "A long paragraph of HTML text that should wrap automatically",
  style: {
    fontFamily: "Arial",
    fontSize: 20,
    fill: 0xffffff,
    wordWrap: true,
    wordWrapWidth: 300,
    align: "center",
  },
});
```

Browser's SVG layout handles word wrap, so it supports everything CSS wrapping supports, including hyphenation, justification and RTL scripts when font and rendered CSS support them.

### Async rendering

```ts
const htmlText = new HTMLText({
  text: "Initial content",
  style: { fontSize: 24, fill: 0xffffff },
});
htmlText.visible = false;
app.stage.addChild(htmlText);

app.ticker.addOnce(() => {
  htmlText.visible = true;
});
```

HTMLText renders to SVG blob, then texture. Texture is available one frame after creation. To have text ready before showing it, add it while hidden and reveal on next tick.

## Common Mistakes

### [HIGH] Updating HTMLText content every frame

Wrong:

```ts
app.ticker.add(() => {
  htmlText.text = `Score: ${score}`;
});
```

Correct:

```ts
const bitmap = new BitmapText({ text: "Score: 0", style });
app.ticker.add(() => {
  bitmap.text = `Score: ${score}`;
});
```

Each `HTMLText.text` assignment re-renders SVG, rasterizes it and uploads to GPU. At 60fps this is far too expensive. Use `BitmapText` for any text changing per-frame.


### [HIGH] Missing CORS headers on fonts

If HTML references web font from different origin without CORS headers, SVG `<foreignObject>` is tainted and rasterization fails (or falls back to default font). Host fonts on same origin or include `Access-Control-Allow-Origin`.


### [MEDIUM] Expecting HTMLText frame on creation

Wrong:

```ts
const text = new HTMLText({ text: "Hello", style });
text.x = (app.screen.width - text.width) / 2; // text.width is 0 here
```

Correct:

```ts
const text = new HTMLText({ text: "Hello", style });
app.ticker.addOnce(() => {
  text.x = (app.screen.width - text.width) / 2;
});
```

HTMLText measurement happens asynchronously. Defer layout calculations to next frame, or use canvas `Text` when you need immediate metrics.


## API Reference

- [HTMLText](https://pixijs.download/release/docs/scene.HTMLText.html.md)
- [HTMLTextStyle](https://pixijs.download/release/docs/text.HTMLTextStyle.html.md)
- [HTMLTextSystem](https://pixijs.download/release/docs/rendering.HTMLTextSystem.html.md)
