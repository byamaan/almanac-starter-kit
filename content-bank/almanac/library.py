#!/usr/bin/env python3
"""
Almanac illustration library — reuse engraved illustrations across carousels.

After a few carousels ship, subject vocabulary starts overlapping (lamp,
door, book, hands, etc.). Generating a fresh illustration every time
wastes ~$0.02 per slide and adds noticeable session latency under
Replicate's burst=1 / 6-per-min low-credit rate limit.

This script keeps a flat library of every PNG that has ever shipped in
a carousel, indexed by its scene description, so future carousels can
reuse instead of regenerate.

Usage:
    # Crawl every almanac-NN-<slug>/ folder, copy illustrations to
    # _library/ with deterministic names, write _library/library.json
    python3 library.py index

    # Find candidates for a new scene description (top 3 by default)
    python3 library.py find "A close-up of a single bedside lamp..."

    # Add a freshly-generated illustration to the library
    python3 library.py add path/to/new.png "scene description here" \
        --source almanac-30-foo/04

    # Print library size and a quick subject distribution
    python3 library.py stats

Library layout:
    _library/
        library.json
        almanac-01-<slug>_03.png
        almanac-02-<slug>_04.png
        ...

Filenames are `<carousel-slug>_<slide-id>.png`. They're stable so
multiple `index` runs are idempotent.

Customizing for your domain:
    The SYNONYMS dict below treats word pairs as the same token for
    matching. Add your domain-specific synonyms to improve reuse hit-rate
    (e.g. "weights": "dumbbell", "barbells": "dumbbell" for a fitness
    domain). The defaults stay generic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from collections import Counter

DIR = Path(__file__).resolve().parent
LIBRARY_DIR = DIR / "_library"
MANIFEST = LIBRARY_DIR / "library.json"

# Stop-words filtered out of subject keyword extraction. The locked
# STYLE_PREFIX boilerplate is the dominant noise — these tokens carry
# zero signal about what the subject actually is.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "of", "in", "on", "at", "to",
    "for", "with", "by", "as", "is", "be", "been", "are", "was", "were",
    "this", "that", "these", "those", "it", "its", "from", "into", "onto",
    "over", "under", "no", "not", "single", "small", "large", "big",
    "tight", "tightly", "close-up", "closeup", "centered", "isolated",
    "scene", "composition", "image", "subject", "side", "above", "below",
    "fine", "thin", "delicate", "gentle", "soft", "calm", "clean",
    "uncluttered", "ornate", "simple", "lower", "upper", "middle", "center",
    "bottom", "top", "left", "right", "front", "back",
    "black", "white", "engraving", "etching", "ink", "linework", "line",
    "hatching", "cross-hatching", "crosshatch", "tonal", "depth",
    "color", "shading", "gradients", "technique", "modern", "contemporary",
    "historical", "vintage", "antique", "background",
    "plain", "pure", "tint", "off-white", "paper", "texture", "border",
    "frame", "plate", "edge", "vignette", "focal", "element", "accent",
    "prop", "text", "captions", "signatures", "watermarks", "decorative",
    "typography", "human", "faces", "eyes", "portraits", "hands", "forearms",
    "feet", "wrist", "ankle", "square", "aspect", "ratio", "rectangular",
    "inner", "around", "just", "itself", "fills", "filling",
    "around", "fill", "endto", "end-to-end", "edge-to-edge", "edges",
    "topto", "bottomto", "side-to-side", "sides",
    "view", "viewed", "across", "through", "showing", "shows",
    "crop", "tight", "resting", "lying", "placed", "standing", "leaning",
    "facing", "sitting", "anchored", "spreading", "covering",
    "carved", "bound", "tied", "wrapped", "etched", "engraved", "drawn",
    "marked", "scattered", "arranged", "stacked", "laid", "piled",
    "draped", "hanging", "perched", "open", "closed", "ajar", "shut",
    "wide", "narrow", "broad", "spread", "folded", "rolled", "bent",
    "curved", "straight", "tall", "short", "long", "shaped", "curving",
    "slim", "thick", "thin", "round", "oval", "triangular",
    "behind", "near", "close", "next", "alongside", "together", "alone",
    "tightly", "loosely", "exactly", "perfectly", "beside", "beyond",
    "beneath", "against", "one", "pair", "figure", "low", "surface",
    "ground", "floor", "shoulder", "leg", "tip", "head", "edge",
    "edges", "rims", "tops", "ends", "viewer",
    "second", "third", "fourth", "fifth", "first", "last",
    "larger", "smaller", "biggest", "smallest",
    "leaving", "almost", "any", "each", "few", "some",
    "appears", "appearing", "show", "reveal",
    "between", "either", "still", "outward", "inward", "upward", "downward",
    "vertically", "horizontally", "sized", "scale", "scaled", "fully",
    "filled", "filled-with", "half", "quarter", "much",
    "very", "more", "less", "most", "least",
}

# Word-stem pairs treated as the same token for matching. Add your own
# domain-specific synonyms here to boost library hit-rate. Defaults are
# generic enough to apply across any topic domain.
SYNONYMS = {
    "doors": "door",
    "lamps": "lamp",
    "lanterns": "lamp",
    "lantern": "lamp",
    "candles": "candle",
    "books": "book",
    "rugs": "rug",
    "mats": "mat",
    "carpets": "rug",
    "windows": "window",
    "moons": "moon",
    "crescents": "moon",
    "dawn": "sunrise",
    "sunrises": "sunrise",
    "sunset": "sunrise",
    "doves": "dove",
    "birds": "dove",
    "flowers": "flower",
    "bloom": "flower",
    "petals": "flower",
    "fruits": "fruit",
    "cups": "cup",
    "mugs": "cup",
    "bowls": "bowl",
    "spoons": "spoon",
    "cushions": "cushion",
    "pillows": "cushion",
    "pillow": "cushion",
    "blankets": "blanket",
    "duvets": "blanket",
    "duvet": "blanket",
    "hourglasses": "hourglass",
    "sandglass": "hourglass",
}

WORD_RE = re.compile(r"[a-z][a-z\-']+")


def tokens(text: str) -> set[str]:
    raw = WORD_RE.findall(text.lower())
    out: set[str] = set()
    for t in raw:
        if t in STOP_WORDS:
            continue
        if len(t) < 3:
            continue
        out.add(SYNONYMS.get(t, t))
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {"entries": {}}
    return json.loads(MANIFEST.read_text())


def save_manifest(data: dict) -> None:
    LIBRARY_DIR.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def index_cmd() -> None:
    """Walk every almanac-*/illustrations/*.png and add to the library."""
    LIBRARY_DIR.mkdir(exist_ok=True)
    data = load_manifest()
    pruned = 0
    for fn in list(data["entries"].keys()):
        if not (LIBRARY_DIR / fn).exists():
            del data["entries"][fn]
            pruned += 1
    added = updated = 0

    for carousel_dir in sorted(DIR.glob("almanac-*/")):
        if not carousel_dir.is_dir():
            continue
        slug = carousel_dir.name
        ill_dir = carousel_dir / "illustrations"
        prompts_path = carousel_dir / "prompts.json"
        if not ill_dir.is_dir() or not prompts_path.is_file():
            continue
        try:
            prompts = json.loads(prompts_path.read_text())
        except json.JSONDecodeError:
            print(f"  skip {slug}: prompts.json unreadable")
            continue
        slides = prompts.get("slides", {})

        for png in sorted(ill_dir.glob("*.png")):
            sid = png.stem
            if sid.endswith("_thumb"):
                continue
            slide = slides.get(sid)
            if not slide:
                continue
            scene = slide.get("scene", "").strip()
            if not scene:
                continue
            lib_name = f"{slug}_{sid}.png"
            lib_path = LIBRARY_DIR / lib_name
            existing = data["entries"].get(lib_name)
            existing_hash = existing.get("sha1") if existing else None
            new_hash = hashlib.sha1(png.read_bytes()).hexdigest()
            file_changed = (existing_hash != new_hash) or (not lib_path.exists())
            if file_changed:
                shutil.copy2(png, lib_path)
            kw = sorted(tokens(scene))
            source_id = f"{slug}/{sid}"
            entry = {"scene": scene, "keywords": kw, "sha1": new_hash}
            if existing:
                history = set(existing.get("sources", [])) | {source_id}
                entry["sources"] = sorted(history)
                if file_changed or existing.get("keywords") != kw or existing.get("scene") != scene:
                    updated += 1
            else:
                entry["sources"] = [source_id]
                added += 1
            data["entries"][lib_name] = entry

    save_manifest(data)
    bits = [f"{added} added", f"{updated} updated"]
    if pruned:
        bits.append(f"{pruned} pruned")
    bits.append(f"{len(data['entries'])} total in library")
    print("index: " + ", ".join(bits))


def find_cmd(
    query: str,
    top_k: int = 3,
    exclude: list[str] | None = None,
    exclude_carousel: str | None = None,
) -> list[tuple[str, float, dict]]:
    data = load_manifest()
    q_tokens = tokens(query)
    scored = []
    for fn, entry in data["entries"].items():
        if exclude and fn in exclude:
            continue
        if exclude_carousel and fn.startswith(exclude_carousel + "_"):
            continue
        if not (LIBRARY_DIR / fn).exists():
            continue
        score = jaccard(q_tokens, set(entry.get("keywords", [])))
        scored.append((fn, score, entry))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def add_cmd(png_path: Path, scene: str, source: str | None) -> None:
    LIBRARY_DIR.mkdir(exist_ok=True)
    data = load_manifest()
    if source:
        lib_name = f"{source.replace('/', '_')}.png"
    else:
        lib_name = f"adhoc_{hashlib.sha1(png_path.read_bytes()).hexdigest()[:10]}.png"
    lib_path = LIBRARY_DIR / lib_name
    shutil.copy2(png_path, lib_path)
    kw = sorted(tokens(scene))
    entry = {
        "scene": scene,
        "keywords": kw,
        "sources": [source] if source else [],
        "sha1": hashlib.sha1(png_path.read_bytes()).hexdigest(),
    }
    data["entries"][lib_name] = entry
    save_manifest(data)
    print(f"added {lib_name} ({len(kw)} keywords)")


def stats_cmd() -> None:
    data = load_manifest()
    n = len(data["entries"])
    if not n:
        print("library is empty. run `library.py index` first.")
        return
    counter: Counter[str] = Counter()
    for entry in data["entries"].values():
        for k in entry.get("keywords", []):
            counter[k] += 1
    print(f"library: {n} entries")
    print("top 20 subject keywords:")
    for kw, count in counter.most_common(20):
        print(f"  {count:3d}  {kw}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("index", help="Crawl carousel folders, populate _library/")

    fp = sp.add_parser("find", help="Find library matches for a scene description")
    fp.add_argument("query")
    fp.add_argument("--top", type=int, default=3)
    fp.add_argument("--exclude", action="append", default=[])

    ap2 = sp.add_parser("add", help="Add a new PNG to the library")
    ap2.add_argument("png", type=Path)
    ap2.add_argument("scene")
    ap2.add_argument("--source", help="Source path like almanac-01-foo/04")

    sp.add_parser("stats", help="Print library size and subject distribution")

    args = ap.parse_args()

    if args.cmd == "index":
        index_cmd()
    elif args.cmd == "find":
        results = find_cmd(args.query, top_k=args.top, exclude=args.exclude)
        if not results:
            print("(library empty — run `library.py index` first)")
            return
        for fn, score, entry in results:
            kw = ", ".join(entry.get("keywords", [])[:8])
            sources = ", ".join(entry.get("sources", []))
            print(f"{score:.2f}  {fn}")
            print(f"      keywords: {kw}")
            print(f"      sources:  {sources}")
            print(f"      scene:    {entry.get('scene', '')[:140]}")
    elif args.cmd == "add":
        if not args.png.is_file():
            sys.exit(f"not a file: {args.png}")
        add_cmd(args.png, args.scene, args.source)
    elif args.cmd == "stats":
        stats_cmd()


if __name__ == "__main__":
    main()
