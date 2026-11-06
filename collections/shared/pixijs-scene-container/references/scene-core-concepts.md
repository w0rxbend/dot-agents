# PixiJS v8 scene core concepts

Shared background for `pixijs-scene-container`, `pixijs-scene-graphics`, `pixijs-scene-text` skills. Upstream PixiJS has separate `pixijs-scene-core-concepts` skill; this repo does not vendor it, so essentials are collected here. Checked against `pixi.js` 8.22 type definitions.

## Scene graph mental model

- Scene is a tree. `app.stage` is root `Container`; everything drawn is a node under it.
- **Containers** group nodes and hold children. **Leaves** (`Sprite`, `Graphics`, `Text`, `BitmapText`, `HTMLText`, `Mesh`, `TilingSprite`, `NineSliceSprite`) draw something; should not have children. Child on leaf logs deprecation warning. Group leaves by wrapping them in a `Container`.
- Transforms (`position`, `scale`, `rotation`, `pivot`, `skew`), `alpha`, `tint`, `visible` inherit. Child world transform: parent world transform multiplied by child local transform.
- Render order: depth-first, children-array order; index 0 drawn first (back). Reorder within one parent: `zIndex` with `sortableChildren: true`. Across parents: `RenderLayer` (below).
- Removing node from parent does not free it. Call `destroy()` (with `{ children: true }` for subtrees) when done.

## Constructor options shared by all scene objects

Every display object constructor accepts `Container` options alongside its own; any public `Container` property works. Common ones:

| Group | Options |
| --- | --- |
| Identity | `label` |
| Transform | `x`, `y`, `position`, `scale` (number or point), `rotation` (radians), `angle` (degrees), `pivot`, `origin`, `skew`, `width`, `height` |
| Appearance | `alpha`, `tint`, `blendMode`, `visible`, `renderable` |
| Ordering | `zIndex`, `sortableChildren` |
| Effects | `filters`, `filterArea`, `mask` |
| Rendering | `isRenderGroup`, `boundsArea` |
| Culling | `cullable`, `cullableChildren`, `cullArea` |
| Interaction | `eventMode`, `cursor`, `hitArea`, `interactiveChildren`, plus `on*` handlers like `onpointerdown` |
| Per-frame | `onRender` |

Bulk copy ignores `children`, `parent`, `effects`; add children with `addChild` after construction.

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

Render group: sub-tree whose transforms apply on GPU, so moving it does not recompute every child's transform on CPU. `app.stage` always is one.

```ts
const world = new Container({ isRenderGroup: true });
// or, on an existing container:
hud.enableRenderGroup();
```

Use for large, mostly static sub-trees moving as a whole: scrolling world, UI layer above it. Most scenes need none beyond stage. Each extra group adds overhead; profile before adding more.

## RenderLayer: render order independent of the hierarchy

`RenderLayer` draws objects at its own render-order position; each object keeps real parent for transforms. Typical use: character's name tag that must draw above all characters while moving with its character.

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

- Layer must be in scene graph, or attached objects do not render.
- Object still needs a parent in scene graph. Attaching does not make it layer's child; `layer.addChild()` throws, use `attach()`.
- Removing object from parent also removes it from layer. Re-adding to a parent does not re-attach; call `attach()` again.
- Known limitations (API marked experimental): hit testing still uses hierarchy order, not layer order. Layer and attached objects must share one render group. Ancestor filters do not apply to object while attached.
- Sort within layer: `sortableChildren: true` with `zIndex`, custom `sortFunction`, or manual `layer.sortRenderLayerChildren()`.

## Masking

```ts
const shape = new Graphics().circle(100, 100, 80).fill(0xffffff);
container.mask = shape; // Graphics mask: stencil, hard edges

const soft = new Sprite(gradientTexture);
container.mask = soft; // Sprite mask: uses the sprite's pixels, soft edges

container.setMask({ mask: shape, inverse: true }); // show everything except the shape
container.mask = null; // remove the mask
```

- `Graphics` mask clips by geometry (stencil). Cheapest.
- `Sprite` mask clips by texture pixels, allows soft edges. Costlier: renders through filter-like pass.
- Add mask object to scene graph (usually sibling or child of masked container) so it follows transforms. Its fill color does not matter; mask itself is not drawn.
- Masks and filters each break batching. Avoid many on many small objects; mask parent container instead.

## Culling

Culling skips rendering objects outside view. Off by default.

```ts
import { CullerPlugin, extensions } from "pixi.js";

extensions.add(CullerPlugin); // before app.init: culls app.stage against app.screen every frame

sprite.cullable = true; // this object may be culled
world.cullableChildren = true; // (default) check children too
bigStatic.cullArea = new Rectangle(0, 0, 4000, 4000); // cheap bounds instead of measuring
```

Without plugin, cull manually before render: `Culler.shared.cull(app.stage, app.renderer.screen)`. When culling pays off: `pixijs-performance`.

## Destroying

`destroy()` detaches node, frees own state. `destroy({ children: true })` destroys subtree recursively. Add `texture: true` and `textureSource: true` only when nothing else uses those textures. Never use node after destroying it. Details: `pixijs-scene-container`.
