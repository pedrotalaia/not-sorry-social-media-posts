# Formats & safe zones

Preset names are used in `"format"` of a spec. Safe-zone insets are top/right/bottom/left in px; the renderer warns when text leaves them and draws them in `--guides`.

| Preset | Size | Use | Safe zone (T/R/B/L) |
|---|---|---|---|
| `ig-portrait` | 1080×1350 (4:5) | Instagram feed default | — (grid shows it cropped to 3:4, see note) |
| `ig-portrait-34` | 1080×1440 (3:4) | Instagram feed, matches profile grid | — |
| `ig-square` | 1080×1080 | Instagram/Facebook feed | — |
| `ig-story` | 1080×1920 (9:16) | Stories | 250 / 60 / 340 / 60 |
| `ig-reel-cover` | 1080×1920 | Reel cover; grid shows the central 3:4 (1080×1440) | 240 / 60 / 420 / 60 |
| `tiktok` | 1080×1920 | TikTok cover/photo mode | 160 / 140 / 480 / 60 |
| `fb-post` | 1080×1350 | Facebook feed | — |
| `fb-link` | 1200×630 | Facebook link / OG image | — |
| `linkedin-post` | 1200×1500 (4:5) | LinkedIn feed | — |
| `linkedin-square` | 1200×1200 | LinkedIn feed | — |
| `linkedin-link` | 1200×627 | LinkedIn link / OG | — |
| `x-post` | 1600×900 (16:9) | X / Twitter | — |
| `yt-thumbnail` | 1280×720 | YouTube thumbnail (timestamp bottom-right) | 0 / 220 / 120 / 0 |
| `pinterest` | 1000×1500 (2:3) | Pinterest pin | — |

Custom: `"format": {"width": 1080, "height": 1350, "safe": [0,0,0,0]}`.

Notes
- Since 2025 the Instagram profile grid shows posts as 3:4 tiles. A 4:5 post (1080×1350) is shown cropped on the left and right in the grid (visible width ≈ 1012px, ~34px lost per side), so keep text off the side edges. `--guides` draws the visible grid area in yellow.
- LinkedIn PDF carousels: render slides at 1080×1350 or 1200×1500, then `magick slide-*.png carousel.pdf`.
- Carousel slides must all share one size (the first slide sets it on Instagram).
- Platform UI changes often; if the user reports a different safe area, use a custom format.
