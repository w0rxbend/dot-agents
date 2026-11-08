# Actual Mix scaffold and verification

## Preserve identity and scope

[elixir-demo mix.exs](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/mix.exs) defines `ElixirDemo.MixProject`, application `:elixir_demo`, version 0.1.0, `elixir: "~> 1.17"`, logger as extra application and no dependencies. No application `mod` callback. Simple function/example change needs neither OTP supervision tree nor external service. Add either only when behavior needs a lifecycle owner.

Requirement is a lower bound, not an exact 1.17 compiler pin. `~> 1.17` allows 1.17.0 up to, excluding, 2.0.0 under [Elixir version requirement semantics](https://hexdocs.pm/elixir/Version.html). Do not change it to `~> 1.17.0` by accident. Do not use newer-only APIs while claiming unchanged lower bound. Check selected Elixir/OTP pair with `elixir --version` and existing toolchain config. [devcontainer](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/.devcontainer/devcontainer.json) uses floating `latest` image, so file alone does not prove installed versions or a reproducible CI environment.

## Existing naming mismatch

[implementation](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/lib/elixir_demo.ex) defines `ElixirDemo.hello/0` returning `:world`, but its example calls `Example.hello()`. [test](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/test/example_test.exs) also says `doctest Example` and asserts `Example.hello()`. This is source-level scaffold drift. Do not claim reproduced runtime failure without running the test. To repair, keep app identity and align doctest target, example and assertion to actual module. Renaming test module/file is optional consistency work, not the fix by itself.

[README](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/README.md) has generated `example` Hex installation/publication wording. It does not prove a package or HexDocs release exists. If documentation is in scope, update those instructions to observed project identity/usage. Publishing a package is a separate task.

## Existing checks

[.formatter.exs](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/.formatter.exs) covers Mix/formatter files and config/lib/test sources. Verify with `mix format --check-formatted`. Apply intended formatting with `mix format <touched-files>`. [official 1.17.3 formatter task](https://github.com/elixir-lang/elixir/blob/v1.17.3/lib/mix/lib/mix/tasks/format.ex) says check mode does not rewrite failures and output can vary between compiler versions. Do not blanket-reformat unrelated files while fixing namespace.

[test_helper.exs](https://github.com/w0rxbend/elixir-demo/blob/2241aaf3e8851e2a0aae12a398fc6235570a986a/test/test_helper.exs) starts ExUnit. Run `mix test test/example_test.exs` for naming/function change, then `mix test` for full suite. [official 1.17.3 test task](https://github.com/elixir-lang/elixir/blob/v1.17.3/lib/mix/lib/mix/tasks/test.ex) starts application, loads test helper and discovers test files. These commands execute code. Not passive source checks. `mix compile` does not substitute for test collection or doctest assertions.

[official doctest implementation/documentation](https://github.com/elixir-lang/elixir/blob/v1.17.3/lib/ex_unit/lib/ex_unit/doc_test.ex) explains executable documentation examples. Keep doctests enabled. Do not remove them to hide stale module names. A doctest verifies its example, not every API edge case. Use ordinary ExUnit assertions for other meaningful behavior. Repairing `hello/0` in this zero-dependency scaffold needs no routine `mix deps.update --all`, Hex publish, production application start or database migration.
