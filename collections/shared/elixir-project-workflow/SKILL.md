---
name: elixir-project-workflow
description: Edit and verify small Elixir Mix projects (such as w0rxbend/elixir-demo) with ExUnit and doctests, preserving app/module identity, declared runtime compatibility and educational scope; diagnose scaffold naming drift before adding frameworks or release infrastructure.
license: MIT
---

Read `mix.exs`, source modules, test helper, formatter config and development environment before editing. Preserve the chosen Mix application and namespace unless the requested behavior needs a rename. Record Elixir and Erlang/OTP versions when a result depends on the runtime; a floating container tag is not a reproducible toolchain pin.

If the repository is w0rxbend/elixir-demo, use [references/mix-scaffold-contracts.md](references/mix-scaffold-contracts.md) for its known naming defect, minimum-version semantics and existing validation; that repository is an educational Mix scaffold without dependencies, a supervisor callback or a web framework. For any other project, read its own `mix.exs` and tests instead of assuming those facts. Keep changes proportional: do not add Phoenix, Ecto, a database, distributed nodes or a release pipeline solely because they are common Elixir patterns.

Trace public behavior through function, documentation example and ExUnit assertion. Executable examples are contracts when doctested; module names inside those examples must resolve to the actual module. Fix the underlying inconsistency before interpreting test collection failures as application logic failures.

Select formatting, compilation, focused tests and full tests according to the change. Avoid global state or concurrent-test assumptions without inspecting the fixture's resource ownership. Preserve process/port cleanup for examples that introduce them. Report observed failures, exact checked environment and verification performed; commands planned or unavailable are not passing tests.
