#!/usr/bin/env bash
# Build a moodboard contact sheet + shared palette from every image in a folder (recursive).
# Usage: moodboard.sh [folder=moodboard] [title]
# Writes <folder>/_board.png and <folder>/_palette.png, prints the palette hex codes.
set -euo pipefail
DIR="${1:-moodboard}"; TITLE="${2:-Moodboard}"
UIFONT=$(fc-match -f "%{file}" "sans-serif:bold" 2>/dev/null)
HERE="$(cd "$(dirname "$0")" && pwd)"
mapfile -t IMGS < <(find "$DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.heic' \) \
  -not -name '_board.png' -not -name '_palette.png' | sort)
[ ${#IMGS[@]} -gt 0 ] || { echo "No images in $DIR" >&2; exit 1; }
n=${#IMGS[@]}; cols=$(( n < 4 ? n : (n <= 9 ? 3 : 4) ))

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
i=0; for f in "${IMGS[@]}"; do
  magick "$f[0]" -auto-orient -resize 420x525^ -gravity center -extent 420x525 "$TMP/$(printf %03d $i).png"; i=$((i+1))
done
magick montage "$TMP"/*.png -tile "${cols}x" -geometry +14+14 -background '#f3f1ec' "$TMP/grid.png"

"$HERE/palette.sh" -n 8 -o "$DIR/_palette.png" "${IMGS[@]}" > "$TMP/hex.txt"
gw=$(magick identify -format %w "$TMP/grid.png")
magick "$DIR/_palette.png" -resize "${gw}x" "$TMP/pal.png"
magick -size "${gw}x110" xc:'#f3f1ec' -fill '#222' ${UIFONT:+-font "$UIFONT"} -pointsize 46 -gravity west -annotate +28+0 "$TITLE" "$TMP/head.png" 2>/dev/null \
  || magick -size "${gw}x110" xc:'#f3f1ec' "$TMP/head.png"
magick "$TMP/head.png" "$TMP/grid.png" "$TMP/pal.png" -append "$DIR/_board.png"
echo "board: $DIR/_board.png ($n images)"
echo "palette:"; cat "$TMP/hex.txt"
