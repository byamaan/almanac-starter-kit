# Setup

Five-minute install. After this you'll be able to ask Claude Code for almanac carousels and have them rendered to PNG end-to-end.

## 1. Drop the kit into a new repo

```bash
# Option A — copy it as-is
cp -R almanac-starter-kit/ ~/your-new-project
cd ~/your-new-project

# Option B — initialize a fresh git repo
cd ~/your-new-project
git init
git add .
git commit -m "init from almanac-starter-kit"
```

The kit *is* the project. The `.claude/skills/` folder makes the skill auto-load when you open Claude Code in this directory.

## 2. Install dependencies

```bash
# Python — the build/render scripts use Pillow (PIL).
pip install pillow

# Chrome / Chromium — required for headless screenshots.
# macOS:    install Google Chrome from google.com/chrome (most users already have it)
# Linux:    sudo apt install chromium-browser   (or your distro's equivalent)
```

If Chrome is in a non-standard location, set `CHROME=/path/to/chrome` in your shell — `render.sh` will pick it up.

## 3. Get a Replicate API token

1. Sign up at [replicate.com](https://replicate.com) (free).
2. Go to [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens) and create a token.
3. Copy `.env.example` to `.env` at the project root and paste your token:

```bash
cp .env.example .env
# edit .env, replace `r8_xxxxx...` with your real token
```

The kit reads `REPLICATE_API_TOKEN` from `.env` automatically. **Never commit `.env`** — `.gitignore` already excludes it.

> Cost: about $0.02 per illustration via Google's `nano-banana-2`. A 7-slide carousel = ~6 generations = ~$0.12. Replicate's free tier gives you a few dollars of credit to start. Below $5 sustained balance you're rate-limited to 6 requests/min — the batch script handles this with 10.5s spacing automatically.

## 4. Open Claude Code in the project folder

```bash
cd ~/your-new-project
claude
```

The skill at `.claude/skills/almanac-carousel/SKILL.md` will be available. Type:

```
make me an almanac post about how to start journaling
```

(Or whatever fits your topic domain — replace "how to start journaling" with anything sequential.)

On the **first** invocation, the skill will detect that `brand.config.json` doesn't exist and run a one-time setup interview. It'll ask you 9 questions:

1. **Brand or account name** — used for documentation only.
2. **Handle** — what shows on every slide. Include the `@`. (e.g. `@yourbrand`)
3. **Topic domain** — one sentence describing what kinds of posts you'll make.
4. **Color variant default** — `cream` (recommended), `deep`, or `midnight`.
5. **Accent color** — hex code for the optional ornamental rule and accent handle.
6. **Image style** — `engraving` (recommended), `minimal-line`, `watercolor`, or `custom`.
7. **Voice rules** — free-text dos/don'ts for body copy. Skippable.
8. **Content verification rules** — what facts/claims need primary-source verification. Skippable.
9. **Replicate token check** — confirms your `.env` is set up.

The skill then writes `brand.config.json` at the project root and `theme.css` next to `base.css`. From the next message onward, just ask for carousels and the autonomous workflow kicks in.

## 5. Make your first carousel

```
make me 3 almanac posts about <topics in your domain>
```

The skill proposes 3 topics in a table. Approve them. The skill runs everything end-to-end and reports back with the folder paths.

Open `content-bank/almanac/almanac-01-<slug>/out/` to see the final 2160×2700 PNGs. Drag them into Instagram in numeric order. Copy `captions.txt` into the caption field (first line is the TikTok title, the rest is the IG body).

## Troubleshooting

**"REPLICATE_API_TOKEN not found"** — Did you create `.env` at the *project root*, not inside `content-bank/almanac/`? Check `cat .env` from the project root.

**`render.sh: Chrome not found`** — Set `CHROME=/path/to/your/chrome` in your shell, or symlink it into `/usr/local/bin/google-chrome`.

**Title clips into the illustration on a 2-line title** — The title is too long. Rewrite it to 1 line or shorter wording. Don't loosen `base.css` — the fixed layout is what makes carousels look consistent. The skill should catch this in its render-time post-checks.

**Illustration is tiny inside the frame** — Replicate returned a small subject. Delete that PNG and re-run `python3 batch_generate.py <carousel-folder>`. The skill should catch this in visual QA and regenerate silently — if it doesn't, ping it.

**Want different default colors?** Edit `brand.config.json`'s `palette` block, then run `python3 build.py` to regenerate `theme.css`.

**Want a totally different image style** (not engraving / minimal-line / watercolor)? Set `"image_style": "custom"` in `brand.config.json` and write your own STYLE_PREFIX into `"custom_style_prefix"`. Keep the no-faces / pure-white-background / no-borders constraints in your custom prefix — those are what the CSS multiply blend depends on.
