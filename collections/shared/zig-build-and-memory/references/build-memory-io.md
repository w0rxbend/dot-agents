# Version-sensitive build, ownership and I/O

## Build graph and test discovery

Reviewed [package metadata](https://github.com/w0rxbend/zig-playground/blob/47345191d6a59dd40a08ce273ad4f8fc08824412/build.zig.zon) declares minimum_zig_version=0.15.2. Its [build graph](https://github.com/w0rxbend/zig-playground/blob/47345191d6a59dd40a08ce273ad4f8fc08824412/build.zig) exposes zig_playground from src/root.zig plus a separate executable root with that named import. Graph uses explicit root_module/createModule APIs, installs executable under selected prefix, forwards b.args after `zig build run --`. Do not transplant older addExecutable root_source_file patterns here.

Test step depends on two addTest/addRunArtifact pairs: library and executable roots. Adding a source file does not prove its tests are discovered; connect its import/declaration reachability and relevant root explicitly. Read optimize/target per module. Do not assume executable's selection automatically changes exposed library's settings. Cross-compilation success does not prove executable ran on that target. See [0.15.2 compilation model](https://ziglang.org/documentation/0.15.2/#Compilation-Model). Use that version's local std source for build APIs; moving online build guide can show newer syntax.

## Allocators and lifetimes

In [main.zig](https://github.com/w0rxbend/zig-playground/blob/47345191d6a59dd40a08ce273ad4f8fc08824412/src/main.zig), ArrayList starts at .empty and allocation/deinit calls take allocator. Matches unmanaged default from [0.15 release changes](https://ziglang.org/download/0.15.1/release-notes.html#ArrayList-make-unmanaged-the-default), not old init(allocator) examples. Use same allocator across allocation's ownership lifetime. Register defer/errdefer cleanup after acquisition. Returning owned memory: transfer cleanup deliberately; do not return slice freed at function exit.

Container growth can invalidate items slices/pointers. Document borrowed views, owned results, arena lifetime. Do not retain list element pointer across append/reallocation, or writer interface backed by expired local buffer. Arena can release whole request's data but must not be destroyed while a consumer still borrows it. Test allocation failure and partial initialization, not only normal cleanup. std.testing.allocator detects leaks in tests but cannot prove all use-after-free paths safe. Follow [Zig ownership guidance](https://ziglang.org/documentation/0.15.2/#Lifetime-and-Ownership).

## Buffered output and fuzzing

[root.zig](https://github.com/w0rxbend/zig-playground/blob/47345191d6a59dd40a08ce273ad4f8fc08824412/src/root.zig) gives std.fs.File.stdout().writer a stack buffer, writes through its interface, propagates flush failure. Preserve explicit successful flush at output boundary. `defer flush() catch {}` hides output failure; buffered print success alone does not mean bytes reached stdout. Keep debug output on stderr so application stdout stays usable by pipes. Follow [versioned I/O migration](https://ziglang.org/download/0.15.1/release-notes.html#Writergate); do not mix old std.io bufferedWriter with this API.

Existing fuzz example deliberately rejects one magic input: discovery is expected demonstration failure, not evidence ordinary tests give complete fuzz coverage. Bound fuzz runs with chosen compiler's supported options. Once failing input exposes real defect, keep it as deterministic regression. Do not delete assertion just to make fuzzing green. Do not claim unbounded fuzz success. Routine validation: `zig fmt --check build.zig src` and `zig build test`. Use native stdout capture for output/flush behavior; report any cross-target execution limitation.
