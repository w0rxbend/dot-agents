# Actual Mix scaffold and verification

## Preserve identity and scope

[elixir-demo mix.exs](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/mix.exs) defines `ElixirDemo.MixProject`, application `:elixir_demo`, version 0.1.0, `elixir: "~> 1.17"`, logger as an extra application and an empty dependency list. There is no application `mod` callback. A simple function/example change needs neither an OTP supervision tree nor an external service. Add either only for behavior requiring a lifecycle owner.

The requirement is a lower compatibility bound, not an exact 1.17 compiler pin: `~> 1.17` permits versions from 1.17.0 up to, excluding, 2.0.0 under [Elixir version requirement semantics](https://hexdocs.pm/elixir/Version.html). Do not change it to `~> 1.17.0` accidentally, and do not use newer-only APIs while claiming the unchanged lower bound. Inspect the selected Elixir/OTP pair with `elixir --version` and existing toolchain configuration. The [devcontainer](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/.devcontainer/devcontainer.json) uses a floating `latest` image, so the file alone does not prove its actual installed versions or a reproducible CI environment.

## Existing naming mismatch

The [implementation](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/lib/elixir_demo.ex) defines `ElixirDemo.hello/0` returning `:world`, but its example calls `Example.hello()`. The [test](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/test/example_test.exs) also says `doctest Example` and asserts `Example.hello()`. This is source-level scaffold drift; do not claim a runtime failure was reproduced without executing the test. Keep the app identity and align doctest target, example and assertion to the actual module when repairing this defect. Renaming the test module/file is optional consistency work, not the fix by itself.

The [README](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/README.md) contains generated `example` Hex installation/publication wording. It does not establish that a package or HexDocs release exists. Update such instructions to observed project identity/usage if documentation is in scope; publishing a package is a separate task.

## Existing checks

[.formatter.exs](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/.formatter.exs) covers Mix/formatter files and config/lib/test sources. Use `mix format --check-formatted` for verification and `mix format <touched-files>` to apply intended formatting. The [official 1.17.3 formatter task](https://github.com/elixir-lang/elixir/blob/v1.17.3/lib/mix/lib/mix/tasks/format.ex) documents that check mode does not rewrite failures and output can vary between compiler versions. Do not blanket-reformat unrelated files while fixing the namespace.

[test_helper.exs](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/test/test_helper.exs) starts ExUnit. Use `mix test test/example_test.exs` for the naming/function change, followed by `mix test` for the complete small suite. The [official 1.17.3 test task](https://github.com/elixir-lang/elixir/blob/v1.17.3/lib/mix/lib/mix/tasks/test.ex) starts the application, loads its test helper and discovers test files. These commands execute code; they are not passive source checks. `mix compile` does not substitute for test collection or doctest assertions.

The [official doctest implementation/documentation](https://github.com/elixir-lang/elixir/blob/v1.17.3/lib/ex_unit/lib/ex_unit/doc_test.ex) explains executable documentation examples. Keep doctests enabled rather than removing them to hide stale module names. A doctest verifies its example, not all edge cases of an API; use ordinary ExUnit assertions for additional meaningful behavior. This zero-dependency scaffold needs no routine `mix deps.update --all`, Hex publish, production application start or database migration to repair `hello/0`.
