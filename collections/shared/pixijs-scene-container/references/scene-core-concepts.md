# PixiJS v8 scene core concepts

Shared background for the `pixijs-scene-container`, `pixijs-scene-graphics` and `pixijs-scene-text` skills. Upstream PixiJS splits this into a separate `pixijs-scene-core-concepts` skill. This repo does not vendor that skill, so the essentials are collected here. Checked against the `pixi.js` 8.22 type definitions.

## Scene graph mental model

- The scene is a tree. `app.stage` is the root `Container`. Everything you draw is a node under it.
- **Containers** group nodes and hold children. **Leaves** (`Sprite`, `Graphics`, `Text`, `BitmapText`, `HTMLText`, `Mesh`, `TilingSprite`, `NineSliceSprite`) draw something and should not have children. Adding a child to a leaf logs a deprecation warning. To group leaves, wrap them in a `Container`.
- Transforms (`position`, `scale`, `rotation`, `pivot`, `skew`), `alpha`, `tint` and `visible` are inherited. A child's world transform is its parent's world transform multiplied by its own local transform.
- Render order is depth-first in children-array order: index 0 is drawn first (at the back). Use `zIndex` with `sortableChildren: true` to reorder within one parent, and `RenderLayer` to reorder across parents (see below).
- Removing a node from its parent does not free it. Call `destroy()` (with `{ children: true }` for subtrees) when you are done with it.

## Constructor options shared by all scene objects

Every display object constructor accepts the `Container` options alongside its own options. Any public `Container` property can be passed. The common ones are:

| Group | Options |
| --- | --- |
| Identity | `label` |
| Transform | `x`, `y`, `position`, `scale` (number or point), `rotation` (radians), `angle` (degrees), `pivot`, `origin`, `skew`, `width`, `height` |
| Appearance | `alpha`, `tint`, `blendMode`, `visible`, `renderable` |
| Ordering | `zIndex`, `sortableChildren` |
| Effects | `filters`, `filterArea`, `mask` |
| Rendering | `isRenderGroup`, `boundsArea` |
| Culling | `cullable`, `cullableChildren`, `cullArea` |
| Interaction | `eventMode`, `cursor`, `hitArea`, `interactiveChildren`, plus `on*` handler properties such as `onpointerdown` |
| Per-frame | `onRender` |

`children`, `parent` and `effects` are ignored by the bulk copy. Add children with `addChild` after construction.

```ts
const sprite = new Sprite({
  texture,
  label: "player",
  position: { x: 100, y: 200 },
  anchor: 0.5,
  scale: 2,
  zIndex: 10,
  eventMode: "static",
  cursor: "pointer",
});
```

## Render groups

A render group is a sub-tree whose transforms are applied on the GPU, so moving the group does not recompute every child's transform on the CPU. `app.stage` is always a render group.

```ts
const world = new Container({ isRenderGroup: true });
// or, on an existing container:
hud.enableRenderGroup();
```

Use them for large, mostly static sub-trees that move as a whole: a scrolling world, or a UI layer above it. Most scenes need none beyond the stage. Each extra group has its own overhead, so profile before adding more.

## RenderLayer: render order independent of the hierarchy

A `RenderLayer` draws objects at its own position in the render order, while each object keeps its real parent for transforms. A typical use is a character's name tag that must draw above all characters while it moves with its character.

```ts
import { Container, RenderLayer, Sprite } from "pixi.js";

const world = new Container();
const uiLayer = new RenderLayer({ sortableChildren: true });
app.stage.addChild(world, uiLayer); // the layer renders after world

const player = new Container();
const nameTag = new Sprite(tagTexture);
player.addChild(nameTag); // transforms still follow player
world.addChild(player);

uiLayer.attach(nameTag); // but it renders where uiLayer renders
// uiLayer.detach(nameTag) returns it to normal hierarchy order
```

- The layer itself must be in the scene graph, or attached objects do not render.
- An object must still have a parent in the scene graph. Attaching it to a layer does not make it a child of the layer, and `layer.addChild()` throws: use `attach()`.
- Removing the object from its parent also removes it from the layer. Re-adding it to a parent does not re-attach it; call `attach()` again.
- Known limitations (the API is marked experimental): hit testing still uses the hierarchy order, not the layer order; the layer and its attached objects must be in the same render group; filters on the object's ancestors do not apply to it while it is attached.
- Sort within a layer with `sortableChildren: true` and `zIndex`, or a custom `sortFunction`, or call `layer.sortRenderLayerChildren()` manually.

## Masking

```ts
const shape = new Graphics().circle(100, 100, 80).fill(0xffffff);
container.mask = shape; // Graphics mask: stencil, hard edges

const soft = new Sprite(gradientTexture);
container.mask = soft; // Sprite mask: uses the sprite's pixels, soft edges

container.setMask({ mask: shape, inverse: true }); // show everything except the shape
container.mask = null; // remove the mask
```

- A `Graphics` mask clips by geometry (stencil). It is the cheapest mask.
- A `Sprite` mask clips by texture pixels and supports soft edges. It costs more, because it renders through a filter-like pass.
- Add the mask object to the scene graph (usually as a sibling or child of the masked container) so it follows transforms. A mask's own fill color does not matter. The mask itself is not drawn.
- Masks and filters each break batching. Avoid applying many of them to many small objects; mask a parent container instead.

## Culling

Culling skips rendering objects that are outside the view. It is off by default.

```ts
import { CullerPlugin, extensions } from "pixi.js";

extensions.add(CullerPlugin); // before app.init: culls app.stage against app.screen every frame

sprite.cullable = true; // this object may be culled
world.cullableChildren = true; // (default) check children too
bigStatic.cullArea = new Rectangle(0, 0, 4000, 4000); // cheap bounds instead of measuring
```

Without the plugin you can cull manually before rendering: `Culler.shared.cull(app.stage, app.renderer.screen)`. See `pixijs-performance` for when culling pays off.

## Destroying

`destroy()` detaches the node and frees its own state. `destroy({ children: true })` recursively destroys the subtree. Add `texture: true` and `textureSource: true` only when nothing else uses those textures. Never use a node after destroying it. See `pixijs-scene-container` for details.
