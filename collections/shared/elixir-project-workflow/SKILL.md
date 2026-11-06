---
name: elixir-project-workflow
description: Edit and verify small Elixir Mix projects (such as w0rxbend/elixir-demo) with ExUnit and doctests, preserving app/module identity, declared runtime compatibility and educational scope; diagnose scaffold naming drift before adding frameworks or release infrastructure.
license: MIT
---

Before editing, read `mix.exs`, source modules, test helper, formatter config and development environment. Keep Mix application and namespace unless requested behavior needs rename. Record Elixir and Erlang/OTP versions when result depends on runtime. Floating container tag is not a reproducible toolchain pin.

For w0rxbend/elixir-demo, use [references/mix-scaffold-contracts.md](references/mix-scaffold-contracts.md): known naming defect, minimum-version semantics, existing validation. That repository is an educational Mix scaffold with no dependencies, supervisor callback or web framework. For other projects, read their own `mix.exs` and tests instead of assuming those facts. Keep changes proportional. Do not add Phoenix, Ecto, database, distributed nodes or release pipeline only because they are common in Elixir.

Trace public behavior through function, documentation example and ExUnit assertion. Doctested examples are executable contracts. Module names in them must resolve to the real module. Fix underlying inconsistency before treating test collection failures as application logic failures.

Choose formatting, compile, focused and full tests to fit the change. Avoid global state or concurrent-test assumptions without inspecting fixture resource ownership. Keep process/port cleanup for examples that introduce them. Report observed failures, exact checked environment and verification done. Planned or unavailable commands are not passing tests.
