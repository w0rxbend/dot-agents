# GTK, secrets, and Linux distribution

## Match the dependency and system API train

AirGradient desktop uses Relm4 re-exports for GTK, libadwaita, GLib, GIO, GDK Pixbuf. Adding direct latest gtk-rs crates can produce incompatible types or duplicate native-link families. AirGradient desktop's `gnome_45` feature sets concrete system API ceiling. Raising Rust feature can raise required installed GTK/libadwaita versions, even when Cargo resolves. SceneDeck has own explicitly coordinated gtk-rs family. Follow ownership convention of app being edited. See [Relm4 dependency ownership and system ceiling](https://github.com/worxbend/airgradient-desktop/blob/d58f3a291441dbca4dedec24cfd611a46c38514f/Cargo.toml) and [SceneDeck GTK and native dependency configuration](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/Cargo.toml).

Read CI's apt/dnf and pkg-config requirements. Distinguish compile-time development libraries from runtime libraries users need. Pure unit tests run without display. They do not prove app starts in real session. Keep display-dependent ignored/smoke tests separate. Record their environment.

## Keep the main loop responsive

Mutate GTK objects on GLib thread. Run HTTP or blocking work through existing worker/async boundaries. Deliver results as typed messages. Own connection sessions explicitly, so reconnect/disconnect tears down polling and event readers together. Guard against previous session publishing stale results into newly connected UI. Do not add independent timer per view consuming same data.

SceneDeck loads synchronous config/keyring data via `spawn_blocking` and owns Tokio session task. It races event and stats loops, so session termination tears both down. Keep its existing session/operation ordering. Do not replace controller with direct widget callbacks. See [session orchestration and test seam](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/src/controller/session_controller.rs).

## Keep secrets in the correct store

SceneDeck stores OBS password in Linux Secret Service, not JSON config. Synchronous keyring backend links system libdbus despite `crypto-rust` feature name. Removing libdbus from CI/packaging without changing implementation breaks builds. Switching to async pure-Rust backend is architectural migration, not dependency cleanup. Surface keyring errors. Never substitute plaintext persistence. See [password storage boundary](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/src/storage/secret.rs) and its Cargo manifest above.

Editing [asynchronous settings save](https://github.com/worxbend/scenedeck/blob/003d9ba1aa72cdbddb16884c9eb0a8b97704418b/src/ui/pages/settings.rs): serialize secret writes. Give latest request ownership of status updates. Two workers may finish out of order. Publish confirmed cached secret state after persistence succeeds, or explicitly roll back optimistic update on failure. Test failed writes and two rapid edits. Check both stored and displayed state.

## Resources and artifacts

Embedded GResources must rebuild when SVG or manifest changes. Keep `cargo:rerun-if-changed` declarations complete. Write generated files under Cargo OUT_DIR. Check desktop file/app ID/icon/resource names together. See [resource compilation and invalidation](https://github.com/worxbend/airgradient-desktop/blob/d58f3a291441dbca4dedec24cfd611a46c38514f/build.rs).

Successful release binary does not prove portable AppImage, Flatpak, Snap, deb or rpm. Read each packaging contract: runtime libraries, architecture, launcher, keyring/session access, store publishing. Do not announce store availability or signed artifacts merely because workflow built archive. Keep existing supported target matrix. Do not infer Windows/macOS releases from cross-platform Rust dependency.
