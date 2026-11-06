# Distinct repository scopes

## Crystal playground

[cr-code-playground shard.yml](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/shard.yml) declares historical `crystal: 0.31.1`, no dependency list, and executable target `starter` at `src/main.cr`. Recheck current requirement and compiler; do not claim this old declaration pins workstation compiler exactly.

[Entrypoint](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/src/main.cr) compares streamed `to_s(io)` output against intermediate-string construction with `Benchmark.ips`. It creates/clears IO::Memory buffer and measures at top level. When measuring allocation/performance, preserve equivalent output and buffer reset; repeated buffer growth would confound comparison. Compilation alone does not measure speed.

[Spec helper](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/spec/spec_helper.cr) only requires `spec`; source require is commented out. [Existing spec](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/spec/cr-code-playground_spec.cr) asserts `false == false`, never exercising MyClass. For formatting/serialization change, verify actual IO output via reusable definitions file or isolated fixture; do not treat this scaffold assertion as coverage or import benchmark-running entrypoint indiscriminately. Playground's [Travis file](https://github.com/w0rxbend/cr-code-playground/blob/5427e3dda8c8b705afb40364179a02cad4f297fd/.travis.yml) comments out explicit spec/format script; inspect active CI instead of advertising configured gate.

## Crystal editor integration is TypeScript

[coc-crystal-experimental package.json](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/package.json) builds with webpack; its `prepare` script cleans/builds output. It is coc.nvim extension, not shard. Use checked-out package manager and reviewed lifecycle scripts. Do not invoke `shards` as its build gate. Do not invent npm test script.

[Activation code](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/src/index.ts) launches configured Scry, selects Crystal file documents, registers client disposable. Schema exposes `crystal.enabled`, but this snapshot reads `config.enable`; disable-switch request must trace that mismatch. Preserve documented key and intentional compatibility, executable validation, start-failure reporting and disposal. Mocked activation test can prove these without spawning Scry or editing live editor settings. [Webpack](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/webpack.config.js) externalizes coc.nvim and emits CommonJS `lib/index.js`; preserve host boundary.

## Workstation setup

Ubuntu-bootstrap's [apps profile](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/profiles/10-apps.yaml) owns classic Crystal snap, which supplies Shards. Its [apps assertions](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/tests/assertions/apps.sh) verify compiler/version/PATH and explicitly skip snap checks in containers. Keep `/usr/bin` apt packages from shadowing selected snap. Inspect executable resolution first, not generic “reinstall Crystal” recipe. These are Bash/YAML workstation contracts, not Crystal source.

[Bootstrap README](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/README.md) documents isolated/generated profile checks and build-only steps for separate fluxion.cr checkout. Do not conflate `shards install`/building that binary with running bootstrap phases. Fixture success with container snap skips does not prove host compiler is installed or selected correctly.
