---
name: astro
description: "Build content-focused websites with Astro 5+ - .astro components, file routing, content collections (Content Layer), client: island directives, on-demand rendering with adapters, and Markdown/MDX. Use when working in an Astro project or choosing Astro for a blog, docs or marketing site; not for SPA-style React/Next.js apps."
category: frontend
risk: safe
source: community
date_added: "2026-03-18"
author: suhaibjanjua
tags: [astro, ssg, ssr, islands, content, markdown, mdx, performance]
tools: [claude, cursor, gemini]
---

# Astro Web Framework

## Overview

Astro is a web framework designed for content-rich websites — blogs, docs, portfolios, marketing sites, and e-commerce. Its core innovation is the **Islands Architecture**: by default, Astro ships zero JavaScript to the browser. Interactive components are selectively hydrated as isolated "islands." Astro supports React, Vue, Svelte, Solid, and other UI frameworks simultaneously in the same project, letting you pick the right tool per component.

## When to Use This Skill

- Use when building a blog, documentation site, marketing page, or portfolio
- Use when performance and Core Web Vitals are the top priority
- Use when the project is content-heavy with Markdown or MDX files
- Use when you want SSG (static) output with optional SSR for dynamic routes
- Use when the user asks about `.astro` files, `Astro.props`, content collections, or `client:` directives

## How It Works

### Step 1: Project Setup

```bash
npm create astro@latest my-site
cd my-site
npm install
npm run dev
```

Add integrations as needed:

```bash
npx astro add tailwind        # Tailwind CSS
npx astro add react           # React component support
npx astro add mdx             # MDX support
npx astro add sitemap         # Auto sitemap.xml
npx astro add vercel          # Vercel SSR adapter
```

Project structure:

```
src/
  pages/          ← File-based routing (.astro, .md, .mdx)
  layouts/        ← Reusable page shells
  components/     ← UI components (.astro, .tsx, .vue, etc.)
  content/        ← Markdown/MDX files (any folder works with the glob loader)
  styles/         ← Global CSS
  content.config.ts ← Content collection definitions (Astro 5+)
public/           ← Static assets (copied as-is)
astro.config.mjs  ← Framework config
```

### Step 2: Astro Component Syntax

`.astro` files have a code fence at the top (server-only) and a template below:

```astro
---
// src/components/Card.astro
// This block runs on the server ONLY — never in the browser
interface Props {
  title: string;
  href: string;
  description: string;
}

const { title, href, description } = Astro.props;
---

<article class="card">
  <h2><a href={href}>{title}</a></h2>
  <p>{description}</p>
</article>

<style>
  /* Scoped to this component automatically */
  .card { border: 1px solid #eee; padding: 1rem; }
</style>
```

### Step 3: File-Based Pages and Routing

```
src/pages/index.astro          → /
src/pages/about.astro          → /about
src/pages/blog/[id].astro      → /blog/:id (dynamic)
src/pages/blog/[...path].astro → /blog/* (catch-all)
```

Dynamic route with `getStaticPaths`:

```astro
---
// src/pages/blog/[id].astro
import { getCollection, render } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map(post => ({
    params: { id: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await render(post);
---

<h1>{post.data.title}</h1>
<Content />
```

### Step 4: Content Collections

Content collections give you type-safe access to Markdown and MDX files. This is the Content Layer API (Astro 5+; the legacy `type: 'content'` collections in `src/content/config.ts`, `post.slug` and `post.render()` are gone in current versions):

```typescript
// src/content.config.ts
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
```

```astro
---
// src/pages/blog/index.astro
import { getCollection } from 'astro:content';

const posts = (await getCollection('blog'))
  .filter(p => !p.data.draft)
  .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
---

<ul>
  {posts.map(post => (
    <li>
      <a href={`/blog/${post.id}/`}>{post.data.title}</a>
      <time>{post.data.date.toLocaleDateString()}</time>
    </li>
  ))}
</ul>
```

### Step 5: Islands — Selective Hydration

By default, UI framework components render to static HTML with no JS. Use `client:` directives to hydrate:

```astro
---
import Counter from '../components/Counter.tsx';  // React component
import VideoPlayer from '../components/VideoPlayer.svelte';
---

<!-- Static HTML — no JavaScript sent to browser -->
<Counter initialCount={0} />

<!-- Hydrate immediately on page load -->
<Counter initialCount={0} client:load />

<!-- Hydrate when the component scrolls into view -->
<VideoPlayer src="/demo.mp4" client:visible />

<!-- Hydrate only when browser is idle -->
<Analytics client:idle />

<!-- Hydrate only on a specific media query -->
<MobileMenu client:media="(max-width: 768px)" />
```

### Step 6: Layouts

```astro
---
// src/layouts/BaseLayout.astro
interface Props {
  title: string;
  description?: string;
}
const { title, description = 'My Astro Site' } = Astro.props;
---

<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <meta name="description" content={description} />
  </head>
  <body>
    <nav>...</nav>
    <main>
      <slot />  <!-- page content renders here -->
    </main>
    <footer>...</footer>
  </body>
</html>
```

```astro
---
// src/pages/about.astro
import BaseLayout from '../layouts/BaseLayout.astro';
---

<BaseLayout title="About Us">
  <h1>About Us</h1>
  <p>Welcome to our company...</p>
</BaseLayout>
```

### Step 7: SSR Mode (On-Demand Rendering)

Enable on-demand rendering by adding an adapter:

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel';

export default defineConfig({
  output: 'static',  // 'static' (default) | 'server'; 'hybrid' was removed in Astro 5
  adapter: vercel(),
});
```

With `output: 'static'` plus an adapter, opt individual pages or endpoints into on-demand rendering with `export const prerender = false`. With `output: 'server'`, everything renders on demand unless a page sets `export const prerender = true`.

## Examples

### Example 1: Blog with RSS Feed

```typescript
// src/pages/rss.xml.ts
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const posts = await getCollection('blog');
  return rss({
    title: 'My Blog',
    description: 'Latest posts',
    site: context.site,
    items: posts.map(post => ({
      title: post.data.title,
      pubDate: post.data.date,
      link: `/blog/${post.id}/`,
    })),
  });
}
```

### Example 2: API Endpoint (SSR)

```typescript
// src/pages/api/subscribe.ts
import type { APIRoute } from 'astro';

export const prerender = false; // needed unless output: 'server'

export const POST: APIRoute = async ({ request }) => {
  const { email } = await request.json();

  if (!email) {
    return new Response(JSON.stringify({ error: 'Email required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  await addToNewsletter(email);
  return new Response(JSON.stringify({ success: true }), { status: 200 });
};
```

### Example 3: React Component as Island

```tsx
// src/components/SearchBox.tsx
import { useState } from 'react';

export default function SearchBox() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    const data = await fetch(`/api/search?q=${query}`).then(r => r.json());
    setResults(data);
  }

  return (
    <form onSubmit={search}>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button type="submit">Search</button>
      <ul>{results.map(r => <li key={r.id}>{r.title}</li>)}</ul>
    </form>
  );
}
```

```astro
---
import SearchBox from '../components/SearchBox.tsx';
---
<!-- Hydrated immediately — this island is interactive -->
<SearchBox client:load />
```

## Best Practices

- ✅ Keep most components as static `.astro` files — only hydrate what must be interactive
- ✅ Use content collections for all Markdown/MDX content — you get type safety and auto-validation
- ✅ Prefer `client:visible` over `client:load` for below-the-fold components to reduce initial JS
- ✅ Use `import.meta.env` for environment variables — prefix public vars with `PUBLIC_`
- ✅ Add `<ClientRouter />` from `astro:transitions` (named `<ViewTransitions />` before Astro 5) for smooth page navigation without a full SPA
- ❌ Don't use `client:load` on every component — this defeats Astro's performance advantage
- ❌ Don't put secrets in `.astro` frontmatter that gets used in client-facing templates
- ❌ Don't skip `getStaticPaths` for dynamic routes in static mode — builds will fail

## Security & Safety Notes

- Frontmatter code in `.astro` files runs server-side only and is never exposed to the browser.
- Use `import.meta.env.PUBLIC_*` only for non-sensitive values. Private env vars (no `PUBLIC_` prefix) are never sent to the client.
- When using SSR mode, validate all `Astro.request` inputs before database queries or API calls.
- Sanitize any user-supplied content before rendering with `set:html` — it bypasses auto-escaping.

## Common Pitfalls

- **Problem:** JavaScript from a React/Vue component doesn't run in the browser
  **Solution:** Add a `client:` directive (`client:load`, `client:visible`, etc.) — without it, components render as static HTML only.

- **Problem:** `getStaticPaths` data is stale after content updates during dev
  **Solution:** Astro's dev server watches content files — restart if changes to `src/content.config.ts` are not reflected.

- **Problem:** `Astro.props` type is `any` — no autocomplete
  **Solution:** Define a `Props` interface or type in the frontmatter and Astro will infer it automatically.

- **Problem:** CSS from a `.astro` component bleeds into other components
  **Solution:** Styles in `.astro` `<style>` tags are automatically scoped. Use `:global()` only when intentionally targeting children.

## Related Skills

- `frontend-ui-engineering` — Component structure, state and accessibility for the interactive islands
- `frontend-design` — Visual design direction for the site
- `theming-components` — Design tokens and theming (including Tailwind setups)

## Limitations
- Examples target Astro 5 and later (checked against Astro 7). For an Astro 4 project, check its version in `package.json` before applying the content-collection and config snippets.
