#!/usr/bin/env python3
"""
Image Optimization Script

Optimizes images for web delivery by:
- Resizing to multiple widths (never upscaling)
- Converting to modern formats (WebP, AVIF) and/or JPEG/PNG
- Compressing with a quality setting
- Printing a srcset string per source image

Requires Pillow (pip install Pillow). AVIF output needs Pillow 11.2+ built with
AVIF support (or the pillow-avif-plugin package); unsupported formats are skipped
with a warning.

Usage:
    python scripts/optimize_images.py --input images/ --output optimized/ \
        --quality 80 --formats webp,jpg --sizes 400,800,1200
    python scripts/optimize_images.py --input photo.jpg --formats webp,avif
"""

import argparse
import sys
from pathlib import Path

SOURCE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
PIL_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP", "avif": "AVIF"}


def find_sources(input_path: Path):
    if input_path.is_file():
        return [input_path]
    return sorted(p for p in input_path.rglob("*") if p.suffix.lower() in SOURCE_SUFFIXES)


def supported_formats(formats):
    from PIL import features
    ok = []
    for fmt in formats:
        if fmt not in PIL_FORMATS:
            print(f"warning: unknown format '{fmt}', skipping", file=sys.stderr)
        elif fmt in ("webp", "avif") and not features.check(fmt):
            print(f"warning: this Pillow build cannot write {fmt}, skipping", file=sys.stderr)
        else:
            ok.append(fmt)
    return ok


def optimize_image(src: Path, output_dir: Path, quality: int, formats, sizes):
    from PIL import Image, ImageOps

    written = []
    with Image.open(src) as opened:
        img = ImageOps.exif_transpose(opened)  # apply camera rotation
        widths = sorted({w for w in sizes if w < img.width} | {min(max(sizes), img.width)})
        for width in widths:
            height = round(img.height * width / img.width)
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            for fmt in formats:
                frame = resized
                if PIL_FORMATS[fmt] == "JPEG" and frame.mode not in ("RGB", "L"):
                    frame = frame.convert("RGB")  # JPEG has no alpha
                out = output_dir / f"{src.stem}-{width}w.{fmt}"
                options = {"optimize": True} if PIL_FORMATS[fmt] in ("JPEG", "PNG") else {}
                if PIL_FORMATS[fmt] != "PNG":
                    options["quality"] = quality
                frame.save(out, PIL_FORMATS[fmt], **options)
                written.append((fmt, width, out))
    return written


def main():
    parser = argparse.ArgumentParser(description="Optimize images for web delivery")
    parser.add_argument("--input", required=True, help="Input image file or directory")
    parser.add_argument("--output", default="./optimized", help="Output directory")
    parser.add_argument("--quality", type=int, default=80, help="Quality 1-100 (JPEG/WebP/AVIF)")
    parser.add_argument("--formats", default="webp,jpg", help="Comma-separated: webp,avif,jpg,png")
    parser.add_argument("--sizes", default="400,800,1200,1600", help="Comma-separated target widths")
    args = parser.parse_args()

    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit("Error: Pillow is required (pip install Pillow)")

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Error: {input_path} does not exist")
    if not 1 <= args.quality <= 100:
        sys.exit("Error: --quality must be between 1 and 100")

    formats = supported_formats([f.strip().lower() for f in args.formats.split(",") if f.strip()])
    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    if not formats or not sizes:
        sys.exit("Error: need at least one supported format and one size")

    sources = find_sources(input_path)
    if not sources:
        sys.exit(f"Error: no images found under {input_path}")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_in = total_out = 0
    for src in sources:
        written = optimize_image(src, output_dir, args.quality, formats, sizes)
        total_in += src.stat().st_size
        for fmt in formats:
            srcset = ", ".join(f"{out.name} {w}w" for f, w, out in written if f == fmt)
            print(f"{src.name} [{fmt}] srcset: {srcset}")
        total_out += sum(out.stat().st_size for _, _, out in written)

    print(f"\nProcessed {len(sources)} image(s): {total_in / 1024:.0f} KB in, "
          f"{total_out / 1024:.0f} KB written to {output_dir}")


if __name__ == "__main__":
    main()
