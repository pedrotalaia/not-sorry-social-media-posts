# Moodboards & references

## Folder layout

```
moodboard/
  urls.txt          # one URL per line (# comments allowed)
  refs/             # fetched or dropped-in images
    _sources.md     # auto-written list of where each ref came from
  _board.png        # contact sheet + palette (scripts/moodboard.sh)
  _palette.png
  notes.md          # what we like about each ref (you write this with the user)
```

## Fetching

```bash
scripts/fetch_refs.sh -d moodboard/refs -f moodboard/urls.txt -b chrome
scripts/fetch_refs.sh -d moodboard/refs -v https://www.instagram.com/reel/XXXX/   # + 4 frames from the video
```

Order of attempts per URL:
1. **Direct image URL** → curl.
2. **gallery-dl** → Instagram image posts & carousels (all slides), Pinterest, Behance, Tumblr, Flickr, etc. Install: `uv tool install git+https://github.com/mikf/gallery-dl`.
3. **yt-dlp** → Instagram reels/video posts, TikTok, YouTube: saves the thumbnail (cover frame) + `.info.json` with caption/description. Image-only IG posts fail here ("There is no video in this post").

Instagram notes:
- Logged-out access is heavily rate-limited; use `-b <browser>` (chrome, chromium, firefox, brave) to reuse that browser's logged-in cookies. Or set `SMP_COOKIES_BROWSER=firefox`.
- Prefer individual post URLs. Profile/board URLs are capped at 20 items per URL (`-m 12` to change).
- If everything fails: open the URL with Claude in Chrome and screenshot it, or ask the user to save screenshots into `moodboard/refs/`.

## Reading a board

After `scripts/moodboard.sh moodboard "Title"`, Read `_board.png` and note:
- Palette (the strip at the bottom + your eye — dominant vs accent colors)
- Typography: serif/sans/display, weight, case, size contrast, tracking
- Composition: centered vs asymmetric, density, whitespace, grids, framing
- Imagery: photo vs illustration, color grading (warm/cool, film, B&W, duotone), crops
- Graphic devices: shapes, stickers, outlines, textures/grain, rounded corners, shadows

Turn those into 2–3 named directions (e.g. "Editorial calm", "Bold blocks", "Warm film") and confirm one before rendering finals. Optionally render a quick low-fi sketch of each direction (same copy, different spec) for side-by-side comparison with `magick a.png b.png c.png -resize 540x +append directions.png`.

References are for inspiration — do not copy layouts 1:1 or reuse third-party images in final posts.
