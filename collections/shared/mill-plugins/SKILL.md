---
name: mill-plugins
description: Extend Mill through build imports, contrib and third-party plugins, isolated JVM workers, meta-build sources, and tested custom language modules.
license: MIT
---

# Mill extensions and meta-builds

Read [extension-design.md](references/extension-design.md) for choosing a header library, helper trait, worker, plugin, or meta-build. Read [integrations.md](references/integrations.md) for the researched contrib/third-party catalog and the TypeScript/Python extension examples.

Use application module dependencies for application code and header/meta-build dependencies for build logic. Match plugin coordinates to the Mill binary platform and compatible Scala version. `$MILL_VERSION` / `$MILL_BIN_PLATFORM` are documented build-header substitutions, not shell substitutions to improvise elsewhere.

Keep ordinary build logic in small tracked tasks/traits. Isolate conflicting tool versions in subprocesses or classloaders; workers own reusable resources and must close them. Do not use a broad plugin or evaluator API merely to run one straightforward generator.

A custom plugin is a JVM library integrating Mill module traits. Test observable outputs, caching/invalidation, and a real consuming build before publication. Meta-build customization should solve a concrete compilation/classpath need; avoid recursive build layers without benefit. Experimental evaluator and precompiled APIs need explicit version checks.
