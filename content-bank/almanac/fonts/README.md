# Fonts

This directory ships **EB Garamond** (variable, regular + italic) — a free, SIL Open Font Licensed serif that's the recommended default for the almanac aesthetic. The CSS in `base.css` references these files directly.

## Swapping fonts

If you want a different serif:

1. Drop your font files into this folder.
2. Edit the `@font-face` declarations at the top of `../base.css` to point at the new files.
3. Re-run `python3 ../build.py` to regenerate the per-slide HTML (no actual font change happens here, but it's a good sanity check).

Stick to a serif. Sans-serif breaks the encyclopedia aesthetic — the engraving illustration + body copy combination needs the bookishness of a serif to feel cohesive.

## Why EB Garamond

- Free to redistribute (SIL OFL).
- Variable weight + italic in one file each.
- Old-style figures and ligatures match the engraving aesthetic.
- Reads well at both 22px (citations) and 110px (cover titles).

If you want a slightly different feel: Cormorant Garamond, Crimson Text, Source Serif, or Lora are all free alternatives that drop in cleanly. Avoid display serifs (Playfair, Bodoni) — they get noisy at small sizes.
