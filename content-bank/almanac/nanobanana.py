#!/usr/bin/env python3
"""
STYLE_PREFIX + compose_prompt for almanac illustrations.

This module is the consistency anchor for image generation. Every
illustration prompt is composed as: STYLE_PREFIX + scene description.
Picking the right STYLE_PREFIX once is what makes a whole archive of
carousels look like it came from the same hand.

The prefix is chosen at setup time via brand.config.json's `image_style`
field. Built-in presets:

  - "engraving" (default): black-and-white steel-engraving line art.
                           This is the dhikrlock aesthetic — encyclopedia
                           plate, fine cross-hatching, no color, no faces.
                           Recommended for almost all topic domains; reads
                           as considered and timeless.
  - "minimal-line":        single-weight clean line drawings, more modern,
                           Apple-illustration adjacent.
  - "watercolor":          soft watercolor washes, approachable, gentle.
  - "custom":              read the prefix verbatim from
                           brand.config.json's `custom_style_prefix` field.

The constraints baked into every preset:
  - Pure white background (#FFFFFF) — the CSS multiply blend keys this
    out at render time. ANY non-white background breaks the seamless
    illustration-on-canvas effect.
  - No human faces, no eyes, no portraits. Hands / forearms / feet only,
    never above the wrist or ankle.
  - No text, no captions, no signatures, no watermarks.
  - Single subject, calm composition, centered.

build.py imports compose_prompt() from this module. The agent never edits
this file mid-session — change image_style in brand.config.json instead
and re-run build.py.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRAND_CONFIG_PATH = PROJECT_ROOT / "brand.config.json"


PRESETS = {
    "engraving": (
        "Black-and-white line illustration in a refined steel-engraving / "
        "etching style: pure black ink, fine confident linework, intricate "
        "cross-hatching for tonal depth, no color anywhere, no shading via "
        "gradients. Treat the engraving as a TECHNIQUE only — the subject "
        "itself can be anything modern, contemporary, or historical, "
        "whatever fits the scene description below. Do not force vintage, "
        "antique, or themed visual props into the scene unless the scene "
        "asks for them. The background MUST be plain pure white (#FFFFFF) "
        "with absolutely no tint, no off-white, no paper texture, no "
        "border, no frame, no plate edge, no vignette. The subject sits "
        "isolated as a single focal element, centered, with at most one "
        "small accent prop. No text in the image, no captions, no "
        "signatures, no watermarks, no decorative typography. No human "
        "faces, no eyes, no portraits — hands, forearms, and feet are "
        "acceptable but never above the wrist or ankle. Composition is "
        "calm, clean, uncluttered."
    ),
    "minimal-line": (
        "Minimal single-weight black line illustration: clean confident "
        "strokes, no shading, no cross-hatching, no fill, no color "
        "anywhere. Modern editorial line-art aesthetic. The subject is "
        "drawn as a contour rendering with at most one or two interior "
        "lines for clarity. The background MUST be plain pure white "
        "(#FFFFFF) with absolutely no tint, no off-white, no border, no "
        "frame, no plate edge, no vignette. The subject sits isolated as "
        "a single focal element, centered, with at most one small accent "
        "prop. No text in the image, no captions, no signatures, no "
        "watermarks. No human faces, no eyes, no portraits — hands, "
        "forearms, and feet are acceptable but never above the wrist or "
        "ankle. Composition is calm, clean, uncluttered."
    ),
    "watercolor": (
        "Soft watercolor illustration: gentle washes of muted color, "
        "light pigment bleeds at the edges, subtle paper grain, no hard "
        "outlines, no ink linework. The palette is restrained — earthy "
        "tones, dusty pastels, never saturated. The background MUST be "
        "plain pure white (#FFFFFF) with absolutely no tint, no border, "
        "no frame, no plate edge, no vignette. The subject sits isolated "
        "as a single focal element, centered, with at most one small "
        "accent prop. No text in the image, no captions, no signatures, "
        "no watermarks. No human faces, no eyes, no portraits — hands, "
        "forearms, and feet are acceptable but never above the wrist or "
        "ankle. Composition is calm, clean, uncluttered."
    ),
}


def _load_style_prefix() -> str:
    """Resolve the active STYLE_PREFIX from brand.config.json."""
    if not BRAND_CONFIG_PATH.exists():
        return PRESETS["engraving"]

    cfg = json.loads(BRAND_CONFIG_PATH.read_text())
    style = cfg.get("image_style", "engraving")
    if style == "custom":
        custom = cfg.get("custom_style_prefix", "").strip()
        if custom:
            return custom
        return PRESETS["engraving"]
    return PRESETS.get(style, PRESETS["engraving"])


STYLE_PREFIX = _load_style_prefix()


def compose_prompt(scene: str, aspect_ratio: str = "1:1") -> str:
    """Return the full prompt string sent to the image model."""
    aspect_hint = (
        "Square 1:1 aspect ratio."
        if aspect_ratio == "1:1"
        else f"{aspect_ratio} portrait aspect ratio."
    )
    return f"{STYLE_PREFIX} {aspect_hint} Scene: {scene}"


if __name__ == "__main__":
    print("active style preset:")
    print(STYLE_PREFIX[:240] + ("…" if len(STYLE_PREFIX) > 240 else ""))
