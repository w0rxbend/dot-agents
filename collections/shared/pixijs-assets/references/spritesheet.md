# Spritesheet: Texture Atlases and Animations

Load and use texture atlases and animation sheets with `Spritesheet` class. Atlases cut draw calls by packing many textures into one image.

## Quick Start

```ts
const sheet = await Assets.load("spritesheet.json");

const hero = new Sprite(sheet.textures["hero.png"]);
app.stage.addChild(hero);

const walk = new AnimatedSprite(sheet.animations["walk"]);
walk.animationSpeed = 0.15;
walk.play();
app.stage.addChild(walk);
```

`Assets.load()` fetches JSON, loads atlas image, calls `sheet.parse()` automatically. Returns `Spritesheet` instance.

## Core Patterns

### SpritesheetData JSON format

```json
{
  "frames": {
    "hero.png": {
      "frame": { "x": 0, "y": 0, "w": 64, "h": 64 },
      "sourceSize": { "w": 64, "h": 64 },
      "spriteSourceSize": { "x": 0, "y": 0, "w": 64, "h": 64 },
      "anchor": { "x": 0.5, "y": 0.5 },
      "borders": { "left": 10, "top": 10, "right": 10, "bottom": 10 }
    },
    "walk_01.png": {
      "frame": { "x": 64, "y": 0, "w": 64, "h": 64 },
      "rotated": true,
      "trimmed": true,
      "sourceSize": { "w": 80, "h": 80 },
      "spriteSourceSize": { "x": 8, "y": 8, "w": 64, "h": 64 }
    }
  },
  "animations": {
    "walk": ["walk_01.png", "walk_02.png", "walk_03.png"]
  },
  "meta": {
    "image": "spritesheet.png",
    "size": { "w": 512, "h": 256 },
    "scale": "1"
  }
}
```

Key fields:

- `frames`: frame names to rectangle data, trim info, anchors, 9-slice borders.
- `rotated`: frame stored rotated 90 degrees in atlas; parser swaps width/height automatically.
- `trimmed`: transparent padding removed. `sourceSize` is original dimensions; `spriteSourceSize` is trimmed region within it.
- `animations`: animation names to ordered arrays of frame names.
- `meta.scale`: texture source resolution. `"2"` means atlas is @2x.
- `meta.image`: atlas image filename, resolved relative to JSON file.

### Manual Spritesheet creation

```ts
const texture = await Assets.load("atlas.png");
const sheet = new Spritesheet({
  texture,
  data: spritesheetJsonData,
  cachePrefix: "myAtlas_",
});
await sheet.parse();

const frame = new Sprite(sheet.textures["hero.png"]);
```

`parse()` is async for large sheets (over 1000 frames), batching texture creation across multiple frames. Smaller sheets can also use `parseSync()`.

`cachePrefix` prefixes all cached texture names, preventing collisions when atlases share frame names (e.g., `"hero.png"` in two sheets).

### Preloaded texture with Assets

```ts
const atlasTexture = await Assets.load("images/spritesheet.png");

Assets.add({
  alias: "atlas",
  src: "images/spritesheet.json",
  data: { texture: atlasTexture },
});
const sheet = await Assets.load("atlas");
```

### Multi-pack spritesheets

With `meta.related_multi_packs` present, loader automatically loads and links related spritesheets. All linked sheets live in `sheet.linkedSheets`.

### Cleanup

```ts
sheet.destroy();
sheet.destroy(true); // also destroys the base atlas texture
```

## Common Mistakes

### [HIGH] Spritesheet meta.scale behavior change

In v8, `meta.scale` directly sets texture source resolution. Atlas exported at @2x with `meta.scale` `"1"` renders frames at double intended size. Ensure `meta.scale` matches atlas image's actual resolution. Tools like TexturePacker set it automatically.

### [MEDIUM] Not awaiting spritesheet parse

`parse()` is async. Reading `sheet.textures` before it resolves gives undefined entries.

## API Reference

- [Spritesheet](https://pixijs.download/release/docs/assets.Spritesheet.html.md)
- [spritesheetAsset](https://pixijs.download/release/docs/assets.spritesheetAsset.html.md)
- [AnimatedSprite](https://pixijs.download/release/docs/scene.AnimatedSprite.html.md)
