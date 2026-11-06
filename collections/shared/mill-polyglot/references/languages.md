# Language modules and heterogeneous outputs

## Shared graph, distinct artifacts

JVM modules consume compatible JVM modules via `moduleDeps`. JavaScript modules share JS/source/type outputs via supported module integration. Python modules share Python paths/dependencies. Across runtime families, pass explicit produced artifact: React bundle into server static resources, Python PEX/executable into deployment bundle, generated JSON/schema into JVM generator. Calling the task creates prerequisite edge; copying from guessed output location does not.

Official multilanguage example has React client, Python sentiment analysis bundle, Java server. Server resource task calls both producers and copies their outputs into own destination. Same pattern fits Scala/Kotlin servers. Verify deployed process finds/executes bundled tools and supplies their interpreter/native dependencies. Bundled file is not automatically runnable on every platform.

## Python

`PythonModule` gives source/configuration/dependency/run tasks; `PythonTests` adds Unittest/Pytest integrations. Configure `mainScript` as tracked source, put dependencies in `pythonDeps`, use tracked `pythonRequirementFiles` where applicable. Keep version/constraint semantics. Inspect transitive resolution; do not assume bare requirements file fully locks environment.

Private indexes need scoped credentials and explicit configuration. Unmanaged wheels must match OS/CPU/interpreter tags and be tracked artifacts. Tool downloads should honor offline mode and verify immutable inputs/checksums when handled manually. Keep virtual environments/output task-owned so parallel modules don't mutate shared installation.

Ruff handles formatting/linting, with separate check/fix modes. CoverageTests can instrument compatible Pytest workflows. Keep separate integration suites for Flask/Django/server/database behavior; give their processes owned lifecycle. Documented packaging: `PublishModule`, publish metadata, generated build files, local packaging/checks, then separate upload action. Building wheel does not authorize uploading it to PyPI.

## JavaScript and TypeScript

`javascriptlib.TypeScriptModule` and React/framework modules give compiler/bundle/run behavior. Distinguish `npmDeps`, `npmDevDeps`, unmanaged packages, module dependency outputs. Keep package metadata/lockfiles that define real project contract. Do not regenerate different dependency graph just because example's list is shorter.

Compiler options, ESM/CommonJS behavior, bundle externals, entrypoint paths, resources affect runtime compatibility. Dependency deliberately external to bundle must exist in deployed runtime. Tests can use Jest, Vitest, Mocha, or Jasmine integrations. Browser suites like Playwright/Cypress need their browsers and service lifecycle. ESLint/Prettier and coverage have separate configuration/tasks.

Publishing integration controls package metadata/exports/bundled outputs. Verify real consumer can import produced package and typings. Keep registry credentials out of package contents. Official Ollama-JS example shows real package/build/export wiring, not universal version list.

## Groovy

`GroovyModule` and `GroovyMavenModule` keep Groovy/source-layout conventions. Test traits and Spock/JUnit support differ from Java-only modules. Pick compatible Groovy/JDK/Spock version. Shared JVM libraries can connect via supported Java-compatible graph; still validate source/compiler/annotation behavior. Groovy scripts have own header/compiler integration; do not treat every Scala script key/API as identical.

## Adoption boundary

Experimental support may suit controlled repository tool or validated application. Before migrating critical build, check exact version's feature gaps and platform behavior. Keep representative fixture covering compile/run/test/package. Custom Python/TypeScript **extension examples** teach implementation techniques; they are not production built-in language modules.

Sources: [multilanguage builds](https://mill-build.org/mill/large/multi-language-builds.html), [Python intro](https://mill-build.org/mill/pythonlib/intro.html), [Python config](https://mill-build.org/mill/pythonlib/module-config.html), [Python dependencies](https://mill-build.org/mill/pythonlib/dependencies.html), [Python tests](https://mill-build.org/mill/pythonlib/testing.html), [Python linting](https://mill-build.org/mill/pythonlib/linting.html), [Python packaging](https://mill-build.org/mill/pythonlib/publishing.html), [Python web examples](https://mill-build.org/mill/pythonlib/web-examples.html), [JS intro](https://mill-build.org/mill/javascriptlib/intro.html), [JS config](https://mill-build.org/mill/javascriptlib/module-config.html), [JS dependencies](https://mill-build.org/mill/javascriptlib/dependencies.html), [JS testing](https://mill-build.org/mill/javascriptlib/testing.html), [JS linting](https://mill-build.org/mill/javascriptlib/linting.html), [JS publishing](https://mill-build.org/mill/javascriptlib/publishing.html), [JS real examples](https://mill-build.org/mill/javascriptlib/build-examples.html), [Groovy intro](https://mill-build.org/mill/groovylib/intro.html).
