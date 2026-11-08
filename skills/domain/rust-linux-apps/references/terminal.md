# Terminal lifecycle and runtime contracts

## Setup and teardown form one owned session

Check interactive-terminal requirements before enabling raw mode. Track which setup steps succeeded. If mouse capture or alternate-screen entry fails, undo steps already active. On normal exit, runtime errors and panic unwind, restore cursor/screen/raw mode in order existing adapter requires. Clear restoration flags only after their undo succeeds, so cleanup stays retryable and never reports partial restoration as complete. Drop guard is last defense, not permission to ignore explicit cleanup failures. See [terminal ownership, partial setup, cleanup, and blocking-read adapter](https://github.com/worxbend/airgradient-cli/blob/938207e0e8b6662f839b9b8f56e38c605946c899/src/tui/runtime/terminal.rs).

Route logs away from stdout while TUI owns it. CLI JSON/human output is separate contract. TUI must not inject diagnostics or ANSI escapes into piped command output. Respect NO_COLOR and project's terminal-detection behavior.

## Text and geometry

Measure terminal cells and segment grapheme clusters when truncating, centering, scrolling or masking. Rust byte count, Unicode scalar count and displayed width differ. Test combining marks, wide characters, multi-code-point emoji, ASCII fallback, tiny terminals, resize. Labels must keep meaning without Nerd Font icon. Keep app's documented minimum size and compact-state behavior. Do not invent new reflow model.

## Async work and shared state

Move blocking `event::poll`/`read` off async executor. Bound worker/result queues. Define overflow behavior for events that matter. Slow frame renderer should not create unbounded network work. Correlate results with active operation/session. Keep cancellation and timeout policy.

Atomic rename prevents file truncation, not lost updates between two read-modify-write transactions. multistream-manager holds lock on separate stable file across load/refresh/save, because rename replaces token JSON. Reviewed code also guards out-of-range provider expiry values. Keep token redaction in logs and Debug output. See [OAuth token transaction and expiry handling](https://github.com/worxbend/multistream-manager/blob/e647e8e173c3bf6ed19d15450468b3cee6b735fe/src/auth/store.rs).

obsctl-rs IPC path handling requires absolute validated private socket path and rejects symlink parents. It probes listener liveness before stale-socket removal. Do not replace this with unconditional `remove_file` at startup or teardown. See [socket lifecycle and adversarial path tests](https://github.com/worxbend/obsctl-rs/blob/d5d732c118a1d5c5a5eb94646f6c8d3f6d0985b4/src/ipc/socket_path.rs).

## Validate observable behavior

Use pure model/render tests for state and geometry. Use fake transport/clock tests for timeout and cancellation. Use real PTY tests for binary input/cleanup when available. Skipped PTY test is conditional coverage, not proof terminal path ran. AirGradient CLI CI records this distinction. It uses test-only refresh hook without changing production interval bounds. Keep that separation. See [quality gates and PTY coverage reporting](https://github.com/worxbend/airgradient-cli/blob/938207e0e8b6662f839b9b8f56e38c605946c899/.github/workflows/ci.yml).

Keep Crossterm/Ratatui feature versions aligned with current dependency tree. One app deliberately uses Ratatui's older backend feature to match existing widgets. Do not force all terminal apps onto same latest pair without testing their actual integrations.
