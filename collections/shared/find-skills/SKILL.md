---
name: find-skills
description: Search the open agent-skills ecosystem (skills.sh, `npx skills find`) and propose an install command for the user to confirm. Use only when the user asks to find, add or install a new skill and no installed skill already covers the need; to choose among installed skills use using-agent-skills.
---

# Find Skills

This skill helps you discover and install skills from the open agent skills ecosystem.

## When to Use This Skill

Use this skill only when both hold:

- The user explicitly asks to find, add or install a skill ("is there a skill for X", "find me a skill that...", "install a skill for X").
- No installed skill already covers the need. Check the installed skill list first (and `using-agent-skills` for routing); recommend an installed skill instead of searching when one fits.

Do not use it for ordinary "how do I do X" questions; answer those directly or with an installed skill.

## This repository manages skills deliberately

In this repository (dot-agents), installed skills are vendored under `collections/` and registered in `catalog.json`; `./install.sh` renders the install config from the catalog and links skills into each agent (see README.md). A skill installed ad hoc with `npx skills add` bypasses that record. When working here or for this user:

- Prefer vendoring a found skill deliberately: review its SKILL.md and scripts, copy it into the right collection, add the catalog entry with source and license, then run `./install.sh check`.
- Use `npx skills add` only if the user explicitly wants an unmanaged install.

## What is the Skills CLI?

The Skills CLI (`npx skills`) is the package manager for the open agent skills ecosystem. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools.

**Key commands:**

- `npx skills find [query] [--owner <owner>]` - Search for skills interactively or by keyword, optionally scoped to a GitHub owner
- `npx skills add <package>` - Install a skill from GitHub or other sources
- `npx skills update` - Update all installed skills

**Browse skills at:** https://skills.sh/

## How to Help Users Find Skills

### Step 1: Understand What They Need

When a user asks for help with something, identify:

1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is a common enough task that a skill likely exists

### Step 2: Check the Leaderboard First

Before running a CLI search, check the [skills.sh leaderboard](https://skills.sh/) to see if a well-known skill already exists for the domain. The leaderboard ranks skills by total installs, surfacing the most popular and battle-tested options.

Well-known publishers include `vercel-labs/agent-skills` (React, Next.js, web design) and `anthropics/skills` (frontend design, document processing). Read the current install counts on the site rather than quoting remembered numbers.

### Step 3: Search for Skills

If the leaderboard doesn't cover the user's need, run the find command:

```bash
npx skills find [query] [--owner <owner>]
```

For example:

- User asks "how do I make my React app faster?" → `npx skills find react performance`
- User asks "can you help me with PR reviews?" → `npx skills find pr review`
- User asks "I need to create a changelog" → `npx skills find changelog`

### Step 4: Verify Quality Before Recommending

**Do not recommend a skill based solely on search results.** Always verify:

1. **Install count** — Prefer skills with 1K+ installs. Be cautious with anything under 100.
2. **Source reputation** — Official sources (`vercel-labs`, `anthropics`, `microsoft`) are more trustworthy than unknown authors.
3. **GitHub stars** — Check the source repository. A skill from a repo with <100 stars should be treated with skepticism.

### Step 5: Present Options to the User

When you find relevant skills, present them to the user with:

1. The skill name and what it does
2. The install count and source
3. The install command they can run
4. A link to learn more at skills.sh

Example response:

```
No installed skill covers React performance. On skills.sh, "react-best-practices"
from vercel-labs/agent-skills provides React and Next.js performance guidelines
(<install count from the site>). I read its SKILL.md: guidance only, no scripts.

Proposed command (not run yet):
npx skills add vercel-labs/agent-skills@react-best-practices -g

Or, to keep it managed in dot-agents, I can vendor it into collections/ and add a
catalog.json entry. Which do you want?
```

### Step 6: Review, Then Install Only With Confirmation

A skill is instructions and possibly scripts that an agent will follow, so treat it like a dependency:

1. Open the skill's SKILL.md and any bundled scripts in the source repository and read them. Flag anything that runs network calls, installs packages, touches credentials, or asks the agent to bypass confirmation.
2. Show the user the exact command you propose and wait for an explicit yes:

```bash
npx skills add <owner/repo@skill> -g
```

`-g` installs at user level. Do not add `-y`: let the CLI's own prompts run so the user sees what is installed and where. In dot-agents, propose vendoring into `collections/` + `catalog.json` instead (see above).

3. After installing, confirm the skill appears where the agent loads skills and summarize what it does.

## Common Skill Categories

When searching, consider these common categories:

| Category        | Example Queries                          |
| --------------- | ---------------------------------------- |
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing         | testing, jest, playwright, e2e           |
| DevOps          | deploy, docker, kubernetes, ci-cd        |
| Documentation   | docs, readme, changelog, api-docs        |
| Code Quality    | review, lint, refactor, best-practices   |
| Design          | ui, ux, design-system, accessibility     |
| Productivity    | workflow, automation, git                |

## Tips for Effective Searches

1. **Use specific keywords**: "react testing" is better than just "testing"
2. **Try alternative terms**: If "deploy" doesn't work, try "deployment" or "ci-cd"
3. **Check popular sources**: Many skills come from `vercel-labs/agent-skills` or `ComposioHQ/awesome-claude-skills`

## When No Skills Are Found

If no relevant skills exist:

1. Acknowledge that no existing skill was found
2. Offer to help with the task directly using your general capabilities
3. If the need recurs, suggest writing a skill (see `skill-writer`); `npx skills init <name>` scaffolds one

Example:

```
I searched for skills related to "xyz" but didn't find any matches.
I can still help you with this task directly! Would you like me to proceed?

If this is something you do often, you could create your own skill:
npx skills init my-xyz-skill
```
