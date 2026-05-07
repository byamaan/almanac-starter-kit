#!/usr/bin/env python3
"""
Almanac carousel builder — manifest-per-folder edition.

Walks every `almanac-NN-<slug>/` folder under this directory, reads its
`manifest.json`, and writes:
  - per-slide HTML files
  - prompts.json (image-gen batch input, excludes CTA)
  - captions.txt (TikTok title + IG caption)

Also writes `theme.css` next to base.css from `brand.config.json` (palette +
accent color). Rerun any time you edit a manifest or the brand config.

Manifest shape (one per carousel folder, file name `manifest.json`):

    {
      "title": "<TikTok title — no trailing period>",
      "caption": "<full IG caption with line breaks and hashtags>",
      "variant": "cream" | "deep" | "midnight",
      "accent": null | "purple",
      "slides": [
        {"id": "01", "type": "cover", "title": "...", "scene": "..."},
        {"id": "02", "type": "step",  "title": "...", "body": [...],
         "arabic": "...", "reference": "...", "scene": "..."},
        {"id": "07", "type": "cta",   "title": "Follow For More."}
      ]
    }
"""
from __future__ import annotations

import html as html_mod
import json
import sys
from pathlib import Path

from nanobanana import compose_prompt  # STYLE_PREFIX is the consistency anchor

DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DIR.parents[1]                   # .../<project>/content-bank/almanac/ → <project>/
BRAND_CONFIG_PATH = PROJECT_ROOT / "brand.config.json"
THEME_CSS_PATH = DIR / "theme.css"

VARIANTS = {"cream", "deep", "midnight"}


def load_brand_config() -> dict:
    if not BRAND_CONFIG_PATH.exists():
        sys.exit(
            "brand.config.json not found at project root.\n"
            "Run the almanac-carousel skill in Claude Code — it walks the\n"
            "first-run setup interview and writes this file. Or copy\n"
            "brand.config.example.json to brand.config.json and edit it."
        )
    return json.loads(BRAND_CONFIG_PATH.read_text())


def emit_theme_css(config: dict) -> str:
    palette = config["palette"]
    accent = config.get("accent_color", "#7B68EE")
    return f"""/* Auto-generated from brand.config.json — do not edit by hand. */
:root, body {{
  --bg: {palette["cream"]["bg"]};
  --ink: {palette["cream"]["ink"]};
  --illust-blend: multiply;
  --illust-filter: none;
}}

body.variant-deep {{
  --bg: {palette["deep"]["bg"]};
  --ink: {palette["deep"]["ink"]};
  --illust-blend: screen;
  --illust-filter: invert(1);
}}

body.variant-midnight {{
  --bg: {palette["midnight"]["bg"]};
  --ink: {palette["midnight"]["ink"]};
  --illust-blend: screen;
  --illust-filter: invert(1);
}}

.rule {{ background: {accent}; }}
.stage.accent-purple .rule {{ display: block; }}
.stage.accent-purple .handle {{ color: {accent}; }}
"""


def render_body_block(slide: dict) -> str:
    """Compose the body region for a step slide. Empty string if nothing set."""
    arabic = slide.get("arabic")
    body = slide.get("body")
    reference = slide.get("reference")

    parts: list[str] = []
    if arabic:
        quoted = f"“{html_mod.escape(arabic)}”"
        parts.append(f'    <div class="arabic">{quoted}</div>')

    if body:
        lines = [body] if isinstance(body, str) else list(body)
        paras = "\n".join(f"      <p>{html_mod.escape(line)}</p>" for line in lines)
        parts.append(f'    <div class="lines">\n{paras}\n    </div>')

    if reference:
        parts.append(f'    <div class="ref">{html_mod.escape(reference)}</div>')

    if not parts:
        return ""
    return f'  <div class="body">\n' + "\n".join(parts) + "\n  </div>"


def slide_html(slide: dict, accent: str | None, variant: str, handle: str) -> str:
    slide_id = slide["id"]
    slide_type = slide["type"]
    title = html_mod.escape(slide["title"])
    img_src = f"illustrations/{slide_id}.png"

    classes = ["stage", slide_type]
    if accent == "purple":
        classes.append("accent-purple")
    stage_cls = " ".join(classes)
    body_cls = f"variant-{variant}" if variant != "cream" else ""

    body_block = render_body_block(slide) if slide_type == "step" else ""
    rule_block = '  <div class="rule"></div>' if accent == "purple" else ""
    frame_block = (
        f'  <div class="frame"><img src="{img_src}" alt=""/></div>'
        if slide_type != "cta" else ""
    )
    swipe_block = '  <div class="swipe-hint">swipe →</div>' if slide_type == "cover" else ""
    handle_html = html_mod.escape(handle)

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="../base.css"/>
  <link rel="stylesheet" href="../theme.css"/>
</head>
<body class="{body_cls}">
<div class="{stage_cls}">
  <div class="title">{title}</div>
{rule_block}
{frame_block}
{body_block}
{swipe_block}
  <div class="handle">{handle_html}</div>
</div>
</body>
</html>
"""


def slide_type_suffix(slide: dict) -> str:
    """Filename-safe slug derived from the slide title."""
    title = slide["title"].lower().rstrip(".")
    cleaned = "".join(c if c.isalnum() else "-" for c in title)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")[:40]


def build_carousel(folder: Path, manifest: dict, config: dict) -> None:
    slug = folder.name
    accent = manifest.get("accent")
    variant = manifest.get("variant") or config.get("default_variant", "cream")
    if variant not in VARIANTS:
        raise ValueError(f"{slug}: unknown variant {variant!r}, must be one of {sorted(VARIANTS)}")

    handle = config["handle"]

    # Per-slide HTML
    for slide in manifest["slides"]:
        path = folder / f"{slide['id']}-{slide_type_suffix(slide)}.html"
        path.write_text(slide_html(slide, accent, variant, handle))

    # prompts.json — STYLE_PREFIX + scene composed and ready for image gen
    default_ar = "1:1"
    prompts = {
        "carousel": slug,
        "aspect_ratio": default_ar,
        "model_tier": "nb2",
        "resolution": "1k",
        "slides": {
            slide["id"]: {
                "scene": slide["scene"],
                "aspect_ratio": slide.get("aspect_ratio", default_ar),
                "prompt": compose_prompt(
                    slide["scene"],
                    aspect_ratio=slide.get("aspect_ratio", default_ar),
                ),
            }
            for slide in manifest["slides"]
            if slide["type"] != "cta"
        },
    }
    (folder / "prompts.json").write_text(json.dumps(prompts, indent=2) + "\n")

    # captions.txt — TikTok title on first line if provided, then IG caption
    title = manifest.get("title", "").strip()
    caption_body = manifest["caption"].rstrip()
    captions_out = f"{title}\n\n{caption_body}\n" if title else caption_body + "\n"
    (folder / "captions.txt").write_text(captions_out)

    print(f"  built {slug}: {len(manifest['slides'])} slides + prompts.json + captions.txt")


def main() -> None:
    config = load_brand_config()

    THEME_CSS_PATH.write_text(emit_theme_css(config))
    print(f"wrote {THEME_CSS_PATH.relative_to(DIR)} from brand.config.json")

    folders = [
        d for d in sorted(DIR.iterdir())
        if d.is_dir()
        and d.name.startswith("almanac-")
        and (d / "manifest.json").exists()
    ]
    if not folders:
        print(
            "no carousel folders found. create a folder like\n"
            "  almanac-01-<slug>/manifest.json\n"
            "and re-run."
        )
        return

    print(f"building {len(folders)} carousel(s)...")
    for folder in folders:
        manifest = json.loads((folder / "manifest.json").read_text())
        build_carousel(folder, manifest, config)
    print(
        "done. next: python3 batch_generate.py <carousel-folder>  "
        "(walks prompts.json, generates illustrations via Replicate), "
        "then ./render.sh <carousel-folder>"
    )


if __name__ == "__main__":
    main()
