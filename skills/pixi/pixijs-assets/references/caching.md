# Caching

Every asset loaded via `Assets` stays cached until explicitly unloaded. Cache: global singleton keyed by resolved URL, alias, and any bundle identifier.

## Quick Start

```ts
await Assets.load("hero.png");

const cached = Assets.get("hero.png");
const sprite = new Sprite(cached);

await Assets.unload("hero.png");
```

`Assets.load` caches; `Assets.get` reads synchronously; `Assets.unload` removes and frees underlying GPU resource.

## Core Patterns

### Synchronous access to already-loaded assets

```ts
await Assets.load(["hero.png", "enemy.png"]);

const hero = Assets.get("hero");
const enemy = Assets.get("enemy");

if (hero) {
  app.stage.addChild(new Sprite(hero));
}
```

`Assets.get(alias)` returns `undefined` if not loaded yet. Synchronous; use in tight loops or where `await` is awkward.

### Multiple keys at once

```ts
await Assets.load(["hero", "enemy", "boss"]);

const all = Assets.get(["hero", "enemy", "boss"]);
const heroTex = all["hero"];
```

Array returns object keyed by alias; fetch a scene's assets in one call.

### Deduping load calls

```ts
const tex1 = await Assets.load("hero.png");
const tex2 = await Assets.load("hero.png");
console.log(tex1 === tex2); // true
```

Repeat `Assets.load` with same key returns same cached result immediately. Safe from concurrent async functions.

### Unloading

```ts
sprite.destroy();
await Assets.unload("hero.png");
```

`Assets.unload(id)` removes from cache, calls `destroy()` on texture (frees GPU memory), removes loader-specific wrappers.

### Unloading a bundle

```ts
level1Container.destroy({ children: true });
await Assets.unloadBundle("level1");
```

Prefer `unloadBundle` over manual iteration. No reference counting: every bundle asset is removed and destroyed, even if another bundle declares same `src`. That bundle's alias stays broken until reloaded.

### Inspecting the cache

```ts
import { Cache } from "pixi.js";

const key = "hero.png";
if (Cache.has(key)) {
  const texture = Cache.get(key);
}
```

Low-level `Cache` backs `Assets.get`: `has(key)`, `get(key)`, `set(key, value)`, `remove(key)`. Most code should use `Assets.get/unload`; direct `Cache` access suits diagnostics or custom loader plugins.

## Common Mistakes

### [CRITICAL] Using `Assets.get` before `Assets.load`

Wrong:

```ts
const texture = Assets.get("hero.png");
const sprite = new Sprite(texture); // texture is undefined
```

Correct:

```ts
await Assets.load("hero.png");
const texture = Assets.get("hero.png");
const sprite = new Sprite(texture);
```

`Assets.get` is synchronous; returns `undefined` before load. Always await `Assets.load` first, or use its return value.


### [HIGH] Not unloading between levels

Textures stay cached indefinitely. Loading level after level without `Assets.unload` or `Assets.unloadBundle` piles up GPU memory until browser limits hit.

```ts
await Assets.unloadBundle("level1");
await Assets.loadBundle("level2");
```


### [MEDIUM] Using sprites after unload

Wrong:

```ts
const sprite = new Sprite(texture);
await Assets.unload("hero.png");
// sprite still references the destroyed texture
```

Correct:

```ts
sprite.destroy();
await Assets.unload("hero.png");
```

`Assets.unload` destroys texture. Sprite still using it renders Texture.EMPTY or crashes, depending on backend. Destroy leaf (or reassign texture) before unloading.


## API Reference

- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [Cache](https://pixijs.download/release/docs/assets.Cache.html.md)
- [Texture](https://pixijs.download/release/docs/rendering.Texture.html.md)
