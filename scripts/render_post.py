#!/usr/bin/env python3
"""Render social media posts from a JSON spec using ImageMagick 7 (`magick`).

Usage:
  render_post.py spec.json [--guides] [--overview]

Spec (single post):
{
  "brand": "brand/brand.json",          # optional, enables $tokens
  "format": "ig-portrait",               # preset name or {"width":1080,"height":1350}
  "output": "posts/2026-11-20-launch/post.png",
  "background": {"color": "$primary"}   # or {"gradient": ["#111","#333"], "angle": 135}
                                         # or {"image": "photo.jpg", "blur": 0, "darken": 0.3, "focus": "center"}
  "layers": [ ...layer objects... ],
  "grain": 0.0                           # optional film grain 0..1
}

Carousel: same top-level keys plus "slides": [{...slide spec...}], and optional
"common_layers": [...] appended to every slide. "output" may contain {n}.
Text may contain {n} and {total} (e.g. page counters).

Layer types:
  text  : text, font, size, color, x, y, width, height, anchor, align,
          line_spacing, kerning, uppercase, stroke, stroke_width,
          box: {color, padding, radius}
  image : src, x, y, width, height, anchor, fit (cover|contain), radius, shadow, opacity
  logo  : src, width|height, anchor, x, y, recolor, opacity
  rect  : x, y, width, height, anchor, color, radius, opacity
  scrim : from (top|bottom|left|right), size (0..1 of canvas), color, opacity

Positions: numbers are px; strings like "8%" are relative to canvas width (x/width)
or height (y/height). x/y are inward offsets from the anchor:
top-left (default), top, top-right, left, center, right, bottom-left, bottom, bottom-right.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

FORMATS = {
    # name: (w, h, safe-zone insets top, right, bottom, left)
    "ig-square": (1080, 1080, (0, 0, 0, 0)),
    "ig-portrait": (1080, 1350, (0, 0, 0, 0)),
    "ig-portrait-34": (1080, 1440, (0, 0, 0, 0)),
    "ig-story": (1080, 1920, (250, 60, 340, 60)),
    "ig-reel-cover": (1080, 1920, (240, 60, 420, 60)),
    "tiktok": (1080, 1920, (160, 140, 480, 60)),
    "fb-post": (1080, 1350, (0, 0, 0, 0)),
    "fb-link": (1200, 630, (0, 0, 0, 0)),
    "linkedin-post": (1200, 1500, (0, 0, 0, 0)),
    "linkedin-square": (1200, 1200, (0, 0, 0, 0)),
    "linkedin-link": (1200, 627, (0, 0, 0, 0)),
    "x-post": (1600, 900, (0, 0, 0, 0)),
    "yt-thumbnail": (1280, 720, (0, 220, 120, 0)),
    "pinterest": (1000, 1500, (0, 0, 0, 0)),
}

ANCHORS = {
    "top-left": (0, 0), "top": (1, 0), "top-right": (2, 0),
    "left": (0, 1), "center": (1, 1), "right": (2, 1),
    "bottom-left": (0, 2), "bottom": (1, 2), "bottom-right": (2, 2),
}

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print(f"WARN: {msg}", file=sys.stderr)


def run(args):
    r = subprocess.run(["magick", *map(str, args)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"magick failed: {' '.join(map(str, args))}\n{r.stderr}")
    return r.stdout


def dims(path):
    w, h = run(["identify", "-format", "%w %h", path]).split()
    return int(w), int(h)


# ---------- brand tokens ----------

PREFERRED = {"src": "logos", "font": "fonts", "image": "logos"}


def resolve_tokens(obj, brand, key_name=None):
    """Replace "$name" / "$section.name" strings with values from brand.json.
    Bare names are looked up in the section that fits the field (src->logos,
    font->fonts, everything else->colors), then in the other sections."""
    if isinstance(obj, dict):
        return {k: resolve_tokens(v, brand, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_tokens(v, brand, key_name) for v in obj]
    if isinstance(obj, str) and obj.startswith("$"):
        key = obj[1:]
        first = PREFERRED.get(key_name, "colors")
        sections = [first] + [s for s in ("colors", "fonts", "logos") if s != first]
        for candidate in [key] + [f"{s}.{key}" for s in sections]:
            cur = brand
            ok = True
            for part in candidate.split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    ok = False
                    break
            if ok and not (isinstance(cur, dict) and candidate == key):
                if isinstance(cur, dict):  # fonts: {"file": ..., "family": ...}
                    cur = cur.get("file") or cur.get("family") or cur.get("path")
                return cur
        sys.exit(f"Unknown brand token: {obj}")
    return obj


def rel_paths(obj, base, keys=("src", "image", "font", "file")):
    """Make relative asset paths resolve against the spec's directory."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in keys and isinstance(v, str) and not os.path.isabs(v):
                cand = os.path.join(base, v)
                out[k] = cand if os.path.exists(cand) else v
            else:
                out[k] = rel_paths(v, base, keys)
        return out
    if isinstance(obj, list):
        return [rel_paths(v, base, keys) for v in obj]
    return obj


# ---------- geometry ----------

def px(v, total, default=0):
    if v is None:
        return default
    if isinstance(v, str) and v.endswith("%"):
        return round(float(v[:-1]) / 100 * total)
    return round(float(v))


def place(layer, w, h, W, H):
    ax, ay = ANCHORS.get(layer.get("anchor", "top-left"), (0, 0))
    ox, oy = px(layer.get("x"), W), px(layer.get("y"), H)
    x = [ox, (W - w) // 2 + ox, W - w - ox][ax]
    y = [oy, (H - h) // 2 + oy, H - h - oy][ay]
    return x, y


# ---------- color / contrast ----------

def hex_to_rgb(c):
    out = run(["xc:" + c, "-format", "%[fx:int(255*r)] %[fx:int(255*g)] %[fx:int(255*b)]", "info:"])
    return tuple(int(v) for v in out.split())


def luminance(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------- layer builders (each returns a PNG path) ----------

def rounded_mask(w, h, r, out):
    run(["-size", f"{w}x{h}", "xc:none", "-fill", "white",
         "-draw", f"roundrectangle 0,0,{w-1},{h-1},{r},{r}", out])


def apply_opacity(path, opacity):
    if opacity is not None and float(opacity) < 1:
        run([path, "-alpha", "on", "-channel", "A", "-evaluate", "multiply", opacity, "+channel", path])


def build_rect(L, W, H, tmp, i):
    w, h = px(L.get("width"), W, W), px(L.get("height"), H, H)
    out = f"{tmp}/l{i}.png"
    r = L.get("radius", 0)
    run(["-size", f"{w}x{h}", "xc:none", "-fill", L.get("color", "#000"),
         "-draw", f"roundrectangle 0,0,{w-1},{h-1},{r},{r}", out])
    apply_opacity(out, L.get("opacity"))
    return out


def build_scrim(L, W, H, tmp, i):
    side = L.get("from", "bottom")
    frac = float(L.get("size", 0.5))
    color = L.get("color", "#000000")
    op = float(L.get("opacity", 0.75))
    vertical = side in ("top", "bottom")
    w, h = (W, round(H * frac)) if vertical else (round(W * frac), H)
    out = f"{tmp}/l{i}.png"
    # alpha ramp: transparent at the inner edge -> opaque at the `from` edge
    rot = {"bottom": 0, "top": 180, "right": 270, "left": 90}[side]
    gw, gh = (w, h) if vertical else (h, w)
    run(["(", "-size", f"{gw}x{gh}", "gradient:black-white", "-evaluate", "pow", "0.6", "-rotate", rot, ")",
         "(", "-size", f"{w}x{h}", f"xc:{color}", ")", "+swap",
         "-alpha", "off", "-compose", "CopyOpacity", "-composite",
         "-channel", "A", "-evaluate", "multiply", op, "+channel", out])
    L = dict(L, anchor={"bottom": "bottom-left", "top": "top-left",
                        "left": "top-left", "right": "top-right"}[side], x=0, y=0)
    return out, L


def build_image(L, W, H, tmp, i):
    src = L["src"]
    if not os.path.exists(src):
        sys.exit(f"Image not found: {src}")
    w, h = px(L.get("width"), W, 0), px(L.get("height"), H, 0)
    out = f"{tmp}/l{i}.png"
    fit = L.get("fit", "cover")
    gravity = L.get("focus", "center").replace("-", "")
    gravity = {"topleft": "NorthWest", "top": "North", "topright": "NorthEast", "left": "West",
               "center": "Center", "right": "East", "bottomleft": "SouthWest", "bottom": "South",
               "bottomright": "SouthEast"}.get(gravity, "Center")
    args = [src, "-auto-orient", "-colorspace", "sRGB"]
    if w and h:
        if fit == "cover":
            args += ["-resize", f"{w}x{h}^", "-gravity", gravity, "-extent", f"{w}x{h}"]
        else:
            args += ["-resize", f"{w}x{h}", "-background", "none", "-gravity", "center", "-extent", f"{w}x{h}"]
    elif w:
        args += ["-resize", f"{w}x"]
    elif h:
        args += ["-resize", f"x{h}"]
    if L.get("recolor"):
        args += ["-alpha", "on", "-fill", L["recolor"], "-colorize", "100%"]
    if L.get("grayscale"):
        args += ["-colorspace", "Gray", "-colorspace", "sRGB"]
    if L.get("duotone"):
        dark, light = L["duotone"]
        args += ["-colorspace", "Gray", "(", "-size", "1x256", f"gradient:{light}-{dark}", ")", "-clut"]
    args += ["+repage", out]
    run(args)
    rw, rh = dims(out)
    if L.get("radius"):
        m = f"{tmp}/m{i}.png"
        rounded_mask(rw, rh, L["radius"], m)
        run([out, m, "-alpha", "on", "-compose", "DstIn", "-composite", out])
    apply_opacity(out, L.get("opacity"))
    if L.get("shadow"):
        s = L["shadow"] if isinstance(L["shadow"], dict) else {}
        op, sigma, oy = s.get("opacity", 45), s.get("blur", 24), s.get("offset", 16)
        run([out, "(", "+clone", "-background", s.get("color", "black"), "-shadow", f"{op}x{sigma}+0+{oy}", ")",
             "+swap", "-background", "none", "-layers", "merge", "+repage", out])
        L = dict(L, _shift=(-2 * sigma, min(0, oy - 2 * sigma)))
    return out, L


def build_text(L, W, H, tmp, i, n=None, total=None):
    text = str(L.get("text", ""))
    if n is not None:
        text = text.replace("{n}", str(n)).replace("{total}", str(total))
    if L.get("uppercase"):
        text = text.upper()
    tf = f"{tmp}/t{i}.txt"
    with open(tf, "w") as f:
        f.write(text)
    w = px(L.get("width"), W, 0)
    h = px(L.get("height"), H, 0)
    align = {"left": "West", "center": "Center", "right": "East"}[L.get("align", "left")]
    out = f"{tmp}/l{i}.png"
    args = ["-background", "none", "-fill", L.get("color", "#000")]
    font = L.get("font")
    if not font:
        warn(f"Text '{text[:30]}' has no font set; using ImageMagick's default. Set a brand font.")
    if font:
        if not os.path.exists(font) and not fontconfig_has(font):
            warn(f"Font '{font}' not found; ImageMagick will fall back to a default font.")
        args += ["-font", font]
    if L.get("size"):
        args += ["-pointsize", L["size"]]
    if L.get("line_spacing") is not None:
        args += ["-interline-spacing", L["line_spacing"]]
    if L.get("kerning") is not None:
        args += ["-kerning", L["kerning"]]
    if L.get("stroke"):
        args += ["-stroke", L["stroke"], "-strokewidth", L.get("stroke_width", 2)]
    args += ["-gravity", align]
    if w:
        args += ["-size", f"{w}x{h}" if h else f"{w}x", f"caption:@{tf}"]
    else:
        args += [f"label:@{tf}"]
    args += ["-trim" if L.get("trim") else "+repage", "+repage", out]
    run(args)
    box = L.get("box")
    if box:
        p = box.get("padding", 24)
        tw, th = dims(out)
        bw, bh = tw + 2 * p, th + 2 * p
        r = box.get("radius", 0)
        run(["-size", f"{bw}x{bh}", "xc:none", "-fill", box.get("color", "#000"),
             "-draw", f"roundrectangle 0,0,{bw-1},{bh-1},{r},{r}",
             out, "-gravity", "center", "-compose", "over", "-composite", out])
    return out, L


_FONT_CACHE = None


def fontconfig_has(name):
    global _FONT_CACHE
    if _FONT_CACHE is None:
        _FONT_CACHE = run(["-list", "font"]).lower()
    return f"font: {name.lower()}" in _FONT_CACHE or f"family: {name.lower()}" in _FONT_CACHE


# ---------- rendering ----------

def render(spec, base, guides=False, n=None, total=None):
    fmt = spec.get("format", "ig-portrait")
    if isinstance(fmt, dict):
        W, H, safe = fmt["width"], fmt["height"], tuple(fmt.get("safe", (0, 0, 0, 0)))
    else:
        if fmt not in FORMATS:
            sys.exit(f"Unknown format '{fmt}'. Known: {', '.join(FORMATS)}")
        W, H, safe = FORMATS[fmt]
    out = spec["output"].replace("{n}", f"{n:02d}" if n else "")
    out = out if os.path.isabs(out) else os.path.join(base, out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    tmp = tempfile.mkdtemp(prefix="smp-")
    try:
        # background
        bg = spec.get("background", {"color": "#ffffff"})
        bgp = f"{tmp}/bg.png"
        if "image" in bg:
            gravity = {"top": "North", "bottom": "South", "left": "West", "right": "East"}.get(bg.get("focus"), "Center")
            args = [bg["image"], "-auto-orient", "-colorspace", "sRGB", "-resize", f"{W}x{H}^",
                    "-gravity", gravity, "-extent", f"{W}x{H}"]
            if bg.get("blur"):
                args += ["-blur", f"0x{bg['blur']}"]
            if bg.get("grayscale"):
                args += ["-colorspace", "Gray", "-colorspace", "sRGB"]
            if bg.get("darken"):
                args += ["-fill", "black", "-colorize", f"{float(bg['darken'])*100:.0f}%"]
            if bg.get("tint"):
                args += ["-fill", bg["tint"], "-colorize", f"{float(bg.get('tint_amount', 0.3))*100:.0f}%"]
            run(args + ["+repage", bgp])
        elif "gradient" in bg:
            a, b = bg["gradient"][:2]
            run(["-size", f"{W}x{H}", "-define", f"gradient:angle={bg.get('angle', 180)}",
                 f"gradient:{a}-{b}", bgp])
        else:
            run(["-size", f"{W}x{H}", f"xc:{bg.get('color', '#ffffff')}", bgp])

        built = []  # (path, x, y, layer)
        for i, L in enumerate(spec.get("layers", [])):
            t = L.get("type")
            if t == "text":
                p, L = build_text(L, W, H, tmp, i, n, total)
            elif t in ("image", "logo"):
                if t == "logo" and "width" not in L and "height" not in L:
                    L = dict(L, width=round(W * 0.14))
                p, L = build_image(dict(L, fit=L.get("fit", "contain" if t == "logo" else "cover")) if t == "image"
                                   else L, W, H, tmp, i)
            elif t == "rect":
                p = build_rect(L, W, H, tmp, i)
            elif t == "scrim":
                p, L = build_scrim(L, W, H, tmp, i)
            else:
                sys.exit(f"Unknown layer type: {t}")
            w, h = dims(p)
            x, y = place(L, w, h, W, H)
            sx, sy = L.get("_shift", (0, 0))
            built.append((p, x + sx, y + sy, L, (x, y, w, h)))

        # contrast check: render everything except text, sample under each text box
        nontext = [b for b in built if b[3].get("type") != "text"]
        probe = f"{tmp}/probe.png"
        composite(bgp, nontext, probe)
        for p, x, y, L, (bx, by, bw, bh) in built:
            if L.get("type") != "text":
                continue
            if L.get("box"):
                continue
            cx, cy = max(0, bx), max(0, by)
            cw, ch = max(1, min(bw, W - cx)), max(1, min(bh, H - cy))
            mean = run([probe, "-crop", f"{cw}x{ch}+{cx}+{cy}", "+repage", "-resize", "1x1!",
                        "-format", "%[fx:int(255*r)] %[fx:int(255*g)] %[fx:int(255*b)]", "info:"])
            under = tuple(int(v) for v in mean.split())
            ratio = contrast(hex_to_rgb(L.get("color", "#000")), under)
            need = 3.0 if float(L.get("size", 0) or 0) >= 48 else 4.5
            label = str(L.get("text", ""))[:30].replace("\n", " ")
            if ratio < need:
                warn(f"Low contrast {ratio:.1f}:1 (need {need}) for text '{label}' — add a scrim/box or change color.")
            # bounds / safe zone
            st, sr, sb, sl = safe
            if bx < sl or by < st or bx + bw > W - sr or by + bh > H - sb:
                warn(f"Text '{label}' is outside the safe zone for {fmt}.")

        composite(bgp, built, out)
        if spec.get("grain"):
            g = float(spec["grain"])
            run([out, "(", "-size", f"{W}x{H}", "xc:gray50", "-attenuate", g * 2, "+noise", "Gaussian",
                 "-colorspace", "Gray", ")", "-compose", "Overlay", "-composite", out])
        if out.lower().endswith((".jpg", ".jpeg")):
            run([out, "-strip", "-quality", "92", "-colorspace", "sRGB", out])
        else:
            run([out, "-strip", "-colorspace", "sRGB", out])

        if guides:
            gp = re.sub(r"(\.\w+)$", r".guides\1", out)
            st, sr, sb, sl = safe
            draw = ["-fill", "none", "-stroke", "#ff2d55", "-strokewidth", "3"]
            if any(safe):
                draw += ["-draw", f"rectangle {sl},{st} {W-sr},{H-sb}"]
            draw += ["-stroke", "#00c2ff", "-strokewidth", "2"]
            for p, x, y, L, (bx, by, bw, bh) in built:
                if L.get("type") in ("text", "logo"):
                    draw += ["-draw", f"rectangle {bx},{by} {bx+bw},{by+bh}"]
            if W == 1080 and H == 1920:  # 3:4 grid crop preview for reels/stories
                top = (1920 - 1440) // 2
                draw += ["-stroke", "#ffd60a", "-draw", f"rectangle 0,{top} 1080,{top+1440}"]
            if W == 1080 and H == 1350:  # 4:5 post shown as a 3:4 tile in the profile grid -> sides cropped
                vis = H * 3 // 4
                left = (W - vis) // 2
                draw += ["-stroke", "#ffd60a", "-draw", f"rectangle {left},0 {left+vis},{H}"]
            run([out, *draw, gp])
            print(f"guides: {gp}")
        print(f"rendered: {out} ({W}x{H})")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def composite(bgp, layers, out):
    args = [bgp]
    for p, x, y, *_ in layers:
        args += [p, "-gravity", "NorthWest", "-geometry", f"{x:+d}{y:+d}", "-compose", "over", "-composite"]
    run(args + ["-alpha", "remove", "-alpha", "off", out])


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("Formats:", ", ".join(f"{k} {v[0]}x{v[1]}" for k, v in FORMATS.items()))
        return
    if not shutil.which("magick"):
        sys.exit("ImageMagick 7 (`magick`) not found. Install it first.")
    spec_path = argv[0]
    guides = "--guides" in argv
    base = os.path.dirname(os.path.abspath(spec_path))
    with open(spec_path) as f:
        spec = json.load(f)
    brand = {}
    if spec.get("brand"):
        bp = spec["brand"] if os.path.isabs(spec["brand"]) else os.path.join(base, spec["brand"])
        with open(bp) as f:
            brand = json.load(f)
        bdir = os.path.dirname(bp)
        brand = rel_paths(brand, bdir, keys=("src", "image", "font", "file", "path", "guidelines"))
        for k, v in (brand.get("logos") or {}).items():
            if isinstance(v, str) and not os.path.isabs(v):
                brand["logos"][k] = os.path.join(bdir, v)
    spec = resolve_tokens(rel_paths(spec, base), brand)

    if "slides" in spec:
        slides = spec["slides"]
        total = len(slides)
        outs = []
        for n, s in enumerate(slides, 1):
            merged = {k: v for k, v in spec.items() if k not in ("slides", "common_layers")}
            merged.update({k: v for k, v in s.items() if k != "layers"})
            merged["layers"] = s.get("layers", []) + spec.get("common_layers", [])
            if "{n}" not in merged["output"]:
                root, ext = os.path.splitext(merged["output"])
                merged["output"] = f"{root}-{{n}}{ext}"
            outs.append(render(merged, base, guides, n, total))
        if "--overview" in argv and outs:
            ov = os.path.join(os.path.dirname(outs[0]), "_overview.png")
            run(["montage", *outs, "-tile", f"{min(total, 5)}x", "-geometry", "360x+12+12",
                 "-background", "#e9e9e9", ov])
            print(f"overview: {ov}")
    else:
        render(spec, base, guides)

    if WARNINGS:
        print(f"\n{len(WARNINGS)} warning(s) — review before delivering.", file=sys.stderr)


if __name__ == "__main__":
    main()
