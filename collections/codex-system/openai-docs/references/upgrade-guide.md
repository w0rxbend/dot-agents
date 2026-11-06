# Model upgrade guidance

Use this file only as bundled routing fallback when live migration guide cannot be fetched.

Latest, current, default or unspecified-model upgrades:

1. Run `scripts/resolve-latest-model-info`.
2. Fetch returned `migrationGuideUrl` and `promptingGuideUrl` exactly.
3. Live guides are canonical.
4. If remote retrieval fails, disclose bundled fallback guidance use.

Explicit GPT-6 Astra migration:

1. Keep user's explicit target. Do not run latest-model resolver.
2. Fetch live GPT-6 model guidance:

   https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md

3. Read `references/upgrading-to-gpt-6-astra.md` for skill-specific migration judgment.
4. Read `references/prompting-guide.md` only when prompt changes are needed.

Other explicit model target: keep it, fetch its current official guidance. Do not reuse GPT-6-specific defaults, API shapes or compatibility rules for a different model.
