---
name: rust-linux-apps
description: Develop Rust GTK/Relm4 desktop and Ratatui terminal applications for worxbend Linux tools, preserving system dependencies, UI lifecycle, keyring boundaries, and release targets.
license: MIT
---

# Rust Linux desktop and terminal applications

Before choosing libraries or commands, read Cargo.toml, lockfile, rust-toolchain.toml when present, local instructions, CI, packaging manifests. Match existing edition, MSRV, features, native dependency train, supported targets. Linux distribution packaging is part of app contract. Static-looking CLI and GTK desktop app need different runtime environments.

Read [desktop.md](references/desktop.md) for GTK/Relm4, resources, thread ownership, D-Bus secrets, distribution. Read [terminal.md](references/terminal.md) for Ratatui/Crossterm input, cleanup, text width, bounded async work, meaningful PTY coverage.

Keep domain calculations, config parsing, policy testable outside UI. Send background results through app's existing messages or channels. No blocking network, keyring, disk or terminal reads on GTK main loop or on async executor thread that must stay responsive.

Use repository's actual test gates. Typical desktop gate: `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets --all-features --locked -- -D warnings`, `cargo test --workspace --all-features --locked`. Keep repository-specific feature and target exclusions. Verify changed resources and packaging separately. Report whether graphical, D-Bus, real-terminal, live-service checks actually ran.
