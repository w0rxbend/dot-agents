# Background Loading

Fetches and prepares assets passively while other work runs. Use to prime next level during play, preload during splash screen, or prep UI assets during initial load. `backgroundLoad` and `backgroundLoadBundle` are non-blocking and return immediately.

## Quick Start

```ts
await Assets.loadBundle("menu");
showMenu();

Assets.backgroundLoadBundle("level1");

playerClicksStart(() => {
  Assets.loadBundle("level1").then(() => startLevel());
});
```

## Core Patterns

### Background-loading a single asset

```ts
Assets.backgroundLoad("images/level2-assets.png");

// later, when we need it:
const texture = await Assets.load("images/level2-assets.png");
```

Fire-and-forget. Loads one asset at a time to avoid blocking main thread. Later `Assets.load(url)` for same asset resolves immediately if done, else waits for in-progress load.

### Background-loading an array

```ts
Assets.backgroundLoad([
  "images/sprite1.png",
  "images/sprite2.png",
  "images/background.png",
]);
```

Queues several assets; processed sequentially.

### Background-loading a bundle

```ts
await Assets.init({
  manifest: {
    bundles: [
      { name: "home", assets: [{ alias: "bg", src: "home-bg.png" }] },
      { name: "level-1", assets: [{ alias: "map", src: "level1-map.json" }] },
    ],
  },
});

await Assets.loadBundle("home");
showHome();

Assets.backgroundLoadBundle("level-1");

onPlayClicked(async () => {
  await Assets.loadBundle("level-1");
  startLevel();
});
```

Same for bundles, one asset at a time. Bundle must exist via manifest or `addBundle`.

### Interrupting background loading

```ts
Assets.backgroundLoadBundle("level-2");

onPlayerDecidedLevel3(async () => {
  await Assets.loadBundle("level-3");
});
```

`Assets.load()` or `Assets.loadBundle()` safely interrupts background loading. Current background asset finishes, then explicit load takes priority and resolves normally.

### Combining with a progress bar

Typical split: background for nice-to-have preloads, foreground `Assets.loadBundle(name, onProgress)` for bundles you wait on.

## Common Mistakes

### [HIGH] Expecting progress from background loading

Wrong:

```ts
Assets.backgroundLoadBundle("level2", (p) => updateBar(p));
```

Correct:

```ts
Assets.backgroundLoadBundle("level2");
// show a spinner or no UI while it runs
```

`backgroundLoad` and `backgroundLoadBundle` don't accept progress callbacks. For visible progress, use foreground `Assets.load` / `Assets.loadBundle` with `onProgress`.


### [MEDIUM] Assuming background load completes before next foreground load

Wrong:

```ts
Assets.backgroundLoadBundle("level-2");
setTimeout(() => startLevel2(), 0);
```

Correct:

```ts
Assets.backgroundLoadBundle("level-2");

onStart(async () => {
  await Assets.loadBundle("level-2");
  startLevel2();
});
```

Best-effort. If player hits Start first, foreground `loadBundle` still awaits remaining work. Always `await` real load before using assets.


### [MEDIUM] Background-loading assets that are never used

Each queued load costs bandwidth and GPU memory, wasted if player never visits level 2. Background-load only assets you're confident are needed soon.


## API Reference

- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [BackgroundLoader](https://pixijs.download/release/docs/assets.BackgroundLoader.html.md)
