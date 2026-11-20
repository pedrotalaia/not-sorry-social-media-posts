```
███╗   ██╗  ██████╗  ████████╗     ███████╗  ██████╗  ██████╗  ██████╗  ██╗   ██╗
████╗  ██║ ██╔═══██╗ ╚══██╔══╝     ██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔══██╗ ╚██╗ ██╔╝
██╔██╗ ██║ ██║   ██║    ██║        ███████╗ ██║   ██║ ██████╔╝ ██████╔╝  ╚████╔╝
██║╚██╗██║ ██║   ██║    ██║        ╚════██║ ██║   ██║ ██╔══██╗ ██╔══██╗   ╚██╔╝
██║ ╚████║ ╚██████╔╝    ██║        ███████║ ╚██████╔╝ ██║  ██║ ██║  ██║    ██║
╚═╝  ╚═══╝  ╚═════╝     ╚═╝        ╚══════╝  ╚═════╝  ╚═╝  ╚═╝ ╚═╝  ╚═╝    ╚═╝
              ▶  S O C I A L   M E D I A   P O S T S   S K I L L  ◀
```

An agent skill that designs on-brand social media images with **ImageMagick 7**: intake → brand discovery → moodboard → render from a JSON spec → QA (contrast, safe zones, grid crop) → delivery with captions/alt text.

`SKILL.md` is what the agent reads. This file is for humans.

## Install

```bash
# dependencies
sudo pacman -S imagemagick ffmpeg        # or apt / brew
uv tool install git+https://github.com/mikf/gallery-dl   # from the original repo
uv tool install yt-dlp

# make the skill visible to Claude Code
ln -sfn ~/.agents/skills/not-sorry-social-media-posts ~/.claude/skills/social-media-posts
```

## Project folder layout

Run the agent inside one folder per brand/client. For a new project, the skill can scaffold this with `scripts/init_project.sh` (creates only missing folders and never moves or overwrites files):

```
<project>/
├── brief.md                  # what this batch of posts is for
├── brand/
│   ├── brand.json            # written by the skill after brand intake
│   ├── guidelines/           # brand book PDFs
│   ├── logos/                # SVG / transparent PNG (light, dark, mark)
│   └── fonts/                # TTF / OTF (not WOFF)
├── assets/
│   ├── photos/
│   └── graphics/             # icons, illustrations, textures
├── moodboard/
│   ├── urls.txt              # Instagram / Pinterest / Behance links
│   ├── refs/                 # downloaded or dropped-in references
│   ├── notes.md
│   └── _board.png            # generated contact sheet + palette
├── templates/                # reusable specs for recurring series
└── posts/YYYY-MM-DD-<slug>/  # spec.json, rendered PNG/JPGs, caption.md
```

Projects with a different structure still work: the skill scans for assets wherever they are and tells you what it found before using them.

## Scripts

| Script | What it does |
|---|---|
| `init_project.sh [dir]` | Create the folder layout above |
| `scan_brand.sh [dir]` | Find brand config, guidelines, logos, fonts, colors, photos, previous posts |
| `fetch_refs.sh -d moodboard/refs [-b chrome] [-v] [-m 20] URL… \| -f urls.txt` | Download references (curl → gallery-dl → yt-dlp) |
| `moodboard.sh [moodboard] [title]` | Contact sheet + shared palette → `_board.png` |
| `palette.sh [-n 6] [-o swatch.png] image…` | Dominant colors from images or logos |
| `render_post.py spec.json [--guides] [--overview]` | Render a post or carousel from a JSON spec |

## Instagram references

Image posts and carousels go through **gallery-dl**; reels and videos through **yt-dlp**. Instagram usually requires a login, so pass `-b chrome` (or firefox/brave) to reuse cookies from a browser where you're logged in. References are for inspiration only and never end up in final posts.

## Docs

- `references/spec.md`: JSON spec and layer options
- `references/formats.md`: platform sizes and safe zones
- `references/brand-intake.md`: brand questions and `brand.json` schema
- `references/moodboard.md`: fetching and reading moodboards
- `references/imagemagick-recipes.md`: duotone, masks, cut-outs, textures, text effects
