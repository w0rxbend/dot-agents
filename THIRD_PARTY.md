# Third-party skill sources

Imported skills retain their upstream licenses and notices. The root MIT license covers the new
repository scripts and original documentation; it does not relicense third-party material.

`catalog.json` maps every skill to its source, license, and, where included, a license file.
[`licenses/upstream/index.json`](licenses/upstream/index.json) records upstream license URLs and Git blob hashes.
The snapshot preserves complete skill folders and bundled collection resources rather than copying
only `SKILL.md`. Copies are deduplicated only when the skill name and entire folder content match.

Sources include Addy Osmani's agent-skills, agentic-awesome-skills (formerly antigravity-awesome-skills),
ai-design-components, claude-code-templates, The Bushido Collective's Han, Caveman, dot-skills,
Vercel skills, Asyraf Hussin's agent-skills, design-patterns-skill, GoF patterns, Samber's Go skills,
ZIO skills, scala-zio-skills, Hermes Agent, Anthropic knowledge-work-plugins, Codex built-ins,
explicitly MIT-licensed Render skills, ciembor's agent-rules-books, and dykyi-roman's awesome-claude-code.

Han uses **FSL-1.1-ALv2**, a source-available license with permitted-purpose and competing-use restrictions
and a future Apache-2.0 grant. Read its included license before reusing those skills commercially.
Any local skills with no recorded upstream are labeled `LicenseRef-Local`; no additional upstream
license is inferred for them.

The Anthropic engineering, design, and productivity plugin skill files were compared with their
public `anthropics/knowledge-work-plugins` versions and matched byte for byte at import time.
Restricted hosted skills and other packages without established redistribution permission are listed
as `external`, with setup guidance in [docs/providers.md](docs/providers.md).

## Mill and VirtusLab Scala Stack

The 14 Mill skills and preference overlay are original guidance under the repository MIT
license, researched from [official Mill documentation](https://mill-build.org/mill/index.html).
The Mill MIT notice is retained at `licenses/upstream/com-lihaoyi--mill.txt` for adapted examples.
The [research manifest](docs/mill-research.json) records source attribution and retrieval hashes.

VirtusLab `direct-style-scala` is cataloged as external because no repository license or
redistribution grant was found at the pinned commit. Its source is downloaded directly by
the optional installer and is never copied into the public collection. Only the original
local preference overlay and installation code are distributed here.

## Repository-specific skills and PixiJS

The sixteen repository adaptation skills are original guidance under MIT, derived from
public build configuration and representative source contracts. Their references
link to reviewed public commits; private repository code and names are not included.

Nine skills from `pixijs/pixijs-skills` retain MIT notices and the pinned upstream
commit in the catalog. Three have reviewed local corrections. The existing skill
forks retain their original licenses, including FSL where applicable; the local fork
manifest does not change those terms. See [the review guide](docs/repository-skills.md).
