---
name: social-media-posts
description: "Design and render on-brand social media images (Instagram posts, carousels, stories, reel covers, LinkedIn/X/Facebook/YouTube graphics) with ImageMagick. Handles intake of the content type and copy, discovers or asks for brand guidelines (colors, fonts, logos, imagery), builds moodboards from local images or Instagram/Pinterest URLs, proposes directions, renders with a reproducible JSON spec, and QA-checks contrast, safe zones and sizes. Use whenever the user wants to create, design, mock up or batch-produce a social post, carousel, story, announcement, quote card, event or product graphic, or wants a moodboard for one."
---

# Social Media Posts

Turn a content brief into finished, on-brand post images using **ImageMagick 7** (`magick`) as the rendering engine. Every design is described as a JSON spec and rendered with `scripts/render_post.py`, so it can be re-rendered, tweaked and reused as a template.

Treat paths as relative to the user's **project folder** (the current working directory), not this skill directory. Skill scripts live in `scripts/` next to this file.

## 0. Check dependencies

Required: `magick` (ImageMagick 7), `python3`, `gallery-dl` (Instagram image posts/carousels, Pinterest, Behance), `yt-dlp` (reels/video refs). Optional: `ffmpeg` (still frames from video refs).

Check with `magick -version`, `gallery-dl --version`, `yt-dlp --version`.

If something is missing, **install it automatically** — tell the user in one line what you're installing and why, then do it:
- **gallery-dl — always from the original GitHub repo** (https://github.com/mikf/gallery-dl), never PyPI or a distro package: `uv tool install git+https://github.com/mikf/gallery-dl` (update with `uv tool upgrade gallery-dl`).
- yt-dlp: `uv tool install yt-dlp`.
- If `uv` itself is missing: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `pipx install` as a fallback).
- ImageMagick 7 / ffmpeg: package manager (`sudo pacman -S --needed imagemagick ffmpeg` / `sudo apt install imagemagick ffmpeg` / `brew install imagemagick ffmpeg`). These need `sudo`: if you can't run it, give the user the command to run as `! sudo pacman -S --needed imagemagick ffmpeg` and continue once it's done.

Re-check versions after installing. If an install fails, show the error and the command, and carry on with the parts of the skill that don't need that tool (only fetching references from URLs needs gallery-dl/yt-dlp).

## Project folder structure

The skill works best with this layout in the project folder (one folder per brand/client):

```
<project>/
├── brief.md                  # optional: what this batch of posts is for
├── brand/
│   ├── brand.json            # colors, fonts, logos, voice — written after brand intake
│   ├── guidelines/           # brand book PDFs, style guides
│   ├── logos/                # SVG / transparent PNG; light, dark, mark versions
│   └── fonts/                # TTF / OTF files
├── assets/
│   ├── photos/               # the brand's own photography
│   └── graphics/             # icons, illustrations, textures, patterns
├── moodboard/
│   ├── urls.txt              # reference links, one per line
│   ├── refs/                 # fetched / dropped-in references (+ _sources.md)
│   ├── notes.md              # what we like about each reference
│   └── _board.png            # generated contact sheet + palette
├── templates/                # reusable specs for recurring series
└── posts/
    └── YYYY-MM-DD-<slug>/    # one folder per post or carousel
        ├── spec.json
        ├── post.png | slide-01.png …
        └── caption.md        # caption, hashtags, alt text
```

Rules:
- **Existing project with its own structure:** don't reorganize it. Map what's there (`scan_brand.sh` finds assets anywhere up to 5 levels deep), tell the user which files you'll use, and point `brand.json` paths at their current locations. Only create the folders you need to write to (`posts/`, `moodboard/`).
- **Empty or new project:** say you'll create the structure, then run `scripts/init_project.sh`. It only creates missing folders plus `brief.md` and `moodboard/urls.txt`/`notes.md` templates, and never moves or overwrites files. Ask the user to drop logos, fonts, guidelines and photos into the matching folders.
- References in `moodboard/` are never used as assets in final posts; only `brand/` and `assets/` (or files the user explicitly provides) are.

## 1. Intake — what are we making?

Ask (one compact message, skip anything already answered) using AskUserQuestion where options make sense:

1. **Content type** — single post, carousel (how many slides), story, reel cover, quote card, announcement/launch, event, product/promo, testimonial, tips/educational, behind-the-scenes, hiring, other.
2. **Platform(s) & format** — see [formats](references/formats.md). Default: Instagram 4:5 portrait (`ig-portrait`, 1080×1350). Offer extra sizes for cross-posting.
3. **Copy** — headline, supporting text, CTA, date/location/price, handle/URL. Ask who writes it; offer to draft it in the brand voice. Ask the **language** (don't assume English).
4. **Goal & audience** — awareness, engagement, conversion, information. Shapes hierarchy and CTA.
5. **Imagery** — user photos, product shots, illustrations, or type-only/graphic.
6. **Deliverables** — also want caption text, hashtags and alt text? (Usually yes — offer it.)

## 2. Brand — discover first, then confirm

Read `brief.md` if present. Run `scripts/scan_brand.sh` in the project folder. It lists brand.json/guidelines, logos (with size/alpha), fonts (with family names), hex colors mentioned in files, photo folders, existing moodboards and previous posts.

- **If assets were found:** state clearly what you found and what you plan to use, e.g. *"Found `brand/logo-white.svg`, `fonts/Inter-Bold.ttf`, colors #0E3B43 / #F2A541 in `brand/guidelines.md`. I'll use these — correct?"* Never silently assume; always state it, and ask when something is ambiguous (several logo versions, conflicting colors).
- **If a PDF brand book exists:** read it (Read tool, `pages`) and extract colors, fonts, logo rules, clear-space, do/don't.
- **If nothing was found:** ask for brand guidelines, colors (hex), fonts (files or names), logos (prefer SVG or transparent PNG; light and dark versions), tone of voice, and handles. If they have none, offer to propose a mini identity, and sample colors from their logo/photos with `scripts/palette.sh -o palette.png image...`.
- **Persist it:** write/update `brand/brand.json` (schema in [brand intake](references/brand-intake.md)) so future posts skip these questions. Ask before overwriting an existing one.

Check fonts actually work: ImageMagick needs TTF/OTF files (convert WOFF/WOFF2 first) or an installed family (`magick -list font | grep -i <name>`). Logos in SVG/PDF/AI: rasterize at high density, e.g. `magick -density 600 -background none logo.svg -resize 1200x logo.png`.

## 3. Moodboard & direction (before the first render)

Offer — don't force — one of these, based on how clear the brief is:

- **Quick questions:** style keywords (minimal / bold / editorial / playful / luxury / organic / tech), light vs dark, photo-led vs type-led, references to brands/accounts they like, anything to avoid.
- **Moodboard folder:** create `moodboard/` and either (a) the user drops images/screenshots in, or (b) the user gives URLs (Instagram posts/reels, Pinterest, Behance, Dribbble, direct images) and you fetch them:
  ```bash
  scripts/fetch_refs.sh -d moodboard/refs -b chrome URL1 URL2   # or -f moodboard/urls.txt
  scripts/moodboard.sh moodboard "Project — direction"            # -> moodboard/_board.png + palette
  ```
  Instagram usually requires login cookies (`-b <browser>` where the user is logged in). `yt-dlp` handles reels/video posts (thumbnail + caption metadata; `-v` also extracts frames); **image-only posts and carousels need `gallery-dl`** — yt-dlp reports "no video" for them. If both fail, fall back to screenshots via Claude in Chrome or ask the user to drop screenshots in the folder. Details: [moodboards](references/moodboard.md).
- Look at the board (Read the PNG) and summarize what you see: palette, type style, composition, photo treatment, density. Propose **2–3 distinct directions** in a few lines each, and let the user pick or mix.

References are inspiration only: never place downloaded third-party images in a final post unless the user confirms they have rights.

## 4. Design & render

Write a spec per post at `posts/<YYYY-MM-DD>-<slug>/spec.json` (outputs next to it), then render:

```bash
python3 scripts/render_post.py posts/2026-11-20-launch/spec.json --guides            # single post
python3 scripts/render_post.py posts/2026-11-20-tips/spec.json --guides --overview   # carousel
```

Spec format and all layer options: [spec reference](references/spec.md). Key points:
- `"brand": "../../brand/brand.json"` enables tokens like `"$primary"`, `"$heading"`, `"$logos.light"`.
- Layer types: `text`, `image`, `logo`, `rect`, `scrim`; positions via `anchor` + `x`/`y` (px or `%`).
- Carousels: `slides` + `common_layers` (logo, `{n}/{total}` counter); output gets `-01`, `-02`…
- For effects the spec doesn't cover (duotone variants, cut-outs, masks, textures, rotated type, background removal), use raw `magick` commands from [ImageMagick recipes](references/imagemagick-recipes.md) to prepare an asset, then place it as an `image` layer.

Design defaults (override with the brand guidelines):
- One clear focal point and hierarchy: headline ≥ 64px on 1080 wide, body ≥ 32px; max ~3 type sizes, max 2 font families.
- Generous margins (≥ 64px / ~6%); align everything to the same margins.
- Keep headline copy short (≤ ~8 words per slide); carousel slide 1 = hook, last slide = CTA.
- Text over photos always gets a scrim, box or a calm area of the image.
- Logo small and consistent in position across a series; respect clear-space rules.

## 5. QA — always look before delivering

1. Read the rendered PNG(s) (and the `.guides.png`) and critique them honestly: hierarchy, alignment, spacing, cropping of faces/products, text overflow, typos, accents/diacritics rendering.
2. Resolve every renderer `WARN:` — low contrast (WCAG: 4.5:1 body, 3:1 large text), text outside platform safe zones (stories/reels UI), missing fonts.
3. Check the profile-grid crop (yellow guide): sides of 4:5 feed posts, central 3:4 of reel covers.
4. Fix and re-render; iterate until clean. Show the user the result (and the carousel `_overview.png`), then iterate on their feedback by editing the spec — never start over without reason.

## 6. Deliver

- Final files: PNG for graphics/text-heavy posts, JPG (q92) for photo-heavy; sRGB; metadata stripped (the renderer does this). Delete `.guides.png` files from the final folder, or keep them only if asked.
- If requested, write `posts/<...>/caption.md` with caption (in the brand voice and chosen language), hashtags, alt text per image, and posting notes.
- Offer to save the spec as a reusable template (`templates/<name>.json`) for the series.

## Scope notes

- This skill makes static images. For animated posts/reels hand off to a video skill (e.g. `video-editing` or HyperFrames).
- ImageMagick cannot generate photos; if the user wants AI-generated imagery, say so and ask which tool they use, or design type/graphic-led.
- Don't publish or schedule posts; deliver files.
