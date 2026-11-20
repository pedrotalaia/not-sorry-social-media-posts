# Brand intake

## Questions (ask only what is missing)

1. Brand name, handle(s), website.
2. Brand guidelines / brand book? (PDF, Figma, Notion, link)
3. Colors — primary, secondary, accent, background, text (hex). Any colors to avoid?
4. Fonts — heading and body (files: TTF/OTF; or Google Fonts names). Weights in use?
5. Logos — full logo, symbol/mark, light (for dark backgrounds) and dark versions. SVG or transparent PNG preferred. Clear-space / minimum-size rules?
6. Imagery — photo style (bright/moody, people/product, studio/lifestyle), existing photo library, illustrations/icons, textures or patterns.
7. Tone of voice — 3 adjectives; formal vs casual; emoji yes/no; language(s).
8. Do / don't — anything the brand never does (e.g. no gradients, no all-caps, logo never on photos).
9. Recurring elements — frames, stickers, page counters, signature layouts, hashtags, CTA phrasing.

## brand/brand.json

Paths are relative to the brand.json file. Fonts may be a file or an installed family name.

```json
{
  "name": "Rumo Studio",
  "handle": "@rumostudio",
  "website": "rumostudio.pt",
  "language": "pt-PT",
  "colors": {
    "primary": "#0E3B43",
    "secondary": "#E8E2D6",
    "accent": "#F2A541",
    "background": "#FAF7F2",
    "text": "#111111",
    "text_inverse": "#FFFFFF"
  },
  "fonts": {
    "heading": {"file": "fonts/Inter-Bold.ttf", "family": "Inter Bold"},
    "body": {"file": "fonts/Inter-Regular.ttf", "family": "Inter"}
  },
  "logos": {
    "primary": "logos/logo.png",
    "light": "logos/logo-white.png",
    "dark": "logos/logo-black.png",
    "mark": "logos/symbol.png"
  },
  "logo_rules": {"min_width_px": 120, "clear_space": "height of the 'R'", "placement": "bottom-right"},
  "imagery": "Natural light, warm tones, people at work, no stock clichés",
  "voice": {"adjectives": ["direct", "warm", "confident"], "emoji": false},
  "do": ["Lots of whitespace", "Sentence case headlines"],
  "dont": ["Gradients", "Logo on busy photos"],
  "hashtags": ["#rumostudio"],
  "guidelines": "Brand-Guidelines.pdf"
}
```

Token lookup in specs: `"$primary"` → colors.primary (for `color` fields), `"$heading"` → fonts.heading (for `font`), `"$light"` → logos.light (for `src`). Fully qualified tokens like `"$logos.mark"` always work.

## Preparing assets

- SVG/PDF/AI/EPS logo → PNG: `magick -density 600 -background none logo.svg -resize 1600x logos/logo.png`
- Logo on white background → transparent: see "remove white background" in imagemagick-recipes.md
- White version of a dark logo: use `"recolor": "#FFFFFF"` on the logo layer (keeps alpha).
- WOFF2 → TTF: `uvx --from fonttools fonttools ttLib.woff2 decompress font.woff2` (outputs .ttf).
- Google Fonts: download the family TTFs into `fonts/` (check the license allows it — OFL fonts do).
- Sample colors from a logo/photo: `scripts/palette.sh -n 6 -o brand/palette.png logos/logo.png`.
