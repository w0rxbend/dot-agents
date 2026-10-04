# Terminal lifecycle and runtime contracts

## Setup and teardown form one owned session

Check interactive-terminal requirements before enabling raw mode. Track which setup steps succeeded; if mouse capture or alternate-screen entry fails, undo the subset already active. On normal exit, runtime errors, and panic unwind, restore cursor/screen/raw mode in the ordering required by the existing adapter. Clear restoration flags only after their undo succeeds, so cleanup is retryable and does not claim a partial restoration was complete. A Drop guard is a last defense, not permission to ignore explicit cleanup failures. See [terminal ownership, partial setup, cleanup, and blocking-read adapter](https://github.com/worxbend/airgradient-cli/blob/938207e0e8b6662f839b9b8f56e38c605946c899/src/tui/runtime/terminal.rs).

Route logs away from stdout while the TUI owns it. CLI JSON/human output remains a separate contract; adding a TUI must not inject diagnostics or ANSI escapes into piped command output. Respect NO_COLOR and the project's terminal-detection behavior.

## Text and geometry

Measure terminal cells and segment grapheme clusters when truncating, centering, scrolling, or masking. Rust byte count, Unicode scalar count, and displayed width differ. Exercise combining marks, wide characters, multi-code-point emoji, ASCII fallback, tiny terminals, and resize. Labels must retain meaning when a Nerd Font icon is absent. Keep the app's documented minimum size and compact-state behavior instead of inventing a new reflow model.

## Async work and shared state

Move blocking `event::poll`/`read` off the async executor. Bound worker/result queues and define the overflow behavior for events that matter; a slow frame renderer should not create unbounded network work. Correlate results with the active operation/session and preserve cancellation and timeout policy.

An atomic rename protects a file from truncation, not two read-modify-write transactions from losing updates. In multistream-manager, the lock is a separate stable file held across load/refresh/save because token JSON is replaced by rename. The reviewed code also guards out-of-range provider expiry values. Preserve token redaction in logs and Debug output. See [OAuth token transaction and expiry handling](https://github.com/worxbend/multistream-manager/blob/e647e8e173c3bf6ed19d15450468b3cee6b735fe/src/auth/store.rs).

For obsctl-rs, IPC path handling requires an absolute validated private socket path, rejects symlink parents, and probes whether a listener is alive before stale-socket removal. Do not replace this with unconditional `remove_file` during startup or teardown. See [socket lifecycle and adversarial path tests](https://github.com/worxbend/obsctl-rs/blob/d5d732c118a1d5c5a5eb94646f6c8d3f6d0985b4/src/ipc/socket_path.rs).

## Validate observable behavior

Use pure model/render tests for state and geometry, fake transport/clock tests for timeout and cancellation, and real PTY tests for binary input/cleanup when available. A skipped PTY test is conditional coverage, not proof the terminal path ran. AirGradient CLI CI records this distinction and uses a test-only refresh hook without changing production interval bounds. Preserve that separation. See [quality gates and PTY coverage reporting](https://github.com/worxbend/airgradient-cli/blob/938207e0e8b6662f839b9b8f56e38c605946c899/.github/workflows/ci.yml).

Keep Crossterm/Ratatui feature versions aligned with the current dependency tree; one app deliberately uses Ratatui's older backend feature to match existing widgets. Do not homogenize all terminal apps to the same latest pair without testing their actual integrations.
