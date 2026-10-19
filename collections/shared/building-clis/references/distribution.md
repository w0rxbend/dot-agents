# CLI Distribution Guide

Guide to packaging and distributing CLIs across platforms and package managers.

## Table of Contents

- [Python Distribution](#python-distribution)
- [Go Distribution](#go-distribution)
- [Rust Distribution](#rust-distribution)
- [Cross-Platform Binary Releases](#cross-platform-binary-releases)

## Python Distribution

### PyPI (Python Package Index)

**Project Structure:**
```
myapp/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── myapp/
│       ├── __init__.py
│       └── cli.py
└── tests/
```

**pyproject.toml:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myapp"
version = "1.0.0"
description = "My CLI application"
readme = "README.md"
license = {file = "LICENSE"}
requires-python = ">=3.8"
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
]

[project.scripts]
myapp = "myapp.cli:app"

[project.urls]
Homepage = "https://github.com/user/myapp"
Repository = "https://github.com/user/myapp"
```

**Build and Publish:**
```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to PyPI
twine upload dist/*

# Or upload to TestPyPI first
twine upload --repository testpypi dist/*
```

**Installation:**
```bash
pip install myapp
```

## Go Distribution

### Homebrew (macOS/Linux)

**Create Formula (myapp.rb):**
```ruby
class Myapp < Formula
  desc "My CLI application"
  homepage "https://github.com/user/myapp"
  url "https://github.com/user/myapp/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "abc123..."  # sha256 of the tarball
  license "MIT"

  depends_on "go" => :build

  def install
    system "go", "build", *std_go_args(ldflags: "-s -w")
  end

  test do
    system "#{bin}/myapp", "--version"
  end
end
```

**Tap Repository:**
```bash
# Create tap repository
mkdir homebrew-tap
cd homebrew-tap
git init
cp myapp.rb Formula/myapp.rb
git add .
git commit -m "Add myapp formula"
git push origin main
```

**Installation:**
```bash
brew tap user/tap
brew install myapp
```

### Go Install

**Direct Installation:**
```bash
go install github.com/user/myapp@latest
```

**Requirements:**
- `go.mod` in repository root
- Main package in `cmd/myapp/` or root

### Binary Releases (GitHub Actions)

**.github/workflows/release.yml:**
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        arch: [amd64, arm64]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Build
        run: |
          GOOS=${{ matrix.os }} GOARCH=${{ matrix.arch }} \
          go build -o myapp-${{ matrix.os }}-${{ matrix.arch }}

      - uses: actions/upload-artifact@v3
        with:
          name: myapp-${{ matrix.os }}-${{ matrix.arch }}
          path: myapp-${{ matrix.os }}-${{ matrix.arch }}*

      - uses: softprops/action-gh-release@v1
        with:
          files: myapp-${{ matrix.os }}-${{ matrix.arch }}*
```

## Rust Distribution

### Cargo Install

**Publish to crates.io:**

**Cargo.toml:**
```toml
[package]
name = "myapp"
version = "1.0.0"
edition = "2021"
license = "MIT"
description = "My CLI application"
repository = "https://github.com/user/myapp"

[[bin]]
name = "myapp"
path = "src/main.rs"

[dependencies]
clap = { version = "4.5", features = ["derive"] }
```

**Publish:**
```bash
# Login to crates.io
cargo login

# Publish
cargo publish
```

**Installation:**
```bash
cargo install myapp
```

### Binary Releases (GitHub Actions)

**.github/workflows/release.yml:**
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: x86_64-unknown-linux-gnu
          - os: ubuntu-latest
            target: aarch64-unknown-linux-gnu
          - os: macos-latest
            target: x86_64-apple-darwin
          - os: macos-latest
            target: aarch64-apple-darwin
          - os: windows-latest
            target: x86_64-pc-windows-msvc

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}

      - name: Build
        run: cargo build --release --target ${{ matrix.target }}

      - name: Package
        run: |
          cd target/${{ matrix.target }}/release
          tar czf myapp-${{ matrix.target }}.tar.gz myapp*

      - uses: softprops/action-gh-release@v1
        with:
          files: target/${{ matrix.target }}/release/myapp-*.tar.gz
```

### Homebrew for Rust

**Formula:**
```ruby
class Myapp < Formula
  desc "My CLI application"
  homepage "https://github.com/user/myapp"
  url "https://github.com/user/myapp/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "abc123..."
  license "MIT"

  depends_on "rust" => :build

  def install
    system "cargo", "install", *std_cargo_args
  end

  test do
    system "#{bin}/myapp", "--version"
  end
end
```

## Cross-Platform Binary Releases

### Using GoReleaser (Go)

**Install:**
```bash
brew install goreleaser
```

**.goreleaser.yaml:**
```yaml
builds:
  - env:
      - CGO_ENABLED=0
    goos:
      - linux
      - darwin
      - windows
    goarch:
      - amd64
      - arm64

archives:
  - format: tar.gz
    name_template: >-
      {{ .ProjectName }}_
      {{- .Version }}_
      {{- .Os }}_
      {{- .Arch }}

brews:
  - name: myapp
    tap:
      owner: user
      name: homebrew-tap
    homepage: "https://github.com/user/myapp"
    description: "My CLI application"
```

**Release:**
```bash
goreleaser release --clean
```

### Using cargo-dist (Rust)

**Install:**
```bash
cargo install cargo-dist
```

**Initialize:**
```bash
cargo dist init
```

**Build:**
```bash
cargo dist build
```

## Installation Scripts

Prefer package managers (Homebrew, Scoop, `cargo install`, `go install`, `pipx`) and signed release archives. If you also ship a shell installer, make it verify what it downloads and avoid requiring root.

### Universal Install Script

**install.sh** (expects release assets named `myapp-<os>-<arch>` plus a `checksums.txt` in `sha256sum` format, as GoReleaser produces):
```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="user/myapp"
BINARY="myapp"
VERSION="${1:?usage: install.sh <version-tag, e.g. v1.2.3>}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

ASSET="${BINARY}-${OS}-${ARCH}"
BASE="https://github.com/$REPO/releases/download/$VERSION"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

curl -fsSL -o "$TMP/$ASSET" "$BASE/$ASSET"
curl -fsSL -o "$TMP/checksums.txt" "$BASE/checksums.txt"

# Verify the binary against the published checksum before installing
(cd "$TMP" && grep " ${ASSET}\$" checksums.txt | sha256sum -c -)   # macOS: shasum -a 256 -c -

mkdir -p "$INSTALL_DIR"
install -m 0755 "$TMP/$ASSET" "$INSTALL_DIR/$BINARY"
echo "Installed $BINARY $VERSION to $INSTALL_DIR (make sure it is on PATH)"
"$INSTALL_DIR/$BINARY" --version
```

Checksums from the same release only protect against corrupted or truncated downloads; for tamper resistance also sign releases (for example cosign or GPG) and verify the signature here.

**Usage** (document this for users; pin a tag and let them read the script first instead of piping a moving branch into a shell):
```bash
curl -fsSLO https://raw.githubusercontent.com/user/myapp/v1.2.3/install.sh
less install.sh                 # review it
bash install.sh v1.2.3
```

## Best Practices

**Versioning:**
- Use semantic versioning (1.0.0)
- Tag releases in git (`v1.0.0`)
- Update version in source code

**Changelog:**
- Maintain CHANGELOG.md
- Document breaking changes
- Include migration guides

**Documentation:**
- Include installation instructions in README
- Document all package managers
- Provide troubleshooting guides

**Testing:**
- Test installation on all supported platforms
- Verify binary compatibility
- Test upgrade paths
