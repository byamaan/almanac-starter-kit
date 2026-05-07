---
name: almanac-carousel
description: "Use when the user wants to create almanac / vintage-encyclopedia style Instagram carousels — cream slides with a classic serif title (period at the end), a steel-engraving illustration sitting directly on the cream (no frame, no border), small serif body copy below, and a brand handle at the bottom. Triggers on phrases like 'almanac post', 'almanac carousel', 'how-to carousel', 'etched illustration carousel', 'encyclopedia style post', 'vintage style post', 'sketch line art post'. On first run, walks the user through a one-time setup interview that writes brand.config.json, then propose topics → confirm → autonomous run (copy + scenes + image gen + visual QA + render). Outputs to content-bank/almanac/almanac-XX-<slug>/, pixel-perfect 2160×2700 PNGs ready to upload."
metadata:
  version: 1.0.0
  origin: "Adapted from the dhikrlock almanac-carousel skill (v3.0.0)"
---

# Almanac Carousels — Portable Edition

You are creating almanac-style Instagram carousels: encyclopedia-on-paper slides with a classic serif title at the top, a single black-and-white engraving illustration in the middle sitting directly on the canvas (no frame, no border, no plate), small body copy below, and the user's brand handle at the bottom. The aesthetic earns trust by feeling considered and timeless. The system is fully built (HTML + EB Garamond bundled + Replicate image-gen wired in + render pipeline). Your job is to follow the proven workflow and never short-circuit it.

The user reviews at **one gate**: after topic proposal. Once topics are approved, run the full pipeline autonomously — copy, scene prompts, manifest, image generation, visual QA, render — without further pauses. The only soft second gate is **content verification**: if a fact / quote / citation can't be verified against the rules in `brand.config.json`, stop and surface it before render. That's non-negotiable.

**Reproducibility is the goal.** Every almanac carousel must look and feel like it came from the same hand: same paper, same ink, same line weight, same composition rules. That comes from the locked **technique** (the engraving style enforced by `STYLE_PREFIX` in `style.py`) and the locked CSS in `base.css`. It does **not** come from forcing the same subject vocabulary. Subjects are topic-driven and free to be modern, contemporary, or historical. Never edit the locked files per-carousel.

---

## STEP 0 — First-time setup (run once)

**Before doing anything else, check if `brand.config.json` exists at the project root.**

```
Read brand.config.json
```

**If the file exists:** load it and skip to the workflow below. Always re-read it at the start of every invocation — the user may have edited it.

**If the file does NOT exist:** run the setup interview below. This is mandatory before any carousels can be built. Ask the questions one batch at a time using `AskUserQuestion`. Use the user's answers to write `brand.config.json` and `content-bank/almanac/theme.css`.

### Setup interview — ask in this order

**Batch 1 — identity (required)**
1. **Brand or account name.** What's the name of the account / brand these carousels are for? (Free text. Used for documentation only.)
2. **Handle.** What handle should appear at the bottom of every slide? Include the `@` symbol. (e.g. `@yourbrand`)
3. **Topic domain.** In one sentence, what kinds of topics will these carousels cover? (e.g. "personal-finance how-tos for early-career professionals", "fitness coaching for runners", "Islamic content modeled on encyclopedia entries"). This drives topic proposals.

**Batch 2 — visual style (defaults are sane; offer skip)**
4. **Color variant default.** Which background should be the default? Options: `cream` (beige `#F5EFE1`, ink black — calm encyclopedia feel), `deep` (purple `#5A46C7`, cream text — rich), `midnight` (indigo `#2A1F6E`, cream text — dramatic). Default: `cream`.
5. **Accent color.** A single accent color used for the optional ornamental rule under titles and the handle when the user opts into accents. Default: `#7B68EE`.
6. **Image style.** The locked illustration aesthetic. Default: black-and-white steel-engraving line art (recommended — that's what makes the format read as "considered"). Alternatives the user might pick: `minimal-line` (single-weight clean line art), `watercolor` (soft watercolor washes), or `custom` (let them write their own STYLE_PREFIX).

**Batch 3 — voice + content rules (optional; can skip with sensible defaults)**
7. **Voice rules.** Free-text list of dos/don'ts for body copy. Examples to suggest: "no em dashes", "first letter of every sentence is capital", "no emojis", "no marketing speak". Default: standard English grammar, no em dashes, no emojis.
8. **Content verification rules.** What facts or claims need primary-source verification before render? (e.g. "all financial claims need a citation", "all hadith verified on sunnah.com to ≥hasan grading", "all statistics need a year + source"). If they have nothing specific, leave empty.
9. **Replicate API token (REQUIRED).** Image generation can't run without it. First check whether `.env` already exists at the project root and contains a `REPLICATE_API_TOKEN=r8_...` line — if it does, skip this step. Otherwise, offer two paths and let the user pick:

   - **(a) Paste it here, I'll write `.env` for you.** Fast, one-shot. Caveat: the token will appear in this Claude Code conversation transcript (Anthropic may briefly retain prompts for safety/abuse review). Fine for personal dev tokens; not recommended for shared secrets.
   - **(b) I'll set up `.env` myself.** User creates `.env` at the project root with `REPLICATE_API_TOKEN=r8_...` (see `.env.example`) and confirms when done. The token never enters chat.

   Get one at https://replicate.com/account/api-tokens. Phrase the choice as a question with both options visible — don't push them toward (a) without flagging the privacy tradeoff.

   **If they pick (a):** ask them to paste the token, then `Write` `.env` at the project root with a single line: `REPLICATE_API_TOKEN=<their-pasted-value>` (no quotes, no spaces around `=`). Confirm "saved to .env" and continue.

   **If they pick (b):** wait for their "done" confirmation, then `Read` `.env` to verify the line is present. If it isn't, surface the issue and re-ask.

   Do **not** echo the token back in chat after writing it — once `.env` is written, refer to it as "your token" without printing the value.

### After the interview

Write `/brand.config.json` at the project root with this shape:

```json
{
  "brand_name": "<answer 1>",
  "handle": "<answer 2>",
  "topic_domain": "<answer 3>",
  "default_variant": "<answer 4 — cream | deep | midnight>",
  "accent_color": "<answer 5>",
  "image_style": "<answer 6 — engraving | minimal-line | watercolor | custom>",
  "custom_style_prefix": "<answer 6 if custom; else empty string>",
  "voice_rules": "<answer 7 as multiline text>",
  "content_rules": "<answer 8 as multiline text>",
  "default_slide_count": 7,
  "palette": {
    "cream":    { "bg": "#F5EFE1", "ink": "#12101A" },
    "deep":     { "bg": "#5A46C7", "ink": "#F5EFE1" },
    "midnight": { "bg": "#2A1F6E", "ink": "#F5EFE1" }
  }
}
```

Then run `python3 content-bank/almanac/build.py` once to verify everything wires up. The script reads `brand.config.json` automatically, regenerates `theme.css` from the palette + accent color, and reports "no carousel folders found" — that's the expected first-run state. The handle in HTML and the `STYLE_PREFIX` for image gen are both pulled from `brand.config.json` at every build, so no per-file edits are needed.

**Confirm with the user** that the kit is ready, then proceed to the workflow below the next time they ask for a carousel. The setup is one-time — once `brand.config.json` exists, this whole step is skipped on future invocations.

---

## What the slide actually looks like

- Background uses `default_variant` from config (`cream` is `#F5EFE1`).
- Title at the top — EB Garamond 84px SemiBold, Title Case, ends in a period.
- Illustration centered — pure black ink on white background, `mix-blend-mode: multiply` keys the white out so the ink sits **directly on the canvas with no frame, no border, no shadow**. There is no white plate, no black stroke around the image.
- Body copy below — EB Garamond 40px regular, 3 short lines, max-width 920px, centered.
- Brand handle (from config) italic at the bottom.

The CTA slide (always last) is **text-only**. No illustration. Title at 84px vertically centered, handle below. That's it.

---

## The 2-phase workflow (LOCKED)

The workflow is intentionally tight: **one user gate at topic approval, everything else autonomous.**

### Phase 1 — Propose topics (THE ONLY GATE)

When the user asks for "an almanac post" or "N almanac carousels", that means **N carousels** (each carousel = cover + 5 steps + CTA = 7 slides by default). Default to 1 if N is unspecified.

Almanac topics MUST be **how-to or step-by-step** in shape. The format is built for instructional / sequential content. Topics that aren't naturally sequential should be redirected — propose a different framing.

Strong almanac topic shapes:
- *How To* + a practice or skill (any domain)
- *The Three Sunnahs Of* / *The Five Steps To* / *The Way To* + daily action
- *How To Prepare For* + a season or event
- *The Habits Of* + a person or archetype (each slide = a habit)
- *What To Do When* + a situation (each slide = a step)

Pull topic ideas from the `topic_domain` field in `brand.config.json` — every topic must fit that domain. If the user gives a specific topic, use it directly.

Propose a batch as a markdown table:

| # | Category | Topic | Why it earns the format |
|---|---|---|---|
| 1 | … | "How To Make Wudhu" | Sequential, foundational, perfect for 7-step almanac structure |

Rules for the proposal:
- Each topic must be naturally sequential / instructional. If it isn't, propose a different one.
- Mix categories — not five "How To" topics in a row from the same sub-niche.
- Avoid duplicating already-shipped almanac carousels (check `content-bank/almanac/` for existing folders).
- Each title is Title Case and ends in a period. ("How To Make Wudhu.")

**STOP** after proposing. Wait for user confirmation. This is the only gate.

### Phase 2 — Autonomous full run

Once topics are approved, run everything end-to-end without further pauses:

1. **Pick variant + length per topic using judgment** (don't ask).
   - Default variant: from `brand.config.json` (`default_variant`). Use the alternates (`midnight`, `deep`) for occasional dramatic frontispieces (~1 in 5).
   - Default length: 7 slides (cover + 5 steps + CTA). Adjust only if the topic genuinely calls for fewer (a 3-step topic gets 5 slides total, not 7).
2. **Write all copy + scenes for every slide of every carousel** using the format and rules below (titles, body lines, references, scene prompts).
3. **Verify all factual claims / citations** against the `content_rules` in `brand.config.json`. This is the soft second gate — if any claim can't be verified per the user's stated rules, STOP and surface it before proceeding. Bad citations are worse than slow output.
4. **Write per-carousel manifest.json files** in each new carousel folder (see "Build manifest" below for the shape). Then run `python3 build.py` from `content-bank/almanac/` — generates HTML + `prompts.json` + `captions.txt`.
5. **Library lookup before generation.** Run `python3 library.py find "<scene>"` for every non-CTA slide's scene. If the top match scores ≥ **0.30** Jaccard, copy that PNG from `_library/` into the new carousel's `illustrations/<slide_id>.png` and skip the Replicate call for that slide. Below 0.30, generate fresh. Track which slides are reused vs newly generated for the end-of-run report.
6. **Run image generation** — `python3 batch_generate.py <carousel-folder-name>` walks every slide in `prompts.json`, skips slides whose PNG already exists, POSTs sequentially to Replicate `google/nano-banana-2` with 10.5s spacing (low-credit tier safe), polls, downloads. After each successful new generation, call `python3 library.py add <png> "<scene>" --source <carousel>/<slide_id>` so the library grows.
7. **Visual QA every PNG** against the checklist in the "Visual QA" section. Regen failures silently — don't ask permission to regenerate a slide that has a face / border / wrong subject. **Library reuses still get QA'd** — the match was on subject vocabulary, not on the slide's specific concept, so confirm the visual makes sense in the new context.
8. **Render** via `./render.sh <carousel-folder>` for each carousel. Render runs `crop.py` automatically as a preprocessor — trims near-white margins on illustrations so subject sizes stay uniform across the carousel.
9. **Report back** at the end: folders ready to post + verification flags + any style-consistency notes + reuse summary (`N reused from library, M newly generated`) + suggested next batch.

The only pauses inside Phase 2:
- Content verification flag (mandatory).
- The user pre-empts you with edits / course corrections (always honor).

Everything else — variant choice, body wording, scene composition, regen of bad PNGs — is autonomous.

---

## Slide format reference

Each slide follows this structure when written:

```
**S1 (cover)** — `How To Make Wudhu.`
Scene: A close-up of a single ornate copper ewer (ibriq) with calligraphic engraving along its body, the ewer filling the composition. Tight crop. No rectangular plate edge, no inner border, no frame around the image, just the ewer itself on pure white. Centered, isolated.

**S2 (step)** — `Begin With Intention.`
> Wudhu starts in the heart, not the hands.
> Quietly intend it for the sake of Allah.
> No words required.
Scene: …

**S7 (cta)** — `Follow For More.`
(no scene — CTA is text-only)
```

### Title rules

- Title Case, ends in a period.
- 1 line ideally; 2 lines max. **Never strand a single word on its own line.** If wrap is awkward, rewrite. ("Wipe Head And Wash Feet." → "Wipe Head, Wash Feet.")
- Punchy and concrete. "Wash The Hands." beats "The Washing Of The Hands."
- Titles in the 25–35 char range commonly orphan a closing single word. Aim **≤22 chars** (single line) or **35+ chars with multi-word distribution**. Catch at draft time.
- **Cover titles = the hook.** They earn or lose the swipe. Specific > generic. Promise a payoff. Punchy. Proven shapes: "Three Sunnahs Of X.", "How To X.", "The X Of Y.", "What X Did On Y." If your subject is a named person (real or historical), name them on the cover, not a pronoun. ("What The Prophet ﷺ Did On Thursdays" beats "What He Did On Thursdays" — pronouns lose their anchor when the title is truncated in a feed preview.)

### Body rules — three-tier hierarchy

The body region renders three optional fields, top to bottom: `arabic` (or any quote/transliteration) → `body` → `reference`. Use whichever the slide actually needs; never duplicate the reference inline in the body.

1. **`body` is a LIST of strings, one string per visible line.** Each list item becomes its own paragraph. The author controls the line break. Never let lines wrap on their own — write each line short enough (target ≤50 chars) so it fits on one display line. This is the rule that prevents orphan-word wraps like a stranded "purity." on a line by itself.
2. **`arabic` (optional)** — for transliterated quotes, foreign-language phrases, or pull-quotes that should sit larger than the prose. Renders italic, slightly tighter, above the body. Use it whenever the slide is built around an actual quote or named phrase; the source line carries weight on its own and shouldn't be buried in prose. (Field name kept as `arabic` for backwards compatibility with the original dhikrlock template — it's actually a generic "headline quote" slot.)
3. **`reference` (optional)** — the citation alone, e.g. `"Bukhari 247"`, `"Drucker, 1973"`, `"NHS 2024"`. Renders 22px italic and muted below the body. **Never** write the citation at the end of a body line; always lift it into its own field. The visual separation is what makes the slide read like a properly typeset reference, not a Twitter screenshot.

Other rules (in addition to whatever's in `voice_rules` from config):
- Reads like a calm encyclopedia, not a tweet. Default is plain prose, no marketing voice.

### Scene rules

The locked `STYLE_PREFIX` (in `style.py`) enforces the **technique** — for the default engraving style: black-and-white steel-engraving line art, pure white background (keyed to the canvas via CSS multiply), no faces, single subject, no text in image. The technique is locked. The **subject is open** — pick whatever the topic calls for. Modern, contemporary, historical, abstract, all fine. Do not force vintage props (oil lamps, ewers, prayer mats) unless the topic genuinely wants them.

1. **Single subject + at most one accent prop.** Crowded scenes look amateur regardless of style. "A modern bedside lamp being switched off, a folded duvet beside it" beats a busy bedroom.
2. **Match subject to topic.** If the topic is contemporary (sleep, scrolling, work, mornings), use contemporary objects. If it's historical or scriptural, historical objects fit naturally. Either way, one focal subject, drawn in the locked technique.
3. **No human faces, no eyes, no portraits — ever.** The locked style prefix excludes them, but the scene description should also avoid framings that would require them. Hands, forearms, feet are fine. **Never above the wrist or ankle.** If a scene seems to need a face, find a different angle (a hand resting on a pillow instead of someone sleeping, a hand turning a tap instead of a person at a sink).
4. **Compose with stillness.** Calm, uncluttered. End scene descriptions with "Centered, isolated." to reinforce.
5. **CTA has no scene.** If the carousel uses a CTA slide, it's text-only. Single-slide posts don't need one at all.

### Scene-prompt formula (use this every time)

The model has two persistent drift modes that the locked style prefix alone does not catch. Defend against both in every scene description:

- **Drift A — model adds a visible rectangular plate / inner border around the illustration.** A subtle gray plate edge that `mix-blend-mode` cannot fully key out, leaving a visible "box" inside the frame.
- **Drift B — subject comes back small.** The model leaves whitespace around the subject, so the illustration looks tiny inside the frame.

Mitigation, baked into every scene description:

```
A close-up of <subject>, <subject> filling the composition. Tight crop.
No rectangular plate edge, no inner border, no frame around the image,
just the <subject> itself on pure white. Centered, isolated.
```

Don't paraphrase the no-border line softly ("on a clean background") — be explicit. The phrase that works is the literal one above.

### Caption + title rules

- **Every carousel manifest MUST have a `title` field** — Title Case, no trailing period (it's a TikTok / IG title, not a slide title). The user posts to TikTok where title and caption are separate inputs; missing title = manual rework on every post. Example: `"title": "The Sunnahs Of Drinking Water"`.
- **Captions follow standard English grammar** unless `voice_rules` overrides. First letter of every sentence is capital. First letter after every period is capital. Proper nouns are always capital. Don't lowercase-everything for "vibes" — it reads as a typo.
- Apply all rules from `voice_rules` in `brand.config.json`.

`build.py` writes the title as the first line of `captions.txt`, then a blank line, then the IG caption body. The user copies the title into TikTok's title field and the body into the caption field.

---

## Build manifest + generate illustrations

For each carousel, create a folder `content-bank/almanac/almanac-NN-<slug>/` (NN zero-padded, slug short kebab-case) and write `manifest.json` inside it with this shape:

```json
{
  "title": "The Sunnahs Of Drinking Water",
  "caption": "<full IG caption with line breaks and hashtags>",
  "variant": "cream",
  "accent": null,
  "slides": [
    { "id": "01", "type": "cover", "title": "...", "scene": "..." },
    {
      "id": "02",
      "type": "step",
      "title": "...",
      "body": ["First line.", "Second line."],
      "arabic": "Optional headline quote",
      "reference": "Bukhari 6324",
      "scene": "..."
    },
    { "id": "07", "type": "cta", "title": "Follow For More." }
  ]
}
```

Field notes:
- `variant`: `"cream"` (default) | `"deep"` | `"midnight"`. Pulls from `default_variant` if omitted.
- `accent`: `null` (default) or `"purple"` — opt-in ornamental rule + colored handle (uses `accent_color` from config).
- All slides use 1:1 aspect ratio. The CTA slide has no `scene` and no `body` — it's text-only.

Then, from inside `content-bank/almanac/`:

```bash
python3 build.py
```

`build.py` walks every `almanac-NN-<slug>/` folder, reads `manifest.json`, writes per-slide HTML + `prompts.json` (excluding CTAs) + `captions.txt`. Each slide entry in `prompts.json` carries a fully composed `prompt` field (STYLE_PREFIX + scene) ready to pass through verbatim.

### Generate illustrations — Replicate `google/nano-banana-2`

For each slide in `prompts.json`, generate via Replicate's hosted `google/nano-banana-2` endpoint. Run from `content-bank/almanac/`:

```bash
python3 batch_generate.py almanac-NN-<slug>
```

The script:
- Reads `REPLICATE_API_TOKEN` from `.env` at project root (or from environment).
- Walks `prompts.json`, skips slides whose PNG already exists in `illustrations/`.
- POSTs sequentially with **10.5s spacing** between creates. Replicate's low-credit tier (sub-$5) is **6 requests/min, burst 1** — parallel batches 429 immediately. Keep the spacing.
- Polls each prediction every 3s in a background thread, downloads to `illustrations/<slide_id>.png`.

To regenerate a single failed slide: delete the PNG on disk and re-run the batch. To skip already-good slides: just leave them in place — the script skips existing files.

### Visual QA before rendering — REQUIRED

Open every illustration. Check each one against this list:

- [ ] Background is white (or near-white). The CSS multiply blend keys this to the canvas — if the illustration has its own tinted background, it will look like a darker block on the slide.
- [ ] No human faces, no eyes anywhere in the image.
- [ ] No accidental borders, frames, plate edges, or vignettes drawn by the model.
- [ ] No text, captions, signatures, watermarks.
- [ ] Stroke weight and crosshatching density match the other slides — they should read as the same hand.
- [ ] Subject matches what the manifest scene asked for.
- [ ] **Subject visually maps to the slide concept.** A reader scanning the slide should see the illustration and immediately understand the topic. If the subject is metaphorical or oblique, swap it. The illustration is the cognitive shortcut.
- [ ] Composition is calm — single subject, at most one accent prop.

### Render

```bash
./render.sh almanac-NN-<slug>
```

Outputs:
- `almanac-NN-<slug>/out/` — final 2160×2700 PNGs (what gets uploaded to IG).
- `almanac-NN-<slug>/previews/` — 1080×1350 downscales of the same PNGs.

**Always read previews, never the full-res `out/` PNGs, when doing visual QA.** The Anthropic API caps any single image in a many-image request at 2000px on the longest side; the 2160×2700 outputs exceed that.

Render-time post-checks (after `./render.sh` writes to `out/`):
- [ ] No 2-line title clips a descender (g, j, y, p, q) into the frame region. If it does, the title is too long for the layout — rewrite to 1 line or shorter wording. Don't loosen the layout.
- [ ] Subject sizes are visually consistent across step slides. `crop.py` runs automatically; if some slides still look much smaller than others, the source PNG had the subject drawn small inside the canvas — regenerate that slide with stronger "fills the composition" language.
- [ ] No floating gap between illustration and body text. Big gaps mean the source had a small subject + lots of whitespace; auto-crop normally fixes this, but a stubborn case may need a regen with tighter scene language.

Any slide that fails any check: regenerate it via Replicate (delete the PNG, re-run `batch_generate.py`). The model composes differently on a re-call. Do **not** edit the locked `STYLE_PREFIX` to fix one slide. Don't ask the user before regenerating a failed slide — it's part of the autonomous run.

Report back:
- The folders created
- Any references that need an extra verification pass
- Style-consistency notes if anything looks off
- Suggested next batch

---

## Slide types and what they look like

The CSS supports three slide types:

- **`cover`** — title only (no body), 780×780 illustration sitting directly on the canvas. Used as slide 1.
- **`step`** — title + 620×620 illustration + structured body (arabic / lines / ref). Used for the middle slides.
- **`cta`** — text only. Big centered title (84px), handle below, no illustration. Used as the final slide.

Default carousel length: cover + 5 steps + CTA = 7 slides. Range: 5–8 slides.

---

## Optional accent

By default the slide is austere: canvas + ink only. The CSS supports an opt-in accent via `"accent": "purple"` (or whatever color is in `accent_color`) in the manifest, which renders:
- A 1px × 60px ornamental rule centered under the title (80px on CTA), AND
- The handle line in the accent color instead of ink.

Do not enable this on every carousel. Default is no accent. Switch on for one carousel in five at most, and only when the topic earns a flourish.

---

## Variants

Three locked color variants — pick per-carousel via the `variant` field in the manifest:

- **`cream`** (default) — beige background, ink text. Calm, austere, encyclopedia-on-paper feel.
- **`deep`** — purple background, cream text. Old-kitab-endpaper feel.
- **`midnight`** — indigo background, cream text. Most dramatic, frontispiece feel.

The same illustration PNGs work for all three variants — the cream version uses `mix-blend-mode: multiply` to drop white onto cream, and the dark variants use `filter: invert(1)` + `mix-blend-mode: screen` to flip the ink and drop black onto the dark background. Zero regeneration cost when switching.

---

## Content verification (HARD RULE)

Apply the rules from `content_rules` in `brand.config.json`. 100% of claims / citations must be verified before render.

If you're not 100% sure on a claim, surface it before rendering. **Stalling > shipping bad content.**

---

## File conventions

- Folder per carousel: `content-bank/almanac/almanac-NN-<slug>/`
- Inside each carousel folder:
  - `manifest.json` — single source of truth for that carousel
  - per-slide HTML files (generated by `build.py`)
  - `prompts.json` (generated; image-gen batch input)
  - `captions.txt` (generated; TikTok title + IG caption)
  - `illustrations/` — the generated PNGs
  - `out/` — final 2160×2700 PNGs
  - `previews/` — 1080×1350 downscales for QA

**Shared scripts at `content-bank/almanac/`:**
- `build.py` — walks carousel folders, reads each manifest, writes HTML + prompts.json + captions
- `batch_generate.py` — Replicate sequential batch image-gen
- `library.py` — illustration reuse library (`index` / `find <scene>` / `add` / `stats`)
- `crop.py` — illustration whitespace normalizer (idempotent; auto-runs from render.sh)
- `render.sh` — Chrome headless screenshot pipeline + auto-crop
- `style.py` — STYLE_PREFIX + compose_prompt (consistency anchor)

**Library at `content-bank/almanac/_library/`:**
- One `<carousel-slug>_<slide-id>.png` per indexed illustration
- `library.json` manifest with scene + subject keywords + source provenance
- Run `python3 library.py index` after a new carousel ships to grow the pool. Idempotent.

The user posts a carousel by opening `<folder>/out/`, dragging the PNGs into IG in order, and pasting `captions.txt` into the caption field.

---

## What NOT to do

- **Do not pause for approval inside Phase 2.** Topic gate is the only one. The only legitimate stop inside Phase 2 is an unverifiable claim per `content_rules`.
- **Do not ask the user about variant or length** at the topic gate unless they've asked you to. Pick using judgment.
- **Do not edit `base.css` or `theme.css`** when adding carousels. Style is locked. New content goes in `manifest.json` only.
- **Do not edit `STYLE_PREFIX`** in `style.py` mid-run. It is the consistency anchor across all carousels — change it once at setup, then never per-carousel.
- **Do not put a frame or border around illustrations.** They sit directly on the canvas. The `mix-blend-mode: multiply` handles the keying.
- **Do not generate illustrations for the CTA.** It is text-only.
- **Do not generate human faces** in scenes.
- **Do not skip the visual QA checklist.** The locked prompt does not catch every drift. Eyes on every PNG before render.
- **Do not skip the content verification gate.**
- **Do not exceed 8 slides** per carousel. Almanac is for tight, focused step-by-step. If the topic needs 12 slides, it's two carousels.
- **Do not write marketing copy.** Voice is the calm narrator of an old kitab, not a brand voice.
- **Do not modify `brand.config.json` mid-session** without telling the user — they own that file.

---

## Quick mental model

User hits you with "make me 3 almanac posts". You:
1. Read `brand.config.json`. (If missing, run setup first.)
2. Propose 3 topics in a table → wait
3. They say go → run everything: variant + length pick, copy + scenes for all 21 slides, content verification, manifests written, build.py run, image-gen batch, visual QA + silent regen, render.sh × 3
4. Report folders + verification flags + style notes

One gate. Pixels, fonts, layout, ink-on-canvas blending are handled by the locked CSS template + locked style prefix — you do not need to think about them.
