# Render Loop

## Frame lifecycle

Each frame, `Ticker` measures elapsed time, clamps it with `minFPS`/`maxFPS`, then calls every `ticker.add()` listener in priority order. `app.render()` is one such listener, at `UPDATE_PRIORITY.LOW`. It walks display list from `app.stage` and recalculates world transforms (position/rotation/scale propagated parent-to-child). Then it fires each object's `onRender` hook, culls off-screen objects if culling enabled, batches draw calls and issues GPU commands.

```
requestAnimationFrame
        │
    [Ticker._tick()]
        │
    ├─ Compute elapsed time (minFPS/maxFPS clamp)
    └─ Call listeners in priority order
        ├─ INTERACTION / HIGH / NORMAL listeners
        ├─ LOW: app.render()
        │   ├─ Traverse display list
        │   ├─ Update world transforms
        │   │   └─ object.onRender() (per-object during traversal)
        │   ├─ Cull display objects (if enabled)
        │   ├─ Upload data to GPU
        │   └─ Draw
        └─ UTILITY listeners (post-render)
```

Rendering is **retained mode**: objects persist across frames unless explicitly removed.

## Core Patterns

### Priority order

Ticker runs callbacks in descending priority. `TickerPlugin` registers `app.render()` at `UPDATE_PRIORITY.LOW`, so `NORMAL`, `HIGH` and `INTERACTION` callbacks run before render.

```
UPDATE_PRIORITY.INTERACTION = 50   // pointer events
UPDATE_PRIORITY.HIGH        = 25   // physics, input sampling
UPDATE_PRIORITY.NORMAL      =  0   // gameplay (default)
UPDATE_PRIORITY.LOW         = -25  // app.render() registered here
UPDATE_PRIORITY.UTILITY     = -50  // post-render cleanup
```

```ts
import { UPDATE_PRIORITY } from "pixi.js";

app.ticker.add(
  (ticker) => {
    handleInput(ticker.deltaMS);
  },
  undefined,
  UPDATE_PRIORITY.HIGH,
);

app.ticker.add((ticker) => {
  updateAnimations(ticker.deltaTime);
});
```

### Time units

| Property    | Type                          | Scaled by speed? | Capped by minFPS? |
| ----------- | ----------------------------- | ---------------- | ----------------- |
| `deltaTime` | dimensionless (~1.0 at 60fps) | yes              | yes               |
| `deltaMS`   | milliseconds                  | yes              | yes               |
| `elapsedMS` | milliseconds                  | no               | no                |

`deltaTime`: frame-rate multiplier for simple per-frame logic. `deltaMS`: pixels-per-second or other time-based math. `elapsedMS`: only for profiling (raw, uncapped, unscaled).

### Manual rendering

```ts
await app.init({ autoStart: false, width: 800, height: 600 });

function frame(time: number) {
  updateGameState();
  app.renderer.render(app.stage);
  requestAnimationFrame(frame);
}

requestAnimationFrame(frame);
```

`autoStart: false` disables `TickerPlugin`'s automatic render registration. You decide when scene draws: custom loop, external animation library or fixed-timestep game clock.

### Stop and start

```ts
app.stop(); // pause the ticker and rendering
app.start(); // resume
```

Use for pause menus or when user leaves tab. Ticker auto-pauses on page blur when `sharedTicker: false` (default).

### Per-object update via `onRender`

```ts
const sprite = new Sprite(texture);
sprite.onRender = () => {
  sprite.rotation += 0.01;
};

app.stage.addChild(sprite);
```

`onRender` runs during scene graph traversal, right before object draws. Per-object alternative to global ticker callback when logic belongs to one display object.

### Frame rate capping

```ts
app.ticker.maxFPS = 30; // run at 30fps
app.ticker.minFPS = 10; // cap deltaTime at 10fps worth if frames drop
```

`maxFPS` sets ceiling by skipping updates. `minFPS` caps `deltaTime` so big frame drops do not yield huge deltas that break physics. Defaults: no `maxFPS`, `minFPS: 10`.

## Common Mistakes

### [CRITICAL] Treating the ticker callback arg as a number

Wrong:

```ts
app.ticker.add((dt) => {
  sprite.rotation += dt; // dt is the Ticker instance, not a number
});
```

Correct:

```ts
app.ticker.add((ticker) => {
  sprite.rotation += ticker.deltaTime;
});
```

v8 passes `Ticker` instance, not a delta. Old v7 code like `(dt) => sprite.x += dt` compiles but produces `NaN` because `dt` is an object.

### [HIGH] Using `updateTransform` for per-frame logic

Wrong:

```ts
class MySprite extends Sprite {
  updateTransform() {
    super.updateTransform();
    this.rotation += 0.01;
  }
}
```

Correct:

```ts
class MySprite extends Sprite {
  constructor() {
    super();
    this.onRender = () => {
      this.rotation += 0.01;
    };
  }
}
```

`updateTransform` removed in v8. Use `onRender` for per-object per-frame logic.

### [MEDIUM] Assuming ticker callbacks run after render

Wrong:

```ts
app.ticker.add(() => {
  readPixelsFromCanvas(); // empty; render hasn't happened yet this frame
});
```

Correct:

```ts
app.ticker.add(
  () => {
    readPixelsFromCanvas();
  },
  undefined,
  UPDATE_PRIORITY.UTILITY,
);
```

Default-priority callbacks (`NORMAL = 0`) run _before_ render (at `LOW = -25`). Use `UTILITY = -50` for post-render work like pixel readbacks or DOM sync.

## API Reference

- [Ticker](https://pixijs.download/release/docs/ticker.Ticker.html.md)
- [TickerPlugin](https://pixijs.download/release/docs/app.TickerPlugin.html.md)
- [UPDATE_PRIORITY](https://pixijs.download/release/docs/ticker.UPDATE_PRIORITY.html.md)
- [Application](https://pixijs.download/release/docs/app.Application.html.md)
