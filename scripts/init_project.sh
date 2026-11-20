#!/usr/bin/env bash
# Create the recommended social-media-posts folder structure in a project.
# Only creates what is missing — never moves, renames or overwrites existing files.
# Usage: init_project.sh [folder=.]
set -euo pipefail
ROOT="${1:-.}"
mkdir -p "$ROOT" && cd "$ROOT"

created=()
mk() { for d in "$@"; do [ -d "$d" ] || { mkdir -p "$d"; created+=("$d/"); }; done; }
put() { [ -e "$1" ] || { cat > "$1"; created+=("$1"); }; }

mk brand/logos brand/fonts brand/guidelines assets/photos assets/graphics moodboard/refs templates posts

put brief.md <<'EOF'
# Brief

- Brand / client:
- Platform(s) & format:
- Content type (post, carousel, story, reel cover…):
- Goal & audience:
- Language:
- Copy (headline / body / CTA):
- Imagery to use:
- Deadline:
- Notes / must-avoid:
EOF

put moodboard/urls.txt <<'EOF'
# One reference URL per line (Instagram posts/reels, Pinterest, Behance, direct images).
# Lines starting with # are ignored. Fetch with:
#   scripts/fetch_refs.sh -d moodboard/refs -f moodboard/urls.txt -b chrome
EOF

put moodboard/notes.md <<'EOF'
# Moodboard notes

What we like about each reference (palette, type, composition, photo treatment):
EOF

if [ ${#created[@]} -gt 0 ]; then
  echo "Created:"; printf '  %s\n' "${created[@]}"
else
  echo "Structure already in place — nothing created."
fi
echo "brand/brand.json is not created here; it is written after the brand intake."
