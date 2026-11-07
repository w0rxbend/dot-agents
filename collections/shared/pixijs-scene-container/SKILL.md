---
name: pixijs-scene-container
description: "Use this skill when grouping, positioning, or transforming display objects in PixiJS v8. Covers Container constructor options (isRenderGroup, sortableChildren, boundsArea), addChild/removeChild/addChildAt/swapChildren/setChildIndex, position/scale/rotation/pivot/skew/alpha/tint, getBounds/getGlobalPosition/toLocal/toGlobal, zIndex sorting, cullable, onRender per-frame callback, destroy. Triggers on (in PixiJS code): Container, addChild, removeChild, addChildAt, swapChildren, sortableChildren, zIndex, container position/scale/rotation/pivot, getBounds, toGlobal, toLocal, onRender, container.destroy, ContainerOptions, RenderLayer, render groups, masks."
license: MIT
---

`Container`: general-purpose PixiJS v8 scene-graph node. Holds children; applies transforms, alpha, tint, blend mode to whole subtree. Every display object is a `Container` (branch) or a leaf (`Sprite`, `Graphics`, `Text`, `Mesh`) nested in one.

Assumes scene graph basics in [references/scene-core-concepts.md](references/scene-core-concepts.md) (leaves vs containers, constructor options, render groups, RenderLayer, masking, culling).

## Quick Start

```ts
const group = new Container({
  label: "hero-group",
  x: 200,
  y: 150,
  sortableChildren: true,
});

const body = new Sprite(await Assets.load("body.png"));
const head = new Sprite(await Assets.load("head.png"));
head.position.set(0, -40);
head.zIndex = 1;

group.addChild(body, head);
group.pivot.set(group.width / 2, group.height / 2);
group.scale.set(1.5);

app.stage.addChild(group);
```

**Related skills:** `pixijs-scene-graphics` / `pixijs-scene-text` (leaves inside containers), `pixijs-events` (`eventMode`, hit testing), `pixijs-performance` (`cacheAsTexture`, culling, render groups).

## Core Patterns

### Constructor options

```ts
const container = new Container({
  label: "world",
  x: 100,
  y: 50,
  scale: 2,
  rotation: Math.PI / 4,
  alpha: 0.8,
  visible: true,
  tint: 0xffaa00,
  blendMode: "add",
  sortableChildren: true,
  isRenderGroup: true,
  origin: { x: 0, y: 0 },
  boundsArea: new Rectangle(0, 0, 1920, 1080),
});
```

Constructor bulk-copies every options field onto instance via `assignWithIgnore`, except `children`, `parent`, `effects`. So any public `Container` property works: `cullable`, `cullArea`, `mask`, `filterArea`, `eventMode`, `hitArea`, etc. Full list: constructor-options table in [references/scene-core-concepts.md](references/scene-core-concepts.md).

`isRenderGroup: true` makes container own render group: transforms apply on GPU, not recomputed per-child on CPU. Use on stable sub-trees (large static worlds, UI layers). Do not overuse; most scenes need no explicit render groups, too many hurt performance. Profile first. See [references/scene-core-concepts.md](references/scene-core-concepts.md#render-groups).

`origin` (v8 `ObservablePoint`) sets rotation/scale center **without** moving container. `pivot` shifts projection of local origin in parent space, so changing it displaces object; `origin` leaves position alone. Accepts `PointData` or single number (both axes); set live via `container.origin.set(x, y)`.

`boundsArea` makes `getBounds()` return fixed rectangle instead of recursively measuring children. Performance win for containers with hundreds of cheap, predictable children.

### Leaves vs containers

Only `Container` (and child-holding subclasses like `RenderLayer`) should have children. `Sprite`, `Graphics`, `Text`, `Mesh`, `ParticleContainer` particles, `DOMContainer` content are leaves by convention in PixiJS v8. To group, wrap in a `Container`: container owns layout logic, leaves stay pure visual data.

### Adding and removing children

```ts
const parent = new Container();

parent.addChild(a, b, c);
parent.addChildAt(d, 0);
parent.swapChildren(a, b);
parent.setChildIndex(c, 0);

parent.removeChild(b);
parent.removeChildAt(0);
parent.removeChildren();

parent.removeChildren(0, 2);
```

`addChild` takes any number of children, returns first. Children render in array order: index 0 first (behind), last index last (in front). `addChildAt` inserts at index; `setChildIndex` moves existing child; `swapChildren` swaps two children.

`removeChildren(beginIndex?, endIndex?)` removes slice, returns removed array.

`addChildAt` on child already in this container silently moves it to new index. No `added` / `childAdded` / `removed` / `childRemoved` events fire (parent unchanged). Events fire only when child comes from different parent (or none).

Reparent keeping world transform (no visual jump): `reparentChild` / `reparentChildAt`. Swap child in place, copying old child's local transform: `replaceChild`.

### Transform properties

```ts
const obj = new Container();

obj.x = 100;
obj.y = 200;
obj.position.set(100, 200);

obj.scale.set(2);
obj.scale = 2;

obj.rotation = Math.PI / 4;
obj.angle = 45;

obj.pivot.set(50, 50);
obj.skew.set(0.1, 0.2);

obj.alpha = 0.5;
obj.tint = 0xff0000;
obj.visible = false;
obj.renderable = false;
```

- `position`, `scale`, `pivot`, `skew` are `ObservablePoint`s. `scale = 2` valid; sets both axes.
- `rotation` (radians) and `angle` (degrees) are synced aliases.
- `pivot`: local point mapped to `position` in parent space. Changing it both moves and rotates container.
- `alpha` and `tint` multiply down through children. `blendMode` applies to this container's draw instructions.
- `visible = false` skips rendering and transform updates. `renderable = false` skips rendering but still updates transforms (for `getBounds()` or hit-testing without drawing).

### zIndex and sortableChildren

```ts
const world = new Container({ sortableChildren: true });

const ground = new Sprite(groundTexture);
ground.zIndex = 0;

const player = new Sprite(playerTexture);
player.zIndex = 10;

const ui = new Sprite(uiTexture);
ui.zIndex = 100;

world.addChild(ground, player, ui);
```

With `sortableChildren` `true`, container re-sorts children by `zIndex` before next render; changing any child's `zIndex` automatically marks parent as needing sort. Sort only what needs it; `sortableChildren` off is cheaper. Full manual control: call `container.sortChildren()` after changing `zIndex` values.

To render at different z while keeping logical parent for transforms, use `RenderLayer`. See [references/scene-core-concepts.md](references/scene-core-concepts.md#renderlayer-render-order-independent-of-the-hierarchy).

### Bounds and coordinate conversion

```ts
const bounds = container.getBounds();
console.log(bounds.x, bounds.y, bounds.width, bounds.height);

const rect = container.getBounds().rectangle;

const local = new Point(10, 20);
const world = container.toGlobal(local);
const backToLocal = container.toLocal(world);

const selfPos = container.getGlobalPosition();
```

Signature `getBounds(skipUpdate?: boolean, bounds?: Bounds)`: first arg `true` skips forced transform update; optional second-arg `Bounds` is reused instead of allocating.

`toGlobal(point)` converts point from this container's local space to scene-root space. `toLocal(point, from?)` converts from another container's local space (global if `from` omitted). `getGlobalPosition()`: shorthand for `parent.toGlobal(this._position)`.

### Sizing

```ts
const sprite = new Sprite(texture);

sprite.setSize(200, 100);
const { width, height } = sprite.getSize();
```

`setSize` adjusts `scale` in one operation so bounds fit requested pixel size. Separate `.width` and `.height` assignments work but each recomputes bounds; prefer `setSize` for both axes.

### Container events

```ts
const parent = new Container();

parent.on("childAdded", (child, container, index) => {
  console.log("added at", index, child.label);
});

parent.on("childRemoved", (child, container, index) => {
  console.log("removed from", index);
});

const child = new Container();
child.on("added", (newParent) => console.log("entered", newParent.label));
child.on("removed", (oldParent) => console.log("left", oldParent.label));
child.on("visibleChanged", (visible) => console.log("visible:", visible));
child.on("destroyed", (destroyed) => console.log("gone", destroyed.label));

parent.addChild(child);
```

| Event            | Fires on                          | Arguments                   |
| ---------------- | --------------------------------- | --------------------------- |
| `childAdded`     | parent receiving child            | `(child, container, index)` |
| `childRemoved`   | parent losing child               | `(child, container, index)` |
| `added`          | attached child                    | `(parent)`                  |
| `removed`        | detached child                    | `(parent)`                  |
| `destroyed`      | destroyed container               | `(container)`               |
| `visibleChanged` | container whose `visible` flipped | `(visible)`                 |

These are `Container`'s `EventEmitter` events, not pointer events from `pixijs-events`.

`destroyed` fires after internal cleanup, before listener removal. In handler, `position`, `scale`, `pivot`, `origin`, `skew`, `parent` already nulled; `children` emptied (length 0, array reference not nulled). Capture needed data _before_ `destroy()`, not in handler.

### Per-frame updates with onRender

```ts
const container = new Container();

container.onRender = (renderer) => {
  container.rotation += 0.01;
};

container.onRender = null;
```

`onRender` runs every frame while container renders; receives active `Renderer`. Use for lightweight per-container animation or updates. v7 overrode `updateTransform` instead; v8 no longer calls `updateTransform` every frame. `onRender = null` detaches.

### Finding and removing from parent

```ts
const player = world.getChildByLabel("player");
const enemies = world.getChildrenByLabel(/enemy-\d+/, true);

const bounds = hud.getLocalBounds();

oldSprite.removeFromParent();
```

- `getChildByLabel(label, deep?)` — first match by string or `RegExp`. Pass `true` for recursive search.
- `getChildrenByLabel(label, deep?, out?)` — all matches. Accepts optional reusable output array.
- `getLocalBounds()` — bounds in container's own coordinate space, ignoring parent transforms. Cheaper than `getBounds()` for self-contained layout math.
- `removeFromParent()` — detaches `this` from current parent (no-op if already orphaned).

### Destroy

```ts
container.destroy();

container.destroy({
  children: true,
  texture: true,
  textureSource: true,
});

console.log(container.destroyed);
```

Default `destroy()` unlinks from parent and tears down own state. `{ children: true }` recursively destroys every descendant (usual call for whole subtree). `texture: true` and `textureSource: true` also destroy GPU resources of leaf children (for textures loaded only for them).

## Common Mistakes

### [CRITICAL] Adding children to leaf scene objects

Wrong:

```ts
const sprite = new Sprite(texture);
const overlay = new Sprite(overlayTexture);
sprite.addChild(overlay);
```

Correct:

```ts
const group = new Container();
const sprite = new Sprite(texture);
const overlay = new Sprite(overlayTexture);
group.addChild(sprite, overlay);
```

Sprites, Graphics, Text, Mesh are leaves. Adding children to them logs deprecation warning now; will be error in future version. Always group them in a `Container`.

### [HIGH] Expecting getBounds() to return a Rectangle

Wrong:

```ts
const rect = container.getBounds();
rect.contains(x, y); // TypeError: contains is not a function
```

Correct:

```ts
const rect = container.getBounds().rectangle;
rect.contains(x, y);

const bounds = container.getBounds();
console.log(bounds.width, bounds.height);
```

v8 `getBounds()` returns `Bounds`. Basic getters (`x`, `y`, `width`, `height`) work; for `Rectangle`-specific methods like `.contains()` or APIs requiring a `Rectangle`, read `.rectangle`.

### [HIGH] Using cacheAsBitmap instead of cacheAsTexture

Wrong:

```ts
container.cacheAsBitmap = true;
```

Correct:

```ts
container.cacheAsTexture(true);
```

v8 renamed `cacheAsBitmap` (v7 property) to `cacheAsTexture()` (method). Always disable with `cacheAsTexture(false)` before calling `destroy()`.

### [MEDIUM] Using container.name instead of container.label

v8 renamed `name` to `label`; `name` still works as deprecated alias. Look up children by name with `getChildByLabel`.

### [MEDIUM] Setting both pivot and origin on the same container

Pivot shifts projection of local origin in parent space (changing rotation center moves object as side-effect). Origin changes rotation/scale center without displacement. Both on one container compound unexpectedly; pick one.

## API Reference

- [Container](https://pixijs.download/release/docs/scene.Container.html.md)
- [ContainerOptions](https://pixijs.download/release/docs/scene.ContainerOptions.html.md)
- [ViewContainer](https://pixijs.download/release/docs/scene.ViewContainer.html.md)
- [Bounds](https://pixijs.download/release/docs/rendering.Bounds.html.md)
- [Point](https://pixijs.download/release/docs/maths.Point.html.md)
- [ObservablePoint](https://pixijs.download/release/docs/maths.ObservablePoint.html.md)
- [RenderGroup](https://pixijs.download/release/docs/rendering.RenderGroup.html.md)
