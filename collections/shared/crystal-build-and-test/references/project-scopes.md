# Distinct repository scopes

## Crystal playground

[cr-code-playground shard.yml](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/shard.yml) declares historical `crystal: 0.31.1`, no dependency list, and the executable target `starter` at `src/main.cr`. Recheck the current requirement and compiler rather than claiming this old declaration pins the workstation's compiler exactly.

The [entrypoint](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/src/main.cr) compares streamed `to_s(io)` output against intermediate-string construction with `Benchmark.ips`. It creates/clears an IO::Memory buffer and runs measurements at top level. Preserve equivalent output and buffer reset while measuring allocation/performance; repeated buffer growth would confound the comparison. Compilation alone does not measure speed.

The [spec helper](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/spec/spec_helper.cr) only requires `spec`; its source require is commented out. The [existing spec](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/spec/cr-code-playground_spec.cr) asserts `false == false`. It never exercises MyClass. For a formatting/serialization change, verify the actual IO output through a reusable definitions file or isolated fixture, rather than treating this scaffold assertion as coverage or importing a benchmark-running entrypoint indiscriminately. Its [Travis file](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/.travis.yml) comments out the explicit spec/format script; inspect active CI instead of advertising a configured gate.

## Crystal editor integration is TypeScript

[coc-crystal-experimental package.json](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/package.json) builds with webpack and has a `prepare` script that cleans/builds output. It is a coc.nvim extension, not a shard. Use the checked-out package manager and reviewed lifecycle scripts; do not invoke `shards` as its build gate or invent an npm test script.

[Activation code](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/src/index.ts) launches configured Scry, selects Crystal file documents and registers the client disposable. The schema exposes `crystal.enabled` while this snapshot reads `config.enable`; a disable-switch request must trace that mismatch. Preserve the documented key and intentional compatibility, executable validation, start-failure reporting and disposal. A mocked activation test can prove these without spawning Scry or editing live editor settings. [Webpack](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/webpack.config.js) externalizes coc.nvim and emits CommonJS `lib/index.js`; preserve the host boundary.

## Workstation setup

Ubuntu-bootstrap's [apps profile](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/profiles/10-apps.yaml) owns the classic Crystal snap, which supplies Shards. Its [apps assertions](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/tests/assertions/apps.sh) verify compiler/version/PATH and explicitly skip snap checks in containers. Keep `/usr/bin` apt packages from shadowing the selected snap; first inspect executable resolution, not a generic “reinstall Crystal” recipe. These are Bash/YAML workstation contracts, not Crystal source.

The [bootstrap README](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/README.md) documents isolated/generated profile checks and build-only steps for a separate fluxion.cr checkout. Do not conflate `shards install`/building that binary with running bootstrap phases. Fixture success with container snap skips is not proof that the host compiler is installed or selected correctly.
