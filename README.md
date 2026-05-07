# Almanac Carousel Starter Kit

Encyclopedia-style Instagram carousels — clean serif title, single black-and-white engraving illustration, small body copy, brand handle. Modeled on what `@dhikrlock` ships every week, packaged so you can drop it into your own brand and produce the same format with your own topics.

You bring the topics, the handle, and a Replicate API token. The kit handles HTML layout, image generation via Gemini's nano-banana-2 model on Replicate, illustration cropping for visual consistency, and rendering to pixel-perfect 2160×2700 PNGs ready to upload.

## What you get

```
almanac-starter-kit/
├── README.md                           # you are here
├── SETUP.md                            # step-by-step install
├── brand.config.example.json           # template config — copied to brand.config.json on first run
├── .env.example                        # template env file — REPLICATE_API_TOKEN goes here
├── .claude/skills/almanac-carousel/
│   └── SKILL.md                        # the skill Claude Code loads
└── content-bank/almanac/
    ├── build.py                        # walks carousel folders, writes HTML + prompts.json + captions
    ├── batch_generate.py               # sequential Replicate image-gen
    ├── render.sh                       # Chrome headless → 2160×2700 PNG
    ├── crop.py                         # whitespace normalizer (auto-runs in render.sh)
    ├── library.py                      # illustration reuse library (grows with every carousel)
    ├── style.py                        # STYLE_PREFIX + compose_prompt — locked consistency anchor
    ├── base.css                        # locked layout
    ├── theme.css                       # generated from brand.config.json on each build
    ├── fonts/                          # EB Garamond bundled (SIL OFL)
    └── _library/                       # illustration reuse cache (starts empty)
```

## How it works

1. **One-time setup** — clone the kit, install deps, run Claude Code in the folder. The skill walks you through 9 questions (brand name, handle, topic domain, style, voice rules, etc.) and writes `brand.config.json`. Add your Replicate token to `.env`.
2. **Ask for carousels** — `"make me 3 almanac posts about <your domain>"`. The skill proposes 3 topics in a table.
3. **Approve** — say go. The skill runs everything autonomously: writes copy + scenes for every slide, runs `build.py`, generates illustrations via Replicate, runs visual QA, regenerates failures silently, and renders the final PNGs.
4. **Post** — open `content-bank/almanac/almanac-NN-<slug>/out/`, drag the PNGs into Instagram in order, paste `captions.txt`.

The whole loop after step 1 is one approval gate per batch. The output looks like it came from the same hand every time because the engraving style and CSS layout are locked at the kit level — only your manifests change.

## Requirements

- **macOS or Linux.** Windows isn't supported by `render.sh` out of the box (you'd need to swap Chrome detection).
- **Claude Code** installed and the skill auto-loaded from `.claude/skills/`.
- **Python 3.9+** with `pillow` (`pip install pillow`).
- **Google Chrome or Chromium** installed (used by `render.sh` for headless screenshots).
- **Replicate account + API token.** Costs roughly $0.02 per illustration. A 7-slide carousel = ~6 generations = ~$0.12 each.

## Next step

Read `SETUP.md` for the 5-minute install walkthrough.

---

*Adapted from the dhikrlock almanac-carousel skill. The aesthetic, workflow shape, and image-gen pipeline are battle-tested across 50+ shipped carousels — see `@dhikrlock` on Instagram and TikTok for live examples.*
