---
name: mill-plugins
description: Extend Mill through build imports, contrib and third-party plugins, isolated JVM workers, meta-build sources, and tested custom language modules. Use when adding a plugin to a Mill build or writing reusable Mill extensions.
license: MIT
---

# Mill extensions and meta-builds

Read [extension-design.md](references/extension-design.md) to choose header library, helper trait, worker, plugin or meta-build. Read [integrations.md](references/integrations.md) for contrib/third-party catalog and TypeScript/Python extension examples.

Use application module dependencies for application code, header/meta-build dependencies for build logic. Match plugin coordinates to Mill binary platform and compatible Scala version. `$MILL_VERSION` / `$MILL_BIN_PLATFORM` are documented build-header substitutions, not shell substitutions to improvise elsewhere.

Keep ordinary build logic in small tracked tasks/traits. Isolate conflicting tool versions in subprocesses or classloaders. Workers own reusable resources and must close them. Do not use broad plugin or evaluator API for one straightforward generator.

Custom plugin: JVM library integrating Mill module traits. Before publishing, test observable outputs, caching/invalidation and a real consuming build. Customize meta-build only for a concrete compilation/classpath need. Avoid pointless recursive build layers. Experimental evaluator and precompiled APIs need explicit version checks.
