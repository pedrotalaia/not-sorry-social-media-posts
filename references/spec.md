# render_post.py spec reference

```bash
python3 scripts/render_post.py spec.json [--guides] [--overview]
```
`--guides` writes `<name>.guides.png` with safe zone (red), text/logo boxes (blue) and grid crop (yellow).
`--overview` (carousels) writes `_overview.png` with all slides side by side.

Paths in a spec are relative to the spec file. Rendering order = layer order (first = bottom).

## Top level

| Key | Value |
|---|---|
| `brand` | path to brand.json (enables `$tokens`) |
| `format` | preset name (see formats.md) or `{"width","height","safe":[t,r,b,l]}` |
| `output` | output path (`.png` or `.jpg`); carousels may use `{n}` |
| `background` | `{"color": "#hex"}` · `{"gradient": ["#a","#b"], "angle": 135}` · `{"image": "photo.jpg", "focus": "top", "blur": 8, "darken": 0.3, "grayscale": true, "tint": "#hex", "tint_amount": 0.3}` |
| `layers` | list of layers |
| `grain` | 0–1 film grain over the final image (0.04–0.08 is subtle) |
| `slides` | carousel: list of per-slide specs (any top-level key can be overridden per slide) |
| `common_layers` | carousel: layers appended on top of every slide |

## Position & size (all layers)

- `anchor`: `top-left` (default), `top`, `top-right`, `left`, `center`, `right`, `bottom-left`, `bottom`, `bottom-right`
- `x`, `y`: inward offset from the anchor; px number or `"8%"` (of canvas width for x/width, height for y/height)
- `width`, `height`: px or `%`

## Layers

**text**
```json
{"type":"text","text":"Line one\nLine two","font":"$heading","size":96,"color":"$text_inverse",
 "width":"84%","x":"8%","y":"12%","anchor":"bottom-left","align":"left",
 "line_spacing":-8,"kerning":-1,"uppercase":false,
 "stroke":"#000","stroke_width":2,
 "box":{"color":"$accent","padding":20,"radius":12}}
```
- With `width`: wraps (caption). Without: single line (label), `\n` still breaks lines.
- `width` + `height` without `size`: auto-fits the text into the box.
- `align`: left | center | right (inside the text box). `{n}`/`{total}` are replaced in carousels.
- Contrast is checked against what's under the text box (except when it has a `box`).

**image**
```json
{"type":"image","src":"photos/team.jpg","width":"84%","height":"50%","anchor":"top","y":"8%",
 "fit":"cover","focus":"top","radius":28,"shadow":{"opacity":45,"blur":24,"offset":16},
 "opacity":1,"grayscale":false,"duotone":["#0E3B43","#F2A541"]}
```
- `fit`: cover (crop to fill, default) | contain (letterbox, transparent). `focus` picks the crop side.
- `duotone`: [shadows, highlights].

**logo** — like image, defaults to 14% canvas width and `contain`.
```json
{"type":"logo","src":"$light","width":160,"anchor":"bottom-right","x":64,"y":64,"recolor":"#FFFFFF"}
```

**rect**
```json
{"type":"rect","width":"100%","height":220,"anchor":"bottom","color":"$primary","radius":0,"opacity":0.9}
```

**scrim** — gradient from an edge for text legibility over photos.
```json
{"type":"scrim","from":"bottom","size":0.55,"color":"#000000","opacity":0.75}
```

## Example — carousel

```json
{
  "brand": "../../brand/brand.json",
  "format": "ig-portrait",
  "output": "slide.png",
  "background": {"color": "$background"},
  "common_layers": [
    {"type":"logo","src":"$mark","width":72,"anchor":"bottom-left","x":64,"y":56},
    {"type":"text","text":"{n}/{total}","font":"$body","size":28,"color":"$text","anchor":"bottom-right","x":64,"y":64}
  ],
  "slides": [
    {"background":{"color":"$primary"},
     "layers":[{"type":"text","text":"5 erros a evitar no teu primeiro logótipo","font":"$heading","size":104,
                "color":"$text_inverse","width":"84%","anchor":"left","x":"8%"}]},
    {"layers":[{"type":"text","text":"1. Demasiados detalhes","font":"$heading","size":72,"color":"$primary","width":"84%","x":"8%","y":"12%"},
               {"type":"text","text":"Um logo tem de funcionar a 32px…","font":"$body","size":38,"color":"$text","width":"84%","x":"8%","y":"28%","line_spacing":8}]}
  ]
}
```
Note: in this example, `common_layers` text uses `$text` — on slide 1 (primary background) that will trigger a contrast warning; override by giving slide 1 its own counter or use a color that works on both.
