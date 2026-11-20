#!/usr/bin/env bash
# Extract a dominant color palette from one or more images.
# Usage: palette.sh [-n 6] [-o swatch.png] image [image...]
# Prints hex colors (most to least frequent) and optionally writes a swatch strip.
set -euo pipefail
N=6; OUT=""
UIFONT=$(fc-match -f "%{file}" "sans-serif:bold" 2>/dev/null)
while getopts "n:o:" o; do case $o in n) N=$OPTARG;; o) OUT=$OPTARG;; *) exit 1;; esac; done
shift $((OPTIND-1))
[ $# -ge 1 ] || { echo "usage: palette.sh [-n 6] [-o swatch.png] image..." >&2; exit 1; }

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
# normalize each image to a small tile, drop fully transparent pixels (logos), join
i=0; for f in "$@"; do
  magick "$f[0]" -auto-orient -colorspace sRGB -resize 160x160 -background none -gravity center -extent 160x160 "$TMP/$i.png"; i=$((i+1))
done
magick "$TMP"/*.png +append "$TMP/all.png"

HEX=$(magick "$TMP/all.png" -alpha on -channel A -threshold 50% +channel \
  -dither None -colors "$((N+1))" -type TrueColorAlpha -depth 8 -format '%c' histogram:info:- 2>/dev/null \
  | sort -t: -k1 -rn | grep -oE '#[0-9A-Fa-f]{8}' | grep -viE '00$' | cut -c1-7 | awk '!seen[toupper($0)]++' | head -n "$N")
echo "$HEX"

if [ -n "$OUT" ]; then
  args=()
  for h in $HEX; do
    args+=( "(" -size 200x240 "xc:$h" -gravity south -fill "$( magick xc:"$h" -format '%[fx:luma>0.55?0:1]' info: | sed 's/1/white/;s/0/black/')" ${UIFONT:+-font "$UIFONT"} -pointsize 22 -annotate +0+16 "$h" ")" )
  done
  magick "${args[@]}" +append "$OUT"
  echo "swatch: $OUT" >&2
fi
