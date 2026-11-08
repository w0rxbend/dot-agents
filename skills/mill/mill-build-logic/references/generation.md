# Generated source and resource pipelines

`assets/codegen` template: Java `app` module, `app/message.txt`, tracked `schema` source task. `generatedSources` reads input, validates deliberately limited example format, writes `example/Generated.java` under its destination, returns `super.generatedSources() ++ Seq(PathRef(Task.dest))`. App prints generated value. Production schema generation needs real schema parser and escaping rules, not string interpolation shortcut.

Run `./mill app.run`, repeat `./mill app.generatedSources`, change declared input, rerun. Verify output changed and app recompiles appropriately. Show no-change cache hit via output-file timestamps/signatures, not console log wording. Generated source task rerunning every compile despite unchanged input: suspect hidden nondeterminism or uncached dependency.

OpenAPI/protobuf/SQL/schema generators: model four inputs: source schema, generator version/classpath, configuration/options, referenced schemas. Generated client shared by multiple consumers: separate library module. Published generated APIs need stable package names and compatibility policy, even with small schema. Keep generated sources apart from hand-written files, out of reach of local formatting/refactoring commands.

Resources such as frontend bundle: backend's resource task reads `client.bundle().path`, copies needed output into `Task.dest / "static"`, returns resource directory along with existing resources. That call creates frontend-to-backend packaging edge; shell copy of stale files from sibling `out/` directory does not. Same pattern: generated OpenAPI JSON, configuration summaries without secrets, immutable batch assets.

Content-dependent resource names for cache busting: hash tracked input bytes, generate mapping, output renamed files and mapping from same task. Keep relative path structure; detect collisions instead of flattening filenames. Serve mapping from packaged classpath so runtime matches build artifact.

Application-implemented generator must not depend on application's final `compile` while feeding `generatedSources`. Extract upstream `generator` module; run its compiled tool via subprocess or isolated classloader. Its input schema and tool classpath become consuming task's dependencies. Simple reusable build-time library: header imports can suffice. Classpath conflicts or differing tool versions: isolated workers/subprocesses.

Share conventions as small trait with configurable source paths/options. Do not force generator on modules that do not use it. Dozens of repositories needing same integration: package trait as tested Mill plugin, check binary platform compatibility. Single repository: helper file or meta-build source may beat publishing plugin.

Validate output correctness, stale-output cleanup, repeatability, rebuild boundaries. Test malformed-input failure if generator has relevant validation. Confirm downstream tests run against generated code/resources, not manually checked-in copy. Persistent task destinations need extra stale-file management: old generated classes can survive source removal.

Sources: [Scala generated sources/resources](https://mill-build.org/mill/scalalib/module-config.html), [Kotlin generators/KSP/Kapt](https://mill-build.org/mill/kotlinlib/module-config.html), [web resource examples](https://mill-build.org/mill/scalalib/web-examples.html), [multilanguage resource edges](https://mill-build.org/mill/large/multi-language-builds.html), [tasks](https://mill-build.org/mill/fundamentals/tasks.html).
