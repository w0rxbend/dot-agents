# Restore provider-managed skills

`catalog.json` records provider-managed skill names, original location patterns, and content hashes.
It contains no account IDs, credentials, or copies of restricted skill files.
These entries remain in the inventory even though a clone alone cannot supply their files or tools.

| Collection | Restore on a new machine |
| --- | --- |
| Codex built-in review skill | Install/update Codex; let it manage `~/.codex/skills/.system`. |
| OpenAI document, PDF, spreadsheet, presentation, and template runtime skills | Install the corresponding plugins through Codex/ChatGPT's supported plugin management. Their runtimes and tool access are provider-managed. |
| OpenAI curated plugins, analytics, templates, Pages, Sites, browser recording, and work pets | Enable the corresponding plugins and connect the services they require in the supported application. |
| Anthropic synced document and productivity skills | Sign in to Claude, enable skills in your account/Customize settings, and let the application sync them. |

Some installed document skill licenses explicitly prohibit extraction, reproduction, and distribution.
Other hosted plugin packages provide no standalone redistribution grant. This repository records them
as `external` and never includes their instruction text or assets in Git or release archives.

After the provider restores the original files, optionally run:

```sh
./install.sh --include-local --dry-run
./install.sh --include-local
./install.sh --include-local --check
```

If global root symlinks conflict, add `--replace` to back them up, as described in the README.
The installer looks only in the catalog's recorded paths below your home directory, follows existing
directories, and creates local links. Some providers use different paths or versions: in that case,
use the provider's native discovery rather than assuming a local link enables its tools.

Official discovery details: [Codex skills](https://learn.chatgpt.com/docs/build-skills),
[Claude Code and synced skills](https://code.claude.com/docs/en/skills).

## VirtusLab Scala Stack

The official [direct-style-scala skill](https://github.com/VirtusLab/scala-skill) has no
verified redistribution grant. Restore it directly with `python3 scripts/install_vss.py`,
then `./install.sh --include-local` (add `--agents all` to target every agent).
The source lives outside managed agent directories to avoid replacing it with a self-link.
The pinned installer adds [the user's Mill preference](../overlays/direct-style-scala/preferences.md);
see [the full setup and research guide](mill-skills.md).

## Local private repository context

`worxbend-private-repository-context` is generated from an authorized local repository
review and remains external. A clone contains its generator, not private names or
observations. Recreate it with `scripts/review_repositories.py --include-private`
and `scripts/build_private_profile.py`, keeping evidence outside the public clone.
Then `./install.sh --agents all --include-local` links the local source. See
[the complete commands and privacy boundaries](repository-skills.md#private-context-on-another-machine).
