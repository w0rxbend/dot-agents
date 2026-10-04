# Code quality and design pattern skills

Checked the skills.sh directory, Skills CLI search results, repository popularity, licenses, and
the actual skill instructions on 2026-10-04. Install counts and GitHub stars are snapshots.

| Topic | Match | Status and adoption | Coverage |
| --- | --- | --- | --- |
| Code Complete | [ciembor/agent-rules-books: code-complete](https://skills.sh/ciembor/agent-rules-books/code-complete) | Candidate; 202 installs; source repository 2,902 stars; MIT | Construction discipline, routines, variables, control flow, defensive programming, and tests, based on Steve McConnell's principles. |
| Refactoring Guru | [`refactoring-guru`](../collections/shared/refactoring-guru/SKILL.md) | Already included | Code smells, refactoring technique selection, and design pattern tradeoffs. An alternate [ciembor implementation](https://skills.sh/ciembor/agent-rules-books/refactoring-guru) has 194 installs and the same 2,902-star MIT source repository. |
| Clean Code | [`clean-code`](../collections/shared/clean-code/SKILL.md) from [sickn33/agentic-awesome-skills](https://skills.sh/sickn33/agentic-awesome-skills/clean-code) | Already included; directory match 12K installs; source repository 47,235 stars; MIT | Robert C. Martin's code readability and maintainability principles. `clean-code-principles` and `clean-code-guard` are also included. |
| GoF | [`gof-patterns`](../collections/shared/gof-patterns/SKILL.md), [`design-patterns`](../collections/shared/design-patterns/SKILL.md) | Already included; their small source repositories each have 1 star | GoF pattern identification and suitability, plus pattern selection and implementation guidance. Limited source popularity; inclusion preserves your installed collection. |
| GRASP | [dykyi-roman/awesome-claude-code: grasp-knowledge](https://skills.sh/dykyi-roman/awesome-claude-code/grasp-knowledge) | Candidate; 8 installs; source repository 102 stars; MIT | All nine responsibility assignment principles. PHP 8.4 examples; limited adoption. No widely adopted general-purpose GRASP-only match found. |
| SOLID | [`design-patterns`](../collections/shared/design-patterns/SKILL.md); [thebeardedbearsas/claude-craft: solid-principles](https://skills.sh/thebeardedbearsas/claude-craft/solid-principles) | Included via design-patterns; dedicated candidate has 143 installs and a 106-star MIT source repository | Dedicated skill covers all five principles and multiple OO languages. Its longer reference document is in French. |

The strongest direct addition for the missing book-specific topic is **Code Complete**.
Your installed Refactoring Guru, Clean Code, and GoF skills already cover those topics.
GRASP and dedicated SOLID matches are narrower candidates with lower adoption.
Searching `solid` also returns SolidJS and Solidity skills, which address different topics.

Optional installation commands for the candidates (not installed by this discovery):

```sh
npx skills add ciembor/agent-rules-books --skill code-complete -g -y
npx skills add ciembor/agent-rules-books --skill refactoring-guru -g -y
npx skills add thebeardedbearsas/claude-craft --skill solid-principles -g -y
npx skills add dykyi-roman/awesome-claude-code --skill grasp-knowledge -g -y
```

Installing the alternate `refactoring-guru` may conflict with your existing skill of the same name;
review the selected agent destinations and keep a backup before replacing it.
After adding skills to your global collection, record their upstream licenses and deliberately refresh
the dot-agents inventory as described in the README.

Inspected primary sources:
[Code Complete](https://github.com/ciembor/agent-rules-books/tree/main/code-complete),
[Refactoring Guru](https://github.com/ciembor/agent-rules-books/tree/main/refactoring-guru),
[SOLID](https://github.com/thebeardedbearsas/claude-craft/tree/main/.claude/skills/solid-principles),
[GRASP](https://github.com/dykyi-roman/awesome-claude-code/tree/master/skills/grasp-knowledge).
