---
name: human-copywrite
description: "Editorial style rules distilled from the Apple Style Guide: voice and tone, punctuation, capitalization, hyphenation, numbers, dates and units, UI-element vocabulary, technical notation and localization. Use when writing or editing UI strings, error messages, help or onboarding text, or release notes, or when deciding how to format a term, number or unit; use copywriting for conversion-focused marketing pages."
---
# Human Copywrite

Editorial style and usage guidance distilled from the Apple Style Guide (June 2025). Use it whenever you're producing text a human will read.

## When to Apply

Apply it when polished user-facing wording is the deliverable, or when a style question comes up. Do not load it for ordinary chat answers or internal notes. Specifically:

- **UI strings & error messages** — button labels, dialog text, empty states, onboarding copy. Voice and UI-vocabulary rules apply.
- **User-facing documentation** — help articles, READMEs, onboarding guides, tutorials. All rules apply.
- **Developer documentation** — API references, SDK guides, code comments meant for humans. Add the technical-notation rules.
- **Marketing copy** — feature announcements, landing pages, release notes. Voice, capitalization, and product-name rules are load-bearing.
- **Localized content** — anything that will be translated. The international-style rules become primary.
- **Writing about Apple platforms** — even if the surrounding product isn't an Apple product, refer to Apple hardware/software by Apple's preferred forms (iPhone, iPad, macOS, App Store).

If the user is writing code with no user-facing strings, skip this skill. If they're writing a function name or variable, that's not copywriting — that's naming, which lives elsewhere.

## Core Principles

These run through every section. When in doubt, fall back on them.

1. **Active voice, present tense, second person.** *You can connect your iPhone to a Mac.* Not *Your iPhone may be connected to a Mac.*
2. **Specific over generic.** *Choose File > Save.* Not *Use the menu to save the file.*
3. **Plain words over jargon.** *Turn on* over *activate*. *Log in* over *authenticate* (unless authenticate is technically precise).
4. **Don't make the product the subject of an action the user takes.** *You can create a database with FileMaker Pro.* Not *FileMaker Pro allows you to create a database.*
5. **Items *appear* on screen — they don't *display*.** *The setup assistant appears.* Not *The setup assistant is displayed.*
6. **Don't restate what code does — say *why*.** Applies to code comments.
7. **Respect product names verbatim.** AirPods (not Airpods), iCloud (not iCloud+ unless you mean the paid tier), Apple Pencil (not the Apple pencil).
8. **Numbers ≥10 stay digits; <10 spell out** — but with many exceptions ([numbers-and-dates.md](references/numbers-and-dates.md)).
9. **Compound modifiers preceding a noun are hyphenated; following the verb they're not** — *user-friendly app*, *the app is user friendly*.
10. **In code, never use a function name as a verb.** *Run `ls` on both directories* — not *`ls` both directories*.

## How to Use

Always read this SKILL.md first, then load the topic file(s) relevant to the current task. For one-off term lookups, jump to [references/a-z-lookup.md](references/a-z-lookup.md) and follow its pointer to the topic file.

### Topic files

| File | When to read |
|------|--------------|
| [voice-and-tone.md](references/voice-and-tone.md) | Any user-facing prose. Most copy decisions live here. |
| [punctuation.md](references/punctuation.md) | Deciding on em dashes, en dashes, ellipses, commas, colons, apostrophes, quotes. |
| [capitalization.md](references/capitalization.md) | Writing headings, titles, button labels, or proper-noun-adjacent terms. |
| [hyphenation-and-compounds.md](references/hyphenation-and-compounds.md) | Compound modifiers, e- and re- prefixes, *user-friendly* vs *user friendly*. |
| [numbers-and-dates.md](references/numbers-and-dates.md) | Writing dates, times, ranges, ordinals, percentages, fractions, decades, *2D*, *4K*, *24/7*. |
| [units-of-measure.md](references/units-of-measure.md) | Quoting GB, MHz, mm, inches, etc. Full SI unit/symbol table. |
| [word-choice-and-confusables.md](references/word-choice-and-confusables.md) | Pairs like *affect/effect*, *backup/back up*, *login/log in*, *OK*, *email*, *online*. |
| [abbreviations-and-acronyms.md](references/abbreviations-and-acronyms.md) | When to spell out, file types, plurals, articles. Includes industry acronyms (URL, ISP, JPEG, etc.). |
| [ui-elements.md](references/ui-elements.md) | Vocabulary for buttons, menus, sheets, popovers, sidebars, controls. |
| [apple-products.md](references/apple-products.md) | Apple hardware names: iPhone, iPad, Mac, MacBook, Apple Watch, AirPods, Apple Pencil, etc. |
| [apple-features-software.md](references/apple-features-software.md) | macOS, iOS, iCloud, Apple Music, Siri, AirDrop, Apple Intelligence, Genmoji, and all Apple software/services/features. |
| [technical-notation.md](references/technical-notation.md) | Developer documentation: code font, syntax descriptions, placeholders. |
| [international-style.md](references/international-style.md) | Localized or international content: ISO country/currency/language codes, ISO 8601 dates, telephone numbers. |

### A-Z lookup

For a single term ("How do I write *backup* vs *back up*?"), open [references/a-z-lookup.md](references/a-z-lookup.md) and follow the pointer to the topic file with that entry.

## Gotchas

See [gotchas.md](gotchas.md). One scope note worth knowing up front: the source's "Writing inclusively" chapter (pronouns, person-first vs identity-first language, replacements for *blacklist/whitelist* and *master/slave*) was intentionally excluded from this skill at ingest time.

## Source

Apple Style Guide, June 2025 (243 pages). Distilled and re-organized by topic for selective loading. Source content is preserved verbatim where reproduced. The web version of the guide is at https://support.apple.com/guide/applestyleguide/welcome/web.
