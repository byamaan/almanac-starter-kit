#!/usr/bin/env python3
"""
Almanac illustration normalizer — trims near-white margins so the subject
fills its PNG canvas at a uniform density.

Why this exists: nano-banana drops the engraved subject anywhere on the
1024x1024 canvas with whatever whitespace it pleases. That gives one
slide a tight subject and the next one a tiny subject floating in white,
which renders as inconsistent visual sizes and big floating gaps in the
final 2160x2700 carousel slide. Cropping to the subject's bounding box
plus a small fixed pad makes every illustration occupy ~roughly the same
visual footprint inside the 620x620 frame.

Idempotent — second run on an already-cropped image is a no-op (within
~1px) because the bbox is already at the canvas edges minus the pad.

Usage:
    # Crop everything in a carousel
    python3 crop.py almanac-01-<slug>

    # Crop everything across every almanac-*/ folder
    python3 crop.py --all

    # Single PNG
    python3 crop.py path/to/illustration.png

The script overwrites in place. Source PNGs from nano-banana are
trivially regenerable from prompts.json so a backup isn't needed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

DIR = Path(__file__).resolve().parent

# Pixels brighter than this in grayscale count as background.
BG_THRESHOLD = 240
# Pad as a fraction of the longer cropped side.
PAD_FRACTION = 0.04


def find_subject_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) bbox of non-background pixels."""
    gray = im.convert("L")
    mask = ImageOps.invert(gray).point(lambda v: 255 if v >= (255 - BG_THRESHOLD) else 0)
    return mask.getbbox()


def normalize(path: Path) -> tuple[bool, str]:
    """Crop to subject bbox + small uniform pad. Overwrites in place."""
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    bbox = find_subject_bbox(im)
    if bbox is None:
        return False, f"{path.name}: blank, skipping"

    l, t, r, b = bbox
    bw, bh = r - l, b - t
    pad = int(round(max(bw, bh) * PAD_FRACTION))

    l2 = max(0, l - pad)
    t2 = max(0, t - pad)
    r2 = min(w, r + pad)
    b2 = min(h, b + pad)

    edge_slack = min(l2, t2, w - r2, h - b2)
    if edge_slack <= max(2, int(0.01 * min(w, h))):
        return False, f"{path.name}: already tight ({l2},{t2}->{r2},{b2})"

    cropped = im.crop((l2, t2, r2, b2))
    cropped.save(path, optimize=True)
    return True, f"{path.name}: {w}x{h} -> {cropped.width}x{cropped.height}"


def gather_pngs(target: Path) -> list[Path]:
    if target.is_file() and target.suffix.lower() == ".png":
        return [target]
    if target.is_dir():
        ill = target / "illustrations"
        if ill.is_dir():
            return sorted(ill.glob("*.png"))
        return sorted(target.glob("*.png"))
    return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*",
                    help="Carousel folder names, absolute paths, or PNG files.")
    ap.add_argument("--all", action="store_true",
                    help="Crop every illustration in every almanac-*/ folder")
    args = ap.parse_args()

    targets: list[Path] = []
    if args.all:
        for d in sorted(DIR.glob("almanac-*/")):
            ill = d / "illustrations"
            if ill.is_dir():
                targets.extend(sorted(ill.glob("*.png")))
    for arg in args.targets:
        p = Path(arg)
        if not p.is_absolute():
            p = DIR / arg
        targets.extend(gather_pngs(p))

    if not targets:
        sys.exit("nothing to crop. pass a carousel folder or --all.")

    n_changed = 0
    for path in targets:
        if path.name.endswith("_thumb.jpeg") or path.stem.endswith("_thumb"):
            continue
        changed, msg = normalize(path)
        print(f"  {msg}")
        if changed:
            n_changed += 1
    print(f"normalized {n_changed} of {len(targets)} files")


if __name__ == "__main__":
    main()
