---
name: pixijs-events
description: "Use this skill when handling pointer, mouse, touch, or wheel input in PixiJS v8. Covers eventMode (none, passive, auto, static, dynamic), FederatedEvent types, propagation and capture phase, hitArea, interactiveChildren, cursor and cursorStyles, global move events for drag, eventFeatures config. Triggers on (in PixiJS code): eventMode, FederatedPointerEvent, pointerdown, click or tap on display objects, globalpointermove, dragging display objects, hitArea, cursorStyles, stopPropagation, persistentDeviceId, contextmenu, rightclick."
license: MIT
---

Federated event system mirrors DOM events on scene graph. Opt object in with `container.eventMode = 'static'`, then listen with `.on()`, `addEventListener()` or `onEventName` property handlers. Move events fire only over listening object; use `globalpointermove` for drag.

## Quick Start

```ts
const button = new Sprite(await Assets.load("button.png"));
button.eventMode = "static";
button.cursor = "pointer";
app.stage.addChild(button);

button.on("pointertap", (event) => {
  console.log("clicked at", event.global.x, event.global.y);
});

let dragging = false;
button.on("pointerdown", () => {
  dragging = true;
});
button.on("pointerup", () => {
  dragging = false;
});
button.on("pointerupoutside", () => {
  dragging = false;
});
button.on("globalpointermove", (event) => {
  if (dragging) button.parent.toLocal(event.global, undefined, button.position);
});
```

**Related skills:** `pixijs-performance` (event-heavy scenes). These skills do not cover screen reader and keyboard support (`import 'pixi.js/accessibility'`) or HTML overlays (`DOMContainer`). See [accessibility guide](https://pixijs.com/8.x/guides/components/accessibility) and [DOMContainer API](https://pixijs.download/release/docs/scene.DOMContainer.html.md).

## Core Patterns

### eventMode values

```ts
import { Sprite } from "pixi.js";

const sprite = new Sprite();

// No interaction at all; children also ignored
sprite.eventMode = "none";

// Default. Self not interactive; interactive children still work
sprite.eventMode = "passive";

// Hit tested only when a parent is interactive
sprite.eventMode = "auto";

// Standard interaction: receives pointer/mouse/touch events
sprite.eventMode = "static";

// Like static, but also fires synthetic events from the ticker
// when the pointer is stationary (for animated objects under cursor)
sprite.eventMode = "dynamic";
```

Use `'static'` for buttons, UI elements, drag targets. Use `'dynamic'` only for objects that move under stationary cursor and need continuous hover updates.

Check whether object can receive events with `isInteractive()`:

```ts
sprite.eventMode = "static";
sprite.isInteractive(); // true

sprite.eventMode = "passive";
sprite.isInteractive(); // false
```

### Event types

Pointer events (recommended for cross-device compatibility): `pointerdown`, `pointerup`, `pointerupoutside`, `pointermove`, `pointerover`, `pointerout`, `pointerenter`, `pointerleave`, `pointertap`, `pointercancel`.

Mouse events: `mousedown`, `mouseup`, `mouseupoutside`, `mousemove`, `mouseover`, `mouseout`, `mouseenter`, `mouseleave`, `click`, `rightdown`, `rightup`, `rightupoutside`, `rightclick`, `contextmenu`, `wheel`. PixiJS doesn't block browser context menu. Call `event.preventDefault()` in `contextmenu` listener to keep it closed. Canceling `rightdown`, `rightup` or `rightclick` doesn't keep it closed. On macOS, ctrl + click also fires `contextmenu`; browser can report it as left click.

Touch events: `touchstart`, `touchend`, `touchendoutside`, `touchmove`, `touchcancel`, `tap`. Each touch carries `altKey`, `ctrlKey`, `metaKey`, `shiftKey` copied from native `TouchEvent`, so modifier keys work as with mouse or pointer events.

Global move events: `globalpointermove`, `globalmousemove`, `globaltouchmove`. Fire on every pointer move, even when pointer is not over listening object.

Container lifecycle events (no `eventMode` required): `added`, `removed`, `destroyed`, `childAdded`, `childRemoved`, `visibleChanged`.

### Listening styles

```ts
import { Sprite } from "pixi.js";

const sprite = new Sprite();
sprite.eventMode = "static";

// EventEmitter style (recommended)
const handler = (e) => console.log("clicked");
sprite.on("pointerdown", handler);
sprite.once("pointerdown", handler); // one-time
sprite.off("pointerdown", handler);

// DOM style
sprite.addEventListener(
  "click",
  (event) => {
    console.log("Clicked!", event.detail);
  },
  { once: true },
);

// Property-based handlers
sprite.onclick = (event) => {
  console.log("Clicked!", event.detail);
};
```

### Pointer events and propagation

```ts
import { Sprite, Container } from "pixi.js";

const parent = new Container();
parent.eventMode = "static";

const child = new Sprite();
child.eventMode = "static";
parent.addChild(child);

child.on("pointerdown", (event) => {
  console.log("child pressed");
  event.stopPropagation(); // prevent parent from receiving this event
});

parent.on("pointerdown", () => {
  console.log("parent pressed (only if child did not stop propagation)");
});
```

### Capture phase events

All events support capture phase: append `capture` to event name (e.g., `pointerdowncapture`, `clickcapture`). Capture listeners fire before event reaches its target.

```ts
container.addEventListener(
  "pointerdown",
  (event) => {
    event.stopImmediatePropagation(); // blocks event from reaching children
  },
  { capture: true },
);
```

### Hit testing

On pointer event, PixiJS walks display tree to find top-most interactive element under pointer. Traversal rules:

- `eventMode = 'none'` on container skips that element and its entire subtree.
- `interactiveChildren = false` on container skips its children (container itself can still be tested).
- `hitArea` overrides bounds-based testing; only the shape is checked.
- Objects not visible, not renderable or not measurable are skipped.

Custom `hitArea` also speeds hit tests on large or complex objects (less geometry to check):

```ts
import { Sprite, Rectangle, Circle, Polygon } from "pixi.js";

const sprite = new Sprite();
sprite.eventMode = "static";

// Rectangular hit area
sprite.hitArea = new Rectangle(0, 0, 100, 50);

// Circular hit area
sprite.hitArea = new Circle(50, 50, 40);

// Polygon hit area
sprite.hitArea = new Polygon([0, 0, 100, 0, 50, 100]);

// Custom hit test via contains()
sprite.hitArea = {
  contains(x: number, y: number): boolean {
    return x >= 0 && x <= 100 && y >= 0 && y <= 100;
  },
};
```

### Cursor styles

Set `cursor` per object. For reusable cursors, register named styles on event system:

```ts
app.renderer.events.cursorStyles.default = "url('bunny.png'), auto";
app.renderer.events.cursorStyles.hover = "url('bunny_saturated.png'), auto";

sprite.eventMode = "static";
sprite.cursor = "hover"; // uses the registered 'hover' style
```

Cursor styles can be strings (CSS cursor values), objects (applied as CSS styles) or functions (called with mode string).

### Event properties

Useful `FederatedPointerEvent` fields:

```ts
sprite.on("pointerdown", (event: FederatedPointerEvent) => {
  event.global; // scene-space Point where the event happened
  event.client; // CSS-pixel Point relative to the viewport
  event.offset; // Point w.r.t. target Container in world space (not supported at the moment)
  event.target; // the Container that received the event
  event.currentTarget; // the Container whose listener is running

  event.pointerType; // 'mouse' | 'pen' | 'touch'
  event.pointerId; // unique id for multi-touch tracking
  event.isPrimary; // first pointer in a multi-pointer gesture
  event.persistentDeviceId; // always 0; present for DOM PointerEvent type compatibility
  event.pressure; // 0-1 pen/touch pressure
  event.button; // 0 left, 1 middle, 2 right
  event.buttons; // bitmask of held buttons
  event.altKey; // modifier key state
  event.ctrlKey;
  event.shiftKey;
  event.metaKey;

  event.nativeEvent; // the underlying DOM PointerEvent / MouseEvent / Touch
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation();
});
```

`FederatedWheelEvent` adds `deltaX`, `deltaY`, `deltaZ`, `deltaMode`. Wheel events fire on same hit-tested object as pointer events.

### Event features

Toggle event categories globally for performance:

```ts
await app.init({
  eventFeatures: {
    move: true, // pointer/mouse/touch move events
    globalMove: true, // global move events (globalpointermove, etc.)
    click: true, // click/tap/press and contextmenu events
    wheel: true, // mouse wheel events
  },
});

// or configure after init
app.renderer.events.features.globalMove = false;
```

### Performance tips

- `eventMode = 'none'` on non-interactive subtrees to skip hit testing entirely.
- `interactiveChildren = false` on containers where only container itself needs interaction.
- Disable unused event features via `eventFeatures` (e.g., `globalMove: false`) to cut per-frame work.

## Common Mistakes

### [HIGH] Default eventMode is passive

Wrong:

```ts
const sprite = new Sprite(texture);
sprite.on("pointerdown", () => {
  console.log("clicked");
});
```

Correct:

```ts
const sprite = new Sprite(texture);
sprite.eventMode = "static";
sprite.on("pointerdown", () => {
  console.log("clicked");
});
```

Default `eventMode` is `'passive'`: object itself receives no events. Must explicitly set `eventMode` to `'static'` or `'dynamic'` before any listener fires.


### [HIGH] buttonMode removed; use cursor

Wrong:

```ts
sprite.interactive = true;
sprite.buttonMode = true;
```

Correct:

```ts
sprite.eventMode = "static";
sprite.cursor = "pointer";
```

`buttonMode` removed in v8. Use `cursor = 'pointer'` for hand cursor on hover. `interactive = true` still works as alias for `eventMode = 'static'`, but prefer `eventMode`.


### [HIGH] Move events only fire over the object in v8

Wrong:

```ts
sprite.eventMode = "static";
sprite.on("pointermove", (event) => {
  // expects to fire everywhere; only fires inside sprite bounds
  updateDrag(event.global.x, event.global.y);
});
```

Correct:

```ts
sprite.eventMode = "static";
sprite.on("globalpointermove", (event) => {
  // fires everywhere, even outside sprite bounds
  updateDrag(event.global.x, event.global.y);
});
```

In v8, `pointermove`, `mousemove`, `touchmove` only fire when pointer is over display object. In v7 they fired on any canvas move. For drag or global tracking, use `globalpointermove`, `globalmousemove` or `globaltouchmove`.


### [MEDIUM] Cursor does not inherit from parent

`cursor` on parent container has no effect on its children. Only direct hit target's `cursor` value applies.

```ts
// This does NOT make children show a pointer cursor
parent.cursor = "pointer";

// Each interactive child needs its own cursor
child.eventMode = "static";
child.cursor = "pointer";
```

For uniform cursor on all children, set `cursor` on each interactive child individually, or set `hitArea` on parent and make children non-interactive.


## API Reference

- [EventSystem](https://pixijs.download/release/docs/events.EventSystem.html.md)
- [FederatedEvent](https://pixijs.download/release/docs/events.FederatedEvent.html.md)
- [FederatedPointerEvent](https://pixijs.download/release/docs/events.FederatedPointerEvent.html.md)
- [FederatedMouseEvent](https://pixijs.download/release/docs/events.FederatedMouseEvent.html.md)
- [FederatedWheelEvent](https://pixijs.download/release/docs/events.FederatedWheelEvent.html.md)
- [EventBoundary](https://pixijs.download/release/docs/events.EventBoundary.html.md)
