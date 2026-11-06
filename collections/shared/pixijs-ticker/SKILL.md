---
name: pixijs-ticker
description: "Use this skill when running per-frame logic or controlling the PixiJS v8 render loop. Covers Ticker.add/addOnce/remove, deltaTime vs deltaMS vs elapsedMS, UPDATE_PRIORITY ordering, maxFPS/minFPS capping, speed scaling, Ticker.shared vs new instances, per-object onRender hook, manual rendering. Triggers on (in PixiJS code): Ticker, UPDATE_PRIORITY, deltaTime, deltaMS, elapsedMS, onRender, app.ticker, maxFPS, minFPS, Ticker.shared."
license: MIT
---

`app.ticker` runs registered callbacks every frame and drives `app.render()` at `UPDATE_PRIORITY.LOW`.

**Related skills:** `pixijs-application` (Application setup, sharedTicker option), `pixijs-performance` (frame rate optimization). For v7 ticker signature changes see [v8 migration guide](https://pixijs.com/8.x/guides/migrations/v8).

## Core Patterns

### Time units

Ticker exposes three timing values:

| Property    | Type                          | Scaled by speed? | Capped by minFPS? | Use case                                     |
| ----------- | ----------------------------- | ---------------- | ----------------- | -------------------------------------------- |
| `deltaTime` | dimensionless (~1.0 at 60fps) | yes              | yes               | Frame-rate-independent multipliers           |
| `deltaMS`   | milliseconds                  | yes              | yes               | Time-based math (pixels/sec)                 |
| `elapsedMS` | milliseconds                  | no               | no                | Raw measurement, profiling                   |

```ts
import { Application } from "pixi.js";

const app = new Application();
await app.init({ width: 800, height: 600 });

app.ticker.add((ticker) => {
  // deltaTime: dimensionless scalar, ~1.0 at 60fps
  sprite.rotation += 0.1 * ticker.deltaTime;

  // deltaMS: real milliseconds (speed-scaled, capped)
  sprite.x += (200 / 1000) * ticker.deltaMS; // 200 pixels per second

  // elapsedMS: raw milliseconds (no scaling, no cap)
  console.log(`Raw frame time: ${ticker.elapsedMS}ms`);
});
```

**Tension note:** `deltaTime` is not milliseconds. It equals `deltaMS * Ticker.targetFPMS`, where targetFPMS is 0.06 (1/16.67). At exactly 60fps, deltaTime is 1.0. At 30fps, 2.0.

### Priority ordering and context binding

```ts
import { Application, UPDATE_PRIORITY } from "pixi.js";

const app = new Application();
await app.init({ width: 800, height: 600 });

// INTERACTION (50) > HIGH (25) > NORMAL (0) > LOW (-25) > UTILITY (-50)
// app.render() is registered at LOW by the TickerPlugin

app.ticker.add(
  (ticker) => {
    // Physics runs before normal-priority callbacks
    updatePhysics(ticker.deltaMS);
  },
  undefined,
  UPDATE_PRIORITY.HIGH,
);

app.ticker.add((ticker) => {
  // Default priority (NORMAL = 0), runs after HIGH but before render
  updateAnimations(ticker.deltaTime);
});

// Pass `this` as the second argument to preserve context on class methods
class GameSystem {
  public speed = 5;
  public position = 0;

  public update(ticker: Ticker): void {
    this.position += this.speed * ticker.deltaTime;
  }
}

const system = new GameSystem();
app.ticker.add(system.update, system);
app.ticker.remove(system.update, system); // must match both fn and context
```

### Frame rate capping

```ts
import { Ticker } from "pixi.js";

const ticker = new Ticker();

ticker.maxFPS = 30; // Cap at 30fps (skips frames to maintain interval)
ticker.minFPS = 10; // Cap deltaTime so it never exceeds 10fps worth

// If maxFPS < minFPS, minFPS is lowered to match
// If minFPS > maxFPS, maxFPS is raised to match
```

`minFPS` caps deltaTime/deltaMS so large frame drops don't produce huge deltas (default minFPS is 10).

### Per-object onRender hook

```ts
import { Sprite, Assets, Application } from "pixi.js";

const app = new Application();
await app.init({ width: 800, height: 600 });

const texture = await Assets.load("bunny.png");
const sprite = new Sprite(texture);
app.stage.addChild(sprite);

sprite.onRender = (renderer) => {
  sprite.rotation += 0.01;
};
```

`onRender` runs during scene graph traversal, before GPU rendering. Use instead of global ticker callback when logic is tied to one display object.

### Ticker.shared, Ticker.system, and new Ticker

```ts
import { Ticker, UPDATE_PRIORITY } from "pixi.js";

// Ticker.shared: singleton, autoStart=true, protected from destroy()
const shared = Ticker.shared;

// Ticker.system: separate instance used by engine background tasks,
// independent of the main scene ticker. It's a plain Ticker instance
// (autoStart=true, _protected=true) with no intrinsic priority; listeners
// are typically added at UTILITY priority by convention.
const system = Ticker.system;

// new Ticker(): custom instance, autoStart=false, you manage the lifecycle
const custom = new Ticker();
custom.autoStart = true; // start when first listener is added
custom.add((ticker) => {
  console.log(ticker.deltaMS);
});

// One-shot callback that auto-removes after firing
custom.addOnce(() => console.log("fires once"), null, UPDATE_PRIORITY.NORMAL);

// When done:
custom.stop();
custom.destroy();
```

`Application` creates own Ticker by default. Set `sharedTicker: true` in `app.init()` to use `Ticker.shared` instead. `Ticker.shared` and `Ticker.system` are both `_protected`: calling `destroy()` on them does not destroy them. Read `ticker.FPS` for measured frame rate, `ticker.count` for current listener count.

### App lifecycle and manual rendering

```ts
import { Application } from "pixi.js";

const app = new Application();
await app.init({ autoStart: false });

// Pause and resume the built-in render loop at any time.
app.start();
app.stop();

// Or drive the loop yourself (headless, visibility-gated, fixed timestep, etc.)
function animate() {
  app.ticker.update(); // fires callbacks, including TickerPlugin's registered render
  // Do not call app.render() again: the ticker already renders the stage.
  requestAnimationFrame(animate);
}
animate();
```

`TickerPlugin` adds `app.start()` and `app.stop()`, mapping to `ticker.start()` / `ticker.stop()`. Use `autoStart: false` plus own frame driver to pause on tab blur, run fixed-timestep loop, or render offscreen.

### Speed scaling

```ts
import { Application } from "pixi.js";

const app = new Application();
await app.init({ width: 800, height: 600 });

app.ticker.speed = 0.5; // Half speed (slow motion)
app.ticker.speed = 2.0; // Double speed

// speed affects deltaTime and deltaMS, but NOT elapsedMS
```

## Common Mistakes

### [CRITICAL] Ticker callback expects delta as first argument

Wrong:

```ts
app.ticker.add((dt) => {
  bunny.rotation += dt;
});
```

Correct:

```ts
app.ticker.add((ticker) => {
  bunny.rotation += ticker.deltaTime;
});
```

v8 passes Ticker instance as callback argument, not delta number. v7 pattern `(dt) => ...` compiles, but `dt` is whole Ticker object. Arithmetic on it produces `NaN`.


### [HIGH] Using updateTransform for per-frame logic

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
    this.onRender = this._onRender.bind(this);
  }
  private _onRender() {
    this.rotation += 0.01;
  }
}
```

`updateTransform` removed in v8. Use `onRender` callback for per-object per-frame logic.


### [MEDIUM] Treating deltaTime as milliseconds

Wrong:

```ts
app.ticker.add((ticker) => {
  // Tries to move 100px/sec but deltaTime is ~1.0, not ~16.67
  sprite.x += (100 * ticker.deltaTime) / 1000;
});
```

Correct:

```ts
app.ticker.add((ticker) => {
  // Using deltaMS for time-based movement
  sprite.x += (100 / 1000) * ticker.deltaMS;
  // Or using deltaTime as a frame-rate multiplier
  sprite.x += 1.5 * ticker.deltaTime;
});
```

Use `deltaMS` for real-time calculations. Use `deltaTime` as simple multiplier when you want "per frame at 60fps" behavior.


## API Reference

- [Ticker](https://pixijs.download/release/docs/ticker.Ticker.html.md)
- [TickerPlugin](https://pixijs.download/release/docs/app.TickerPlugin.html.md)
- [TickerPluginOptions](https://pixijs.download/release/docs/app.TickerPluginOptions.html.md)
