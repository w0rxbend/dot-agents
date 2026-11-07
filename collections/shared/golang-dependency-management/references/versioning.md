# Versioning & Minimal Version Selection

## Semantic Versioning (SemVer)

Go modules use **`vMAJOR.MINOR.PATCH`** (`v` prefix required):

- **MAJOR**: Breaking changes to public API
- **MINOR**: Backward-compatible new functionality
- **PATCH**: Backward-compatible bug fixes

### Stability Rules

| Version     | Stability                                 |
| ----------- | ----------------------------------------- |
| `v0.x.x`    | Unstable — no compatibility guarantees    |
| `v1.x.x`+   | Stable — backward-compatible within major |
| Pre-release | Unstable (e.g., `v1.5.0-beta.1`)          |

### Major Version Suffix Rule

For `v2` and above, module path must include `/vN` suffix. Go's import compatibility rule treats different major versions as entirely separate modules, so they can coexist in one build:

```go
// go.mod
module github.com/example/pkg/v2

// Import in code
import "github.com/example/pkg/v2/subpkg"
```

Tags: `v2.0.0`, `v2.1.0`, etc. `v0` and `v1` have no suffix.

### Special Cases

- **Pseudo-versions**: For untagged commits — `v0.0.0-20210101120000-abcdef123456` (base version + timestamp + commit hash)
- **`+incompatible`**: Marks `v2+` modules that have not adopted `/vN` path convention
- **`gopkg.in`**: Always uses version suffix with dot — `gopkg.in/yaml.v3`

## Minimal Version Selection (MVS)

### How It Works

Most package managers (npm, pip, cargo) pick **latest** compatible version of each dependency. Go instead picks **minimum version that satisfies all requirements**. If module A requires `pkg@v1.2.0` and module B requires `pkg@v1.3.0`, MVS selects `v1.3.0`: highest minimum required, not latest available.

### Why This Design

- **Deterministic without a lock file**: Same `go.mod` inputs always yield same build list; `go.sum` only verifies integrity.
- **High fidelity**: Builds closely match what module authors tested, since MVS picks nearest compatible version, not latest.
- **No solver needed**: Simple graph traversal (under 50 lines of code), not NP-hard constraint satisfaction.

### Upgrades and Downgrades

- **Upgrade**: `go get pkg@v1.5.0` adds edge to `v1.5.0` in graph and reruns MVS. Only minimum necessary changes propagate.
- **Downgrade**: `go get pkg@v1.2.0` removes all versions above `v1.2.0` from graph, then walks back to latest remaining versions of affected dependencies.
