# Workspace, runtime and asynchronous boundaries

## Select the package before selecting the command

Pinned [ops-dashboard root manifest](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/package.json) delegates `build`, `dev` and `preview` only to `homelab-ui`. [UI manifest](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-ui/package.json) uses Solid 1.9, TypeScript 5.8, Vite 6; [backend manifest](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/package.json) uses Hono 4, Node, tsx and `tsc`. Snapshot versions explain existing contracts; they are not an instruction to downgrade another repository. Resolve ranges from current lockfile.

Backend change: existing compile gate is `pnpm --filter homelab-backend run build`. UI change: `pnpm --filter homelab-ui run build` runs `tsc -b && vite build`. Neither package currently declares a test script. Do not report imagined root `pnpm test` or recursive test as verification. Review selected package names and filter output; `--fail-if-no-match` can make an intentionally narrow selection fail instead of silently selecting nothing. Include dependent packages only when their actual dependency or contract changed. See [pnpm filtering](https://pnpm.io/filtering).

Keep workspace's package manager and lockfile. Inspect lifecycle scripts before installs; installation is not necessarily passive metadata processing. Do not silently replace pnpm with npm/yarn or rewrite lockfile for a convenient runner.

## Keep compiler and runtime graphs consistent

[backend tsconfig](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/tsconfig.json) uses `NodeNext`, emits to `dist`. [index.ts](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/src/index.ts) imports `./app.js` from TypeScript source; that extension names emitted Node ESM file. Do not change it to `.ts` merely because source is TypeScript. Do not copy UI's bundler resolution into Node output. Match `package.json`'s `type`, exports and executing runtime. [TypeScript module reference](https://www.typescriptlang.org/docs/handbook/modules/reference.html).

UI's [tsconfig](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-ui/tsconfig.app.json) deliberately uses bundler resolution, DOM libraries, `noEmit`, Solid JSX. Read project references before adding arbitrary compiler arguments: `tsc -b` coordinates referenced projects; standalone `tsc -p` is not the same graph build. [TypeScript project references](https://www.typescriptlang.org/docs/handbook/project-references.html). Vite transpilation alone does not replace typecheck; repository UI build already runs both. [Vite TypeScript support](https://vite.dev/guide/features.html#typescript).

## Hono factory versus server lifecycle

[createApp()](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/src/app.ts) constructs middleware and service/health routes; `index.ts` starts Node listener. Test HTTP contract on factory-created application with `app.request(...)` instead of importing listener and binding port 3001. Check meaningful status/body/header/error behavior and dependency failure cases where applicable. Test actual socket startup separately if change concerns binding, shutdown or Node adaptation. [Hono testing](https://hono.dev/docs/guides/testing).

Validate request bodies/query/configuration at entry. TypeScript type cannot authenticate caller or guarantee JSON shape. Observed permissive CORS middleware does not establish an authorization model. When adding real administrative operations, inspect their actual authentication and authorization design; do not infer one from dashboard name.

## Solid owner and polling behavior

Observed [data hook](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-ui/src/hooks/useHomelabData.ts) starts polling timer on mount, stores signals, marks failed fetch stale, clears timer on cleanup. Keep signal accessors and reactive owner; React dependency-array or rerender assumptions do not apply automatically. Prefer derived values over effects that repeatedly write back into their own dependencies. [Solid effects](https://docs.solidjs.com/concepts/effects).

For polling changes, separate stopping future timer ticks from cancelling an already running request. Decide whether overlapping requests are allowed, how old responses are discarded and whether source supports abort. Meaningful scenarios: slow response reordering, failure then recovery, unmount during request, preventing repeated timers. Register disposal within owning scope; async callbacks must not accidentally create resources without an owner. [Solid cleanup](https://docs.solidjs.com/reference/lifecycle/on-cleanup). Use fake source and controlled time for deterministic lifecycle checks; real homelab access is separate integration boundary.
