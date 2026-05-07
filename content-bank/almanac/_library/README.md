# Illustration library

This folder stores every illustration that's ever shipped in one of your almanac carousels, indexed by its scene description. When the skill drafts a new carousel, it runs `library.py find "<scene>"` for each non-CTA slide before calling Replicate. If the top match scores ≥ 0.30 Jaccard similarity, it reuses that PNG instead of generating a new one.

The library starts empty. It grows automatically as you ship carousels.

## Commands

```bash
cd ../   # move to content-bank/almanac/

# Crawl every almanac-NN-<slug>/ folder, copy illustrations into _library/, write library.json
python3 library.py index

# Find candidates for a new scene description (top 3 by default)
python3 library.py find "A close-up of a single bedside lamp..."

# Manually add a PNG to the library
python3 library.py add path/to/illustration.png "scene description here" --source almanac-01-foo/04

# Print library size + top subject keywords
python3 library.py stats
```

## Why it matters

Replicate charges ~$0.02 per generation and the low-credit tier rate-limits you to 6 requests/min. After 5–10 carousels, subject vocabulary repeats often enough that library reuse cuts ~30–40% of generation cost and time. The `crop.py` step on the original PNG means a reused illustration is already normalized for visual consistency.

## Files

- `library.json` — manifest mapping each library filename to its scene + extracted keywords + source provenance + sha1.
- `<carousel-slug>_<slide-id>.png` — the actual PNG files. One per indexed illustration.

The folder is checked into git so the kit ships the library state across collaborators.
