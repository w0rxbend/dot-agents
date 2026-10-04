---
name: rust-linux-apps
description: Develop Rust GTK/Relm4 desktop and Ratatui terminal applications for worxbend Linux tools, preserving system dependencies, UI lifecycle, keyring boundaries, and release targets.
license: MIT
---

# Rust Linux desktop and terminal applications

Read Cargo.toml, the lockfile, rust-toolchain.toml when present, local instructions, CI, and packaging manifests before choosing libraries or commands. Match the existing edition, MSRV, features, native dependency train, and supported targets. Linux distribution packaging is part of the app contract; a static-looking CLI and a GTK desktop application need different runtime environments.

Read [desktop.md](references/desktop.md) for GTK/Relm4, resources, thread ownership, D-Bus secrets, and distribution. Read [terminal.md](references/terminal.md) for Ratatui/Crossterm input, cleanup, text width, bounded async work, and meaningful PTY coverage.

Keep domain calculations, config parsing, and policy testable outside the UI. Send background results through the application's existing messages or channels. Do not perform blocking network, keyring, disk, or terminal reads on the GTK main loop or an async executor thread that must remain responsive.

Use the repository's actual test gates. A representative desktop gate is `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets --all-features --locked -- -D warnings`, and `cargo test --workspace --all-features --locked`; preserve repository-specific feature and target exclusions. Verify changed resources and packaging separately. State whether graphical, D-Bus, real-terminal, and live-service checks actually ran.
