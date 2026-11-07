# Ownership, errors and conditional memory work

## Follow ownership through the API

Borrow when callee only inspects a value; take ownership when it must retain or transfer it. Owned return can be right when output must outlive input; switching to borrowed view changes lifetime and storage requirements. Read consumer before changing `String`/`&str`, `Vec<T>`/`&[T]`, reference or iterator signatures. Clone frequency is a measured cost, not a reason to change observable ownership or add shared synchronization.

For collections, capacity reservation differs from length and initialized elements. Vector growth can move storage; references/raw pointers into its allocation cannot be held across invalidating operations. Setting length does not initialize memory. Prefer safe collection operations. For a justified unsafe fast path, document initialization, valid pointer range, alignment, aliasing and drop ownership. [Vec guarantees](https://doc.rust-lang.org/std/vec/struct.Vec.html).

Keep error information across boundaries. Libraries expose caller-relevant failure categories; CLI entrypoints may add operational context and pick display/exit behavior. `?` propagates compatible errors. Mapping every failure to empty collection, zero or success changes the contract. Documented educational precondition can justify a panic; untrusted file/network/user input usually needs a recoverable path. Align error decisions with source exercise guidance in [workspace-and-learning.md](workspace-and-learning.md).

## Allocators only when the task reaches that boundary

Inspected rust-playground manifests/source have no custom allocator. Do not add one as optimization default. If code implements or selects an allocator, inspect its target, toolchain, failure behavior and ownership API before modifying it.

For a `GlobalAlloc` implementation, keep allocation alignment/layout and matching deallocation; nonzero sizes and overflow bounds matter. After successful reallocation, old pointer is invalid even at unchanged address. On failure, caller still owns old allocation. Allocator hooks must not unwind. Avoid allocating logging or synchronization paths that can recursively call the allocator. Do not assume unused source-level allocation invokes the hook: optimization can remove it, so exact counts are not a safety proof. Use the specific API's allocation/deallocation pair; do not mix global functions with underlying allocator methods. [GlobalAlloc safety and re-entrance](https://doc.rust-lang.org/std/alloc/trait.GlobalAlloc.html).

Rust 2024 warns on unsafe operations in unsafe functions without explicit unsafe blocks. Function's caller precondition and each operation's proof are separate obligations. During migration, use localized blocks with meaningful safety explanation instead of suppressing the lint. [Rust 2024 unsafe-operation change](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html).

Pick tools by invariant: tests for input/output/drop behavior; [Miri](https://github.com/rust-lang/miri#using-miri) when available and supported for relevant unsafe execution; [sanitizer](https://doc.rust-lang.org/unstable-book/compiler-flags/sanitizer.html)/native integration when code depends on FFI or platform allocation; release-mode measurements for performance claims. Tools differ in coverage and cannot certify all thread interleavings or external native code. Keep unsupported targets and unrun checks explicit. Desktop/terminal lifecycle and Linux packaging belong to available `rust-linux-apps` skill when repository is such an application.
