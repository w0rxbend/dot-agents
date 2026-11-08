# Bundles

Named asset group, loaded or unloaded as a unit. Batch assets per game level, UI screen, or feature so one `loadBundle(name)` call resolves everything that context needs.

## Quick Start

```ts
Assets.addBundle("level1", [
  { alias: "bg", src: "level1/background.png" },
  { alias: "tileset", src: "level1/tiles.json" },
  { alias: "theme", src: "level1/music.mp3" },
]);

const resources = await Assets.loadBundle("level1");
const bg = Sprite.from("bg");
```

`loadBundle(name)` returns `Record<alias, asset>`. Each alias also works with `Assets.get(alias)` once bundle resolves.

## Core Patterns

### Programmatic bundles

`addBundle(name, assets)` registers bundle at runtime. Entries use same `{ alias, src, data? }` shape as `Assets.add()`.

### Loading multiple bundles at once

```ts
await Assets.loadBundle(["ui", "level1", "sounds"]);
```

Array of names loads in parallel. Result keyed by bundle name: `{ ui: {...}, level1: {...}, sounds: {...} }`.

### Progress across a bundle

```ts
await Assets.loadBundle("level1", (progress) => {
  loadingBar.width = progress * maxBarWidth;
});
```

Second argument: `ProgressCallback`, fired as each asset completes. Progress normalized `[0, 1]` across whole bundle.

### Unloading a bundle

```ts
await Assets.unloadBundle("level1");
```

Destroys every bundle asset, frees GPU memory, removes cache entries.

### Sharing assets between bundles

```ts
Assets.addBundle("main", [{ alias: "hero", src: "hero.png" }]);
Assets.addBundle("bossArea", [{ alias: "hero", src: "hero.png" }]);
```

Same alias with same `src` in two bundles: texture loads once, shared. No reference counting: unloading either bundle destroys it, and other bundle's alias stays broken until reloaded.

### Bundle IDs

```ts
const resources = await Assets.loadBundle("level1");
const bg = resources["bg"];

const fromCache = Assets.get("bg");

const fromNamespaced = Assets.get("level1-bg");
```

Resolver stores bundle assets under combined key like `'level1-bg'` by default. Plain `'bg'` still resolves via resolver shortcuts. To change format, pass `bundleIdentifier` to `Assets.init()`.

## Common Mistakes

### [HIGH] Unloading while assets are still in use

Wrong:

```ts
await Assets.unloadBundle("level1");
// level1 sprites still on the stage; they now reference destroyed textures
```

Correct:

```ts
level1Container.destroy({ children: true });
await Assets.unloadBundle("level1");
```

Always destroy or detach display objects using bundle textures before unloading. Otherwise renderer hits freed GPU memory and errors.


### [MEDIUM] Confusing `addBundle` and `init` manifests

Wrong:

```ts
await Assets.init();
Assets.addBundle('ui', [...]);
await Assets.loadBundle('ui');
```

Not actually wrong; both work. But manifest in `Assets.init({ manifest: {...} })` registers all bundles at init, in one place. Prefer manifests when all bundles known upfront; `addBundle` when bundles are discovered dynamically at runtime.


## API Reference

- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [AssetsBundle](https://pixijs.download/release/docs/assets.AssetsBundle.html.md)
- [Resolver](https://pixijs.download/release/docs/assets.Resolver.html.md)
