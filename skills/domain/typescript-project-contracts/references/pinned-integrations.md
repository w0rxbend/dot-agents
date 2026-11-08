# Pinned editor and rendering integrations

## Archived coc.nvim extension

Pinned [coc-crystal-experimental manifest](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/package.json) belongs to archived extension. It declares TypeScript 4.3.4, webpack 5.40, coc.nvim 0.0.80, a coc engine range and `lib/index.js` as delivered entrypoint. [webpack configuration](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/webpack.config.js) targets Node/CommonJS, leaves `coc.nvim` external. Keep that host-provided dependency and packaging shape in bounded maintenance fix. Modern browser bundler defaults, Node-only TypeScript execution or new coc APIs may not match supported host.

Trace configuration across contributed schema and [activation source](https://github.com/w0rxbend/coc-crystal-experimental/blob/b154aa3feedb70ee29c50af1abc45cca323a9e9f/src/index.ts). Manifest publishes `crystal.enabled`; observed source reads `config.enable`. Resolve that compatibility question when fixing enable/disable behavior; it is not permission to rewrite all options. Server setting, file selector/watcher, start readiness/error path and disposal subscription are also integration contracts. Verify executable configuration before starting a process. Do not turn an arbitrary configured command into a shell string.

Existing `build` runs webpack; `prepare` runs clean/build through npx. Build can verify bundle shape but cannot prove activation, settings or Scry communication inside coc.nvim. Editor integration check needs suitable installed host/server and requested maintenance scope. Keep archive status and existing release/distribution behavior unless task asks to revive it. No test script observed.

## Pixi browser sources

Archived [obs-effects manifest](https://github.com/w0rxbend/obs-effects/blob/ad8d6fd8767c7bd90a9746b076c80797cf53c46d/package.json) has Pixi 8.19, TypeScript 6, Vite 8 and a Spine Pixi-v8 adapter. Its build already combines lint, metadata validation, TypeScript and Vite. Keep that train; do not borrow dashboard's Solid/TS5/Vite6 configuration. Use lockfile's resolved versions and package-compatible docs for rendering APIs and adapters.

Pixi 8 initializes `Application` asynchronously; attach scenes/assets only after initialization. Teardown must respect ownership of ticker subscriptions, media, event listeners and shared textures. Passing TypeScript build or effects-metadata test does not prove transparent rendering, visibility suspension, browser-source navigation or audio behavior in OBS. [Pixi v8 migration guide](https://pixijs.com/8.x/guides/migrations/v8) explains API-generation boundary. Use installed Pixi specialist skills for detailed rendering work, and streaming integration guidance when failing boundary is OBS/Twitch/event transport.

For change spanning backend event and scene renderer, inspect both wire decoding and consuming scene. Keep unknown-event behavior; do not cast malformed messages into domain types. Scope browser tests to changed lifecycle or rendering contract; state whether actual OBS integration ran. Do not introduce framework/toolchain migration as side effect of archived integration repair.
