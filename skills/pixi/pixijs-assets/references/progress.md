# Progress Tracking

`Assets.load` and `Assets.loadBundle` take progress callback, fired as each asset completes. Drives loading bars, percentage readouts, spinner state during long loads. Value normalized `[0, 1]` across whole call.

## Quick Start

```ts
const loadingBar = new Graphics();
app.stage.addChild(loadingBar);

await Assets.load(["hero.png", "enemy.png", "map.json"], (progress) => {
  loadingBar.clear();
  loadingBar.rect(0, 0, progress * 400, 20).fill(0x66ccff);
});
```

## Core Patterns

### Progress on a single asset

```ts
await Assets.load("large-atlas.json", (progress) => {
  console.log(`${Math.round(progress * 100)}%`);
});
```

Fires even for one asset (typically once, reaching `1.0`). Single-call progress is rarely useful; prefer bundles or arrays.

### Progress on an array

```ts
const assets = await Assets.load(
  ["hero.png", "enemy.png", "map.json", "music.mp3"],
  (progress) => updateBar(progress),
);
```

Progress splits evenly across N assets. Third of four assets done: progress is `0.75`.

### Progress on a bundle

```ts
await Assets.loadBundle("level1", (progress) => {
  loadingText.text = `Loading… ${Math.round(progress * 100)}%`;
});
```

Each bundle asset counts equally: 10 entries contribute `0.1` each.

### Progress via `LoadOptions.onProgress`

```ts
await Assets.load("game.json", {
  onProgress: (progress) => updateBar(progress),
  onError: (err, asset) => {
    const src = typeof asset === "string" ? asset : asset.src;
    console.warn("failed:", src, err);
  },
});
```

Pass `LoadOptions` object instead of callback as second argument. Preferred when you also need error handling or retry strategies. `onError` receives `string | ResolvedAsset`; guard before accessing `.src`.

### Global progress across multiple loads

```ts
async function loadAllWithTotal(tasks: Array<() => Promise<any>>) {
  let done = 0;
  for (const task of tasks) {
    await task();
    done++;
    updateBar(done / tasks.length);
  }
}

await loadAllWithTotal([
  () => Assets.load("menu.json"),
  () => Assets.loadBundle("level1"),
  () => Assets.loadBundle("sounds"),
]);
```

Callbacks are scoped per call. For one bar over several sequential loads, wrap calls and count completions yourself.

## Common Mistakes

### [HIGH] Treating progress callback as completion

Wrong:

```ts
Assets.load("hero.png", (progress) => {
  if (progress === 1) {
    showHero();
  }
});
```

Correct:

```ts
await Assets.load("hero.png", (progress) => updateBar(progress));
showHero();
```

`progress === 1` may fire slightly before returned promise resolves. Always use `await` or `.then()` to know loading truly finished. Callback is for UI updates only.


### [MEDIUM] Progress not updating smoothly

Each asset is one discrete step: three assets jump `0 -> 0.33 -> 0.66 -> 1.0`. For smoother bar, split large bundles into smaller ones, or animate bar width toward target value:

```ts
let target = 0;
await Assets.loadBundle("game", (p) => {
  target = p;
});

app.ticker.add(() => {
  loadingBar.width += (target * maxWidth - loadingBar.width) * 0.1;
});
```


### [MEDIUM] Progress via background loading

Wrong:

```ts
Assets.backgroundLoadBundle("game", (p) => updateBar(p));
```

Background loading has no progress callback. For visible progress, use foreground `Assets.loadBundle`. See `references/background.md`.


## API Reference

- [Assets](https://pixijs.download/release/docs/assets.Assets.html.md)
- [LoadOptions](https://pixijs.download/release/docs/assets.LoadOptions.html.md)
- [ProgressCallback](https://pixijs.download/release/docs/assets.ProgressCallback.html.md)
