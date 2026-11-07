# UI Prototype

Generate **several radically different UI variations** on one route, switched from floating bottom bar. User flips variants in browser, picks one (or steals bits from each), throws rest away.

Question about logic/state rather than looks? Wrong branch; use [LOGIC.md](LOGIC.md).

## When this is the right shape

- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- "Try a different layout for the settings screen."
- Any time user would otherwise spend a day picking between three vague mockups in their head.

## Two sub-shapes: strongly prefer sub-shape A

UI prototype is far easier to judge **butting up against the rest of the app**: real header, sidebar, data, density. Throwaway route alone is a vacuum: every variant looks fine in isolation. Default to sub-shape A whenever a plausible existing page can host variants.

### Sub-shape A: adjustment to an existing page (preferred)

Route exists. Variants render **on the same route**, gated by `?variant=` URL search param. Existing data fetching, params, auth stay; only rendering swaps.

Something without a page yet that *would naturally live inside one* (new dashboard section, new settings-screen card, new step in existing flow) is still sub-shape A. Mount variants inside host page.

### Sub-shape B: a new page (last resort)

Only when prototyped thing genuinely has no existing page to live inside (e.g. entirely new top-level surface, or flow that can't be embedded anywhere sensible).

Create **throwaway route** per project's existing routing convention. Name it so it's obviously a prototype (e.g. word `prototype` in path or filename). Same `?variant=` pattern.

Before choosing sub-shape B, sanity-check: really no existing page to embed it in?

## Process

### 1. State the question and pick N

Default **3 variants**. Cap at 5: beyond that, variants stop being radically different and become noise.

Write plan in one line, at prototype's location or top-of-file comment:

> "Three variants of the settings page, switchable via `?variant=`, on the existing `/settings` route."

### 2. Generate radically different variants

Draft each variant, held to:

- Page's purpose and data it can access.
- Project's component library / styling system (TailwindCSS, shadcn, MUI, plain CSS, whatever).
- Clear exported component name, e.g. `VariantA`, `VariantB`, `VariantC`.

Variants must be **structurally different**: layout, information hierarchy, primary affordance, not just colours. Three slightly-tweaked card grids is wallpaper, not UI prototype. If two drafts come out too similar, redo one with explicit "do not use a card grid" guidance.

### 3. Wire them together

One switcher component on route:

```tsx
// pseudo-code, adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

Sub-shape A (existing page): keep all existing data fetching above switcher; only rendered subtree changes per variant.

Sub-shape B (new page): throwaway route under `/prototype/<name>` mounts same switcher.

### 4. Build the floating switcher

Small fixed-position bar, bottom-centre of screen, three pieces:

- **Left arrow**: previous variant (wraps around).
- **Variant label**: current variant key, plus variant's exported name if any, e.g. `B (Sidebar layout)`.
- **Right arrow**: next variant (wraps around).

Behaviour:

- Arrow click updates URL search param via framework's router (e.g. `router.replace` on Next, `navigate` on React Router, etc), so variant is shareable and reload-stable.
- Keyboard: `←` and `→` arrow keys also cycle. Don't intercept arrow keys when `<input>`, `<textarea>`, or `[contenteditable]` is focused.
- Visually distinct from page (e.g. high-contrast pill, subtle shadow), obviously not part of design under evaluation.
- Hidden in production builds: gate on `process.env.NODE_ENV !== 'production'` or equivalent check, so stray prototype merge can't ship bar to users.

One shared switcher component, reused by both sub-shapes. Place it where project's shared UI lives.

### 5. Hand it over

Surface URL and `?variant=` keys. User flips through when they get to it. Best feedback is usually **"I want the header from B with the sidebar from C"**: the design they actually want.

### 6. Capture the answer and clean up

Once a variant wins, capture answer (which variant, why), then capture prototype per [SKILL](SKILL.md). Fold winner into real code; move rest to throwaway branch, not into main:

- **Sub-shape A**: fold winner into existing page; drop losing variants and switcher from main.
- **Sub-shape B**: promote winning variant to real route; drop throwaway route and switcher from main.

Full set of variants is the primary source: it lands on throwaway branch, not the bin. Variant components and switcher left in main rot fast and confuse next reader.

## Anti-patterns

- **Variants that differ only in colour or copy.** Real variants disagree about structure.
- **Sharing too much code between variants.** Shared `<Header>` fine; shared `<Layout>` defeats the point. Each variant stays free to throw out layout.
- **Wiring variants to real mutations.** Read-only prototypes fine. Variant needing mutation points at a stub: question is "what should this look like", not "does the backend work".
- **Promoting the prototype directly to production.** Variant code was written under prototype constraints (no tests, minimal error handling). Rewrite properly when folding in.
