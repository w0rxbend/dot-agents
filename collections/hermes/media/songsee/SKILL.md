---
name: songsee
description: "Audio spectrograms/features (mel, chroma, MFCC) via CLI. Use when the user wants to visualize or analyze an audio file's spectrum or features."
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Audio, Visualization, Spectrogram, Music, Analysis]
    homepage: https://github.com/steipete/songsee
prerequisites:
  commands: [songsee]
---

# songsee

## Prerequisites

Requires [Go](https://go.dev/doc/install). If `songsee` missing, ask user before installing. Pinned tag is verified against sum.golang.org:
```bash
go install github.com/steipete/songsee/cmd/songsee@v0.1.3
```

WAV and MP3 decode natively. Other formats need `ffmpeg`.

## Quick Start

```bash
# Basic spectrogram
songsee track.mp3

# Save to specific file
songsee track.mp3 -o spectrogram.png

# Multi-panel visualization grid
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# Time slice (start at 12.5s, 8s duration)
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg

# From stdin
cat track.mp3 | songsee - --format png -o out.png
```

## Visualization Types

`--viz` takes comma-separated values. Multiple types render as grid in one image.

| Type | Description |
|------|-------------|
| `spectrogram` | Standard frequency spectrogram |
| `mel` | Mel-scaled spectrogram |
| `chroma` | Pitch class distribution |
| `hpss` | Harmonic/percussive separation |
| `selfsim` | Self-similarity matrix |
| `loudness` | Loudness over time |
| `tempogram` | Tempo estimation |
| `mfcc` | Mel-frequency cepstral coefficients |
| `flux` | Spectral flux (onset detection) |

## Common Flags

| Flag | Description |
|------|-------------|
| `--style` | Color palette: `classic`, `magma`, `inferno`, `viridis`, `gray` |
| `--width` / `--height` | Output image dimensions |
| `--window` / `--hop` | FFT window and hop size |
| `--min-freq` / `--max-freq` | Frequency range filter |
| `--start` / `--duration` | Audio time slice |
| `--format` | Output format: `jpg` or `png` |
| `-o` | Output file path |

Inspect output images with `vision_analyze` for automated audio analysis.
