# GTK, secrets, and Linux distribution

## Match the dependency and system API train

AirGradient desktop uses Relm4 re-exports for GTK, libadwaita, GLib, GIO, and GDK Pixbuf. Adding direct latest gtk-rs crates can produce incompatible types or duplicate native-link families. Its `gnome_45` feature chooses a concrete system API ceiling; raising a Rust feature can raise required installed GTK/libadwaita versions even when Cargo resolves successfully. SceneDeck has its own explicitly coordinated gtk-rs family; apply the ownership convention of the app being edited. See [Relm4 dependency ownership and system ceiling](https://github.com/worxbend/airgradient-desktop/blob/d58f3a291441dbca4dedec24cfd611a46c38514f/Cargo.toml) and [SceneDeck GTK and native dependency configuration](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/Cargo.toml).

Read CI's apt/dnf and pkg-config requirements. Distinguish development libraries used to compile from runtime libraries that users need. Pure unit tests can run without a display, but that does not prove an app starts in a real session. Keep display-dependent ignored/smoke tests separate and record their environment.

## Keep the main loop responsive

Mutate GTK objects on the GLib thread. Run HTTP or blocking work using existing worker/async boundaries, and deliver results as typed messages. Own connection sessions explicitly so reconnect/disconnect tears down polling and event readers together. Guard against a previous session publishing stale results into a newly connected UI. Do not add an independent timer for every view that consumes the same data.

SceneDeck loads synchronous config/keyring data through `spawn_blocking`, owns a Tokio session task, and races event and stats loops so session termination tears both down. Preserve its existing session/operation ordering instead of replacing the controller with direct widget callbacks. See [session orchestration and test seam](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/src/controller/session_controller.rs).

## Keep secrets in the correct store

SceneDeck stores its OBS password in Linux Secret Service, not JSON config. The synchronous keyring backend links system libdbus despite its `crypto-rust` feature name; removing libdbus from CI/packaging without changing the implementation breaks builds. Switching to an async pure-Rust backend is an architectural migration, not dependency cleanup. Surface keyring errors without substituting plaintext persistence. See [password storage boundary](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/src/storage/secret.rs) and its Cargo manifest above.

When editing the [asynchronous settings save](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/src/ui/pages/settings.rs), serialize secret writes and give the latest request ownership of status updates. Two workers may finish out of order. Publish confirmed cached secret state after persistence succeeds, or explicitly roll back an optimistic update on failure. Test failed writes and two rapid edits, checking both stored and displayed state.

## Resources and artifacts

Embedded GResources must rebuild when an SVG or manifest changes. Keep `cargo:rerun-if-changed` declarations complete and write generated files under Cargo OUT_DIR. Check desktop file/app ID/icon/resource names together. See [resource compilation and invalidation](https://github.com/worxbend/airgradient-desktop/blob/d58f3a291441dbca4dedec24cfd611a46c38514f/build.rs).

A successful release binary does not establish a portable AppImage, Flatpak, Snap, deb, or rpm. Read each packaging contract for runtime libraries, architecture, launcher, keyring/session access, and store publishing. Do not announce store availability or signed artifacts merely because the workflow built an archive. Preserve the existing supported target matrix; do not infer Windows/macOS releases from a cross-platform Rust dependency.
