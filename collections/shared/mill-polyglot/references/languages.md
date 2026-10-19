# Language modules and heterogeneous outputs

## Shared graph, distinct artifacts

A JVM module consumes another compatible JVM module through `moduleDeps`. JavaScript modules share JS/source/type outputs through their supported module integration, and Python modules share Python paths/dependencies. Across runtime families, pass an explicit produced artifact: a React bundle into server static resources, a Python PEX/executable into a deployment bundle, or generated JSON/schema into a JVM generator. The task call creates the prerequisite edge; copying from a guessed output location does not.

The official multilanguage example has a React client, Python sentiment analysis bundle, and Java server. Its server resource task calls both producers and copies their outputs into its own destination. That pattern generalizes to Scala/Kotlin servers. Verify the deployed process locates/executes bundled tools correctly and supplies their interpreter/native dependencies; a bundled file is not automatically runnable on every platform.

## Python

`PythonModule` provides source/configuration/dependency/run tasks and `PythonTests` with Unittest/Pytest integrations. Configure `mainScript` as a tracked source, put dependencies in `pythonDeps`, and use tracked `pythonRequirementFiles` where applicable. Preserve version/constraint semantics and inspect transitive resolution rather than assuming a bare requirements file fully locks an environment.

Private indexes require scoped credentials and explicit configuration. Unmanaged wheels must match OS/CPU/interpreter tags and be tracked artifacts. Tool downloads should honor offline mode and verify immutable inputs/checksums when handled manually. Keep virtual environments/output under task ownership so parallel modules don't mutate a shared installation.

Ruff integration handles formatting/linting with separate check/fix modes; CoverageTests can instrument compatible Pytest workflows. Separate integration suites for Flask/Django/server/database behavior and give processes owned lifecycle. The documented packaging uses `PublishModule`, publish metadata, generated build files, local packaging/checks, then a separate upload action. Building a wheel does not authorize uploading it to PyPI.

## JavaScript and TypeScript

`javascriptlib.TypeScriptModule` and React/framework modules provide compiler/bundle/run behavior. Distinguish `npmDeps`, `npmDevDeps`, unmanaged packages, and module dependency outputs. Preserve package metadata/lockfiles when they define the real project contract; avoid regenerating a different dependency graph merely because an example's list is shorter.

Compiler options, ESM/CommonJS behavior, bundle externals, entrypoint paths, and resources affect runtime compatibility. A dependency intentionally external to a bundle must exist in the deployed runtime. Tests can use Jest, Vitest, Mocha, or Jasmine integrations; browser suites such as Playwright/Cypress require their browsers and service lifecycle. ESLint/Prettier and coverage have separate configuration/tasks.

The publishing integration controls package metadata/exports/bundled outputs. Verify an actual consumer can import the produced package and typings. Keep registry credentials outside package contents. The official Ollama-JS example is useful for real package/build/export wiring, not a universal version list.

## Groovy

`GroovyModule` and `GroovyMavenModule` preserve Groovy/source-layout conventions; test traits and Spock/JUnit support differ from Java-only modules. Select a compatible Groovy/JDK/Spock version. Shared JVM libraries can connect through the supported Java-compatible graph, but source/compiler/annotation behavior still needs validation. Groovy scripts have their own header/compiler integration; do not treat every Scala script key/API as identical.

## Adoption boundary

Experimental support may be appropriate for a controlled repository tool or a validated application, but check the exact version's feature gaps and platform behavior before migrating a critical build. Keep a representative fixture with compile/run/test/package behavior. The custom Python/TypeScript **extension examples** teach implementation techniques and are distinct from production built-in language modules.

Sources: [multilanguage builds](https://mill-build.org/mill/large/multi-language-builds.html), [Python intro](https://mill-build.org/mill/pythonlib/intro.html), [Python config](https://mill-build.org/mill/pythonlib/module-config.html), [Python dependencies](https://mill-build.org/mill/pythonlib/dependencies.html), [Python tests](https://mill-build.org/mill/pythonlib/testing.html), [Python linting](https://mill-build.org/mill/pythonlib/linting.html), [Python packaging](https://mill-build.org/mill/pythonlib/publishing.html), [Python web examples](https://mill-build.org/mill/pythonlib/web-examples.html), [JS intro](https://mill-build.org/mill/javascriptlib/intro.html), [JS config](https://mill-build.org/mill/javascriptlib/module-config.html), [JS dependencies](https://mill-build.org/mill/javascriptlib/dependencies.html), [JS testing](https://mill-build.org/mill/javascriptlib/testing.html), [JS linting](https://mill-build.org/mill/javascriptlib/linting.html), [JS publishing](https://mill-build.org/mill/javascriptlib/publishing.html), [JS real examples](https://mill-build.org/mill/javascriptlib/build-examples.html), [Groovy intro](https://mill-build.org/mill/groovylib/intro.html).
