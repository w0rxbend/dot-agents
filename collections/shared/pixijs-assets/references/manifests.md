# Manifests

Manifest: JSON-shaped description of every app bundle. Pass to `Assets.init({ manifest })`; resolver registers all bundles at startup, so later code refers to them by name. Use when asset graph is known upfront and you want one source of truth.

## Quick Start

```ts
await Assets.init({
  manifest: {
    bundles: [
      {
        name: "load-screen",
        assets: [{ alias: "logo", src: "logo.png" }],
      },
      {
        name: "game",
        assets: [
          { alias: "hero", src: "hero.{webp,png}" },
          { alias: "enemies", src: "enemies.json" },
        ],
      },
    ],
  },
});

await Assets.loadBundle("load-screen");
await Assets.loadBundle("game");
```

Each bundle: `name` plus `assets` array of `UnresolvedAsset` entries. Format expansions (`{webp,png}`) and resolution patterns (`@{1,2}x`) work in `src`.

## Core Patterns

### Inline manifest object

Any plain object matching `AssetsManifest` shape works. Pass directly to `init`.

### Manifest from a URL

```ts
await Assets.init({ manifest: "assets/manifest.json" });
```

String `manifest` is loaded as JSON first, then bundles register. Useful when build tooling generates manifest at deploy time (e.g., with `@assetpack/core`).

### Format and resolution patterns in manifests

```ts
const manifest = {
  bundles: [
    {
      name: "hero",
      assets: [{ alias: "hero", src: "hero@{0.5,1,2}x.{webp,avif,png}" }],
    },
  ],
};
```

Resolver expands pattern to six candidates, picks best match by `window.devicePixelRatio` and browser format support. Set preferences in `Assets.init({ texturePreference: {...} })`.

### Multiple aliases per entry

```ts
const manifest = {
  bundles: [
    {
      name: "characters",
      assets: [
        { alias: ["hero", "player"], src: "hero.png" },
        { alias: "npc1", src: "villager.png" },
      ],
    },
  ],
};
```

Entry can expose several aliases. `Assets.load('hero')` and `Assets.load('player')` return same texture.

### Data options in manifest entries

```ts
const manifest = {
  bundles: [
    {
      name: "pixel-art",
      assets: [
        {
          alias: "tile",
          src: "tile.png",
          data: { scaleMode: "nearest" },
        },
      ],
    },
  ],
};
```

Entry `data` field goes to loader. Use for `scaleMode`, `autoGenerateMipmaps`, `parseAsGraphicsContext`, FontFace descriptors, etc.

### Background-loading from a manifest

```ts
await Assets.init({ manifest });
await Assets.loadBundle("load-screen");

Assets.backgroundLoadBundle("game");
await Assets.loadBundle("game");
```

After init, start background loading other bundles right away. Non-blocking; later `await Assets.loadBundle('game')` resolves fast if background work finished.

## Common Mistakes

### [HIGH] Calling `Assets.init` twice

Wrong:

```ts
await Assets.init({ manifest });
await Assets.init({ basePath: "https://cdn.example.com/" });
```

Correct:

```ts
await Assets.init({ manifest, basePath: "https://cdn.example.com/" });
```

`Assets.init()` can only be called once; second call is ignored with warning. Put all configuration in one call.


### [MEDIUM] Missing format expansion on manifest entries

Wrong:

```ts
{ alias: 'hero', src: 'hero.webp' }
```

Correct:

```ts
{ alias: 'hero', src: 'hero.{webp,png}' }
```

Only one format blocks resolver fallback on browsers without WebP/AVIF support. Always list at least one fallback.


### [MEDIUM] Loading manifest after `Assets.add`

If `Assets.add(...)` or `Assets.addBundle(...)` runs before `Assets.init({ manifest })`, manifest bundles append to existing state, but preference-detection (format, resolution) hasn't run yet. Prefer `init` first, then ad-hoc assets.


## API Reference

- [AssetsManifest](https://pixijs.download/release/docs/assets.AssetsManifest.html.md)
- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [Resolver](https://pixijs.download/release/docs/assets.Resolver.html.md)
- [UnresolvedAsset](https://pixijs.download/release/docs/assets.UnresolvedAsset.html.md)
