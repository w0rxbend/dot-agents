# Workspace, runtime and asynchronous boundaries

## Select the package before selecting the command

The pinned [ops-dashboard root manifest](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/package.json) delegates `build`, `dev`, and `preview` only to `homelab-ui`. Its [UI manifest](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-ui/package.json) uses Solid 1.9, TypeScript 5.8 and Vite 6; its [backend manifest](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/package.json) uses Hono 4, Node, tsx and `tsc`. These snapshot versions explain existing contracts, not an instruction to downgrade another repository. Resolve ranges from the current lockfile.

For a backend change, the existing compile gate is `pnpm --filter homelab-backend run build`; for a UI change, `pnpm --filter homelab-ui run build` runs `tsc -b && vite build`. Neither package currently declares a test script. Do not report an imagined root `pnpm test` or recursive test as verification. Review the selected package names and filter output; `--fail-if-no-match` can make an intentionally narrow selection fail instead of silently selecting nothing. Include dependent packages only when their actual dependency or contract changed. See [pnpm filtering](https://pnpm.io/filtering).

Preserve the workspace's package manager and lockfile. Before running installs, inspect lifecycle scripts: installation is not necessarily passive metadata processing. Do not silently replace pnpm with npm/yarn or rewrite the lockfile to obtain a convenient runner.

## Keep compiler and runtime graphs consistent

The [backend tsconfig](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/tsconfig.json) uses `NodeNext` and emits to `dist`; [index.ts](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/src/index.ts) imports `./app.js` from TypeScript source. That extension describes the emitted Node ESM file. Do not change it to `.ts` merely because the source file is TypeScript, or copy the UI's bundler resolution into Node output. Match `package.json`'s `type`, exports and the executing runtime. [TypeScript module reference](https://www.typescriptlang.org/docs/handbook/modules/reference.html).

The UI's [tsconfig](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-ui/tsconfig.app.json) deliberately uses bundler resolution, DOM libraries, `noEmit`, and Solid JSX. Read project references before adding arbitrary compiler arguments: `tsc -b` coordinates referenced projects, whereas a standalone `tsc -p` is not the same graph build. [TypeScript project references](https://www.typescriptlang.org/docs/handbook/project-references.html). Vite transpilation alone does not replace a typecheck; the repository's UI build already runs both. [Vite TypeScript support](https://vite.dev/guide/features.html#typescript).

## Hono factory versus server lifecycle

[createApp()](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-backend/src/app.ts) constructs middleware and service/health routes; `index.ts` starts the Node listener. Test an HTTP contract against a factory-created application with `app.request(...)` instead of importing the listener and binding port 3001. Check meaningful status/body/header/error behavior and dependency failure cases where applicable. Test actual socket startup separately if the change concerns binding, shutdown or Node adaptation. [Hono testing](https://hono.dev/docs/guides/testing).

Validate request bodies/query/configuration at entry. A TypeScript type cannot authenticate a caller or guarantee JSON shape. The observed permissive CORS middleware does not establish an authorization model. If adding real administrative operations, inspect their actual authentication and authorization design rather than infer one from the dashboard name.

## Solid owner and polling behavior

The observed [data hook](https://github.com/w0rxbend/ops-dashboard/blob/a4f74b9b209ea898482b850fc35b3b23ec2c9431/homelab-ui/src/hooks/useHomelabData.ts) starts a polling timer on mount, stores signals, marks a failed fetch stale, and clears the timer on cleanup. Preserve signal accessors and the reactive owner; React dependency-array or rerender assumptions do not apply automatically. Prefer derived values over effects that repeatedly write back into their own dependencies. [Solid effects](https://docs.solidjs.com/concepts/effects).

For polling changes, distinguish stopping future timer ticks from cancelling an already running request. Decide whether overlapping requests are allowed, how old responses are discarded, and whether the source supports abort. Meaningful scenarios include slow response reordering, failure followed by recovery, unmount during a request, and preventing repeated timers. Register disposal within the owning scope; asynchronous callbacks must not accidentally create resources without an owner. [Solid cleanup](https://docs.solidjs.com/reference/lifecycle/on-cleanup). Use a fake source and controlled time for deterministic lifecycle checks; real homelab access is a separate integration boundary.
