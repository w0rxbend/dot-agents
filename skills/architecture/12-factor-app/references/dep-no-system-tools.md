---
title: Never Rely on Implicit System Tools Being Available
impact: HIGH
impactDescription: ensures portability, prevents deployment failures
tags: dep, system-tools, portability, vendoring
---

## Never Rely on Implicit System Tools Being Available

Twelve-factor app never relies on implicit system tools. ImageMagick, curl or ffmpeg may exist on many systems. No guarantee they exist in production or that their versions are compatible.

**Incorrect (assumes system tools exist):**

```python
import subprocess

def resize_image(input_path, output_path):
    # Assumes ImageMagick is installed
    subprocess.run([
        'convert', input_path,
        '-resize', '800x600',
        output_path
    ])
    # Fails silently or crashes if convert isn't installed
    # Version differences cause unexpected behavior

def fetch_data(url):
    # Assumes curl is installed
    result = subprocess.run(
        ['curl', '-s', url],
        capture_output=True
    )
    return result.stdout
```

**Correct (language libraries or vendored tools):**

```python
# Use a library instead of shelling out
from PIL import Image
import requests

def resize_image(input_path, output_path):
    # Pillow is declared in requirements.txt
    with Image.open(input_path) as img:
        img.thumbnail((800, 600))
        img.save(output_path)

def fetch_data(url):
    # requests is declared in requirements.txt
    response = requests.get(url)
    return response.content
```

**Alternative (vendor the tool):**

```dockerfile
# If you must use a system tool, make it explicit
FROM python:3.11-slim

# Explicitly install required system tools
RUN apt-get update && apt-get install -y \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Third-party image bundling the tool? Review it, pin by digest (image@sha256:...), never :latest
```

Reference: [The Twelve-Factor App - Dependencies](https://12factor.net/dependencies)
