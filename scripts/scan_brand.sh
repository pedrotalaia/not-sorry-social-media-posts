#!/usr/bin/env bash
# Scan a project folder for brand assets and print a grouped summary.
# Usage: scan_brand.sh [folder]   (default: current directory)
set -uo pipefail
ROOT="${1:-.}"
cd "$ROOT" || exit 1

FIND=(find . -maxdepth 5 -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.venv/*')

section() { printf '\n## %s\n' "$1"; }
list() { if [ -n "$1" ]; then printf '%s\n' "$1" | sed 's/^/- /' | head -n "${2:-40}"; else echo "- (none found)"; fi; }

echo "# Brand scan: $(pwd)"

section "Brand config (brand.json / brand.md)"
list "$("${FIND[@]}" \( -iname 'brand.json' -o -iname 'brand.md' -o -iname 'brand.y*ml' \))"

section "Guidelines / brand books"
list "$("${FIND[@]}" \( -iname '*guideline*' -o -iname '*brandbook*' -o -iname '*brand-book*' -o -iname '*manual*marca*' -o -iname '*normas*' -o -iname '*styleguide*' -o -iname '*style-guide*' -o -ipath '*/guidelines/*' \) )"

section "Logos"
LOGOS="$("${FIND[@]}" \( -ipath '*logo*' -o -iname '*logotipo*' -o -iname '*symbol*' -o -iname '*simbolo*' -o -iname '*marca*' -o -iname '*wordmark*' -o -iname '*monogram*' -o -iname '*isotipo*' \) \( -iname '*.svg' -o -iname '*.png' -o -iname '*.pdf' -o -iname '*.eps' -o -iname '*.ai' -o -iname '*.webp' \))"
if [ -n "$LOGOS" ]; then
  while IFS= read -r f; do
    info=$(magick identify -format '%wx%h %[channels]' "$f[0]" 2>/dev/null | head -c 60)
    echo "- $f  ${info:+($info)}"
  done <<< "$LOGOS" | head -40
else echo "- (none found)"; fi

section "Fonts"
FONTS="$("${FIND[@]}" \( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.woff' -o -iname '*.woff2' \))"
if [ -n "$FONTS" ]; then
  while IFS= read -r f; do
    fam=$(fc-scan --format '%{family[0]} / %{style[0]}' "$f" 2>/dev/null | head -1)
    case "$f" in *.woff|*.woff2) note=" [web font: convert to TTF/OTF before use]";; *) note="";; esac
    echo "- $f — ${fam:-unknown}$note"
  done <<< "$FONTS" | head -40
else echo "- (none found — ask the user or pick from: fc-list : family)"; fi

section "Color hints (files mentioning hex colors)"
"${FIND[@]}" \( -iname '*.md' -o -iname '*.txt' -o -iname '*.json' -o -iname '*.css' -o -iname '*.scss' -o -iname '*.ase' \) -size -200k 2>/dev/null \
  | xargs -r grep -oHiE '#[0-9a-f]{6}\b' 2>/dev/null | sort | uniq | awk -F: '{a[$1]=a[$1]" "$2} END{for(k in a) print "- "k":"a[k]}' | head -20
echo "(also run scripts/palette.sh on the logo to sample colors)"

section "Photos / imagery"
IMGS="$("${FIND[@]}" \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.heic' -o -iname '*.tif*' \) -not -ipath '*logo*' -not -ipath './moodboard/*' -not -ipath './posts/*' -not -ipath './output*')"
if [ -n "$IMGS" ]; then
  echo "- $(printf '%s\n' "$IMGS" | wc -l) image(s). Folders:"
  printf '%s\n' "$IMGS" | xargs -r -I{} dirname {} | sort | uniq -c | sort -rn | head -10 | sed 's/^/  /'
else echo "- (none found)"; fi

section "Moodboard / references"
list "$(find . -maxdepth 3 -type d \( -iname 'moodboard*' -o -iname 'refs' -o -iname 'references' -o -iname 'inspo*' -o -iname 'inspiration*' \) 2>/dev/null)"

section "Previous posts (for style continuity)"
list "$(find . -maxdepth 3 -type d \( -iname 'posts' -o -iname 'output*' -o -iname 'exports' -o -iname 'social*' \) 2>/dev/null)"

section "Project instructions"
list "$("${FIND[@]}" -maxdepth 2 \( -iname 'brief*.md' -o -name 'AGENTS.md' -o -name 'CLAUDE.md' -o -iname 'README.md' \))"
