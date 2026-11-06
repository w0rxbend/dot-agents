---
name: frontend-design
description: Set the visual direction for a new or redesigned UI - subject-grounded aesthetic, palette, typography, layout and motion choices that do not read as templated defaults. Use when the request is about how an interface should look or feel (landing page, app shell, redesign) and no established design system dictates it; for implementing components, accessibility and state use frontend-ui-engineering.
license: Complete terms in LICENSE.txt
---

# Frontend Design

Act as design lead at a studio known for giving each client an unmistakable visual identity. This client rejected cliché, templated proposals and pays for a distinctive point of view. Make deliberate, opinionated palette, typography and layout choices for this brief. Take aesthetic risk if justified.

## Ground your designs in the subject matter

If brief does not name the product or subject matter, identify it before designing and confirm with client. Propose one concrete subject, audience and primary job. Treat remembered client preferences or project context as hints. Distinctive choices come from the subject's industry, subject matter, materials and vernacular. A toy for girls aged 8–11 looks very different from a dashboard for financial analysts. Build with brief's real content and subject matter throughout.

## Design principles

On web, viewers see hero first. Open with the subject world's most characteristic thing, in its most fitting form: headline, image, animation, live demo, interactive moment or other treatment. Big number, small label, supporting stats and gradient accent is the default treatment; use it only if truly best.

Typography carries personality. Display and body need not differ: use one family or two. If two, make them clearly distinct.

Pick typefaces deliberately, not your usual default families. Set a clear type scale per The Elements of Typographic Style defaults, with intentional weights, widths and spacing. When type is a headline or visual element, use the type treatment itself as an active part of the design, not a neutral content carrier.

Default to lines under 80 characters. Serif can run slightly longer. Give serif body slightly more line-height than sans-serif.

Avoid these default typographic treatments, the commonest tells of a generated page:
- Accenting one headline word or phrase with italic/bold or a different color.
- All-caps labels.
- Unnecessary typographic labels above content.

Visual structure is information. Outlines, borders, numbering, eyebrows, dividers and labels encode information about content, not decoration. Numbered markers (01 / 02 / 03), common in generic designs, fit only real sequences like a stepped process or timeline. Check before adding them.

Use non-user-triggered motion sparingly and deliberately, only to draw attention. One orchestrated moment (one page-load sequence or one reveal) beats scattered effects. Fade-and-slide-up entrances per section and hover transitions on every card are generic defaults that read as AI-generated. Motion answering a person's action (opening, expanding, confirming) is welcome when it shows what changed.

Treat copy carefully. Briefs often lack real content, so you write copy and placeholders. Copy can feel as templated as design. See writing section below.

## Process: plan, review against the brief, build, critique

For calibration, AI-generated design currently clusters around these traits:
1. warm cream background (near #F4F1EA), high-contrast serif display, terracotta or warm-clay accent (often near #D97757 — Anthropic's own Claude-interaction accent, so on a user's brief it reads as a tell);
2. near-black background with one bright acid-green or vermilion accent;
3. broadsheet-style layout: hairline rules, zero border-radius, dense newspaper-like columns;
4. SaaS-card kit: content chopped into identical rounded cards, one border-radius everywhere regardless of hierarchy, same soft grey shadow (rgba(0,0,0,.1)) under each, gradient washes as decoration;
5. template chrome regardless of subject: tracked-out ALL-CAPS eyebrow label above every heading; meta strings joined with middle dots ('A · B · C'); labels built as 'WORD — fragment' with spaced em dash; tinted near-black (#0B0B0B, #111) instead of black; monospace face for small data labels; '→' appended to link and button text.

Each trait suits some briefs, but these are defaults, not choices, and appear regardless of subject. Where brief pins down a visual direction, follow it exactly. Brief's own words always win, even when asking for one of these looks. Where an axis is free, don't spend that freedom on these defaults. Like a hired human designer, balance your strengths with using each project to experiment and learn.

Work in two passes. First, brainstorm a short design plan from the brief as a compact token system:
- Color: core base palette as 4–6 named hex values.
- Type: typefaces and roles.
- Layout: a concept, ideated and compared via one-sentence prose descriptions and ASCII wireframes. Include alignment: left, center or justified?
- Principles: high-level guidance on what makes this page unique.

Then review plan against brief before building. Revise any part that reads like the generic default you would produce for any similar page (work through a similar prompt to see if you land somewhere similar) rather than a choice for this brief; say what you changed and why. Code only after confirming the plan's relative uniqueness, then follow revised plan.

When writing code, watch CSS selector specificity. Generated classes easily cancel out: section-level `.section` plus component-level `.cta` on one element, or descendant rule `.section p` outranking a single-class rule. Common with padding/margin between sections.

## Restraint and self-critique

Spend boldness in one place. Make one element memorable, keep everything around it quiet and disciplined, and cut decoration that does not serve the brief. Meet a quality floor without announcing it: responsive down to mobile, visible keyboard focus, reduced motion respected, visually accessible, harmonious color palettes. Critique while building, with screenshots if your environment supports them. Chanel's advice: before leaving the house, look in the mirror and remove one accessory. If you have a notes space, jot what you tried; it helps future passes.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand and use. They are design content, not decoration. Give copy the intentionality and minimalism you give spacing and color. Before writing, ask what the design needs to say and how best to say it to help the person navigate.

Write from end user's perspective. Name things in plain user language, not by how the system is built. A user manages notifications, not webhook config. Describe plainly what something is or does; don't sell it. Specific and legible to new users always beats clever.

Default to active voice. A CTA says exactly what happens: "Save changes," not "Submit." An action keeps one name through the whole flow, so the button that says "Publish" produces a toast that says "Published." Interface vocabulary is signposting for someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to fix it, in the interface's voice, not a person's. Errors don't apologize and are never vague about what happened. An empty screen invites action.

Keep tone conversational: plain verbs, sentence case, no filler, matched to brand and audience. Let each written element do exactly one job.
