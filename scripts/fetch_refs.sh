#!/usr/bin/env bash
# Download visual references (Instagram, Pinterest, Behance, direct images...) into a moodboard folder.
# Usage: fetch_refs.sh [-d moodboard/refs] [-b chrome|firefox|brave...] [-v] URL... | -f urls.txt
#   -b  browser to borrow login cookies from (Instagram usually requires being logged in)
#   -v  also download videos (reels) and extract 4 still frames from each
#   -m  max images per URL (default 20; stops profile/board URLs from pulling whole accounts)
# Strategy per URL: direct image -> curl; otherwise gallery-dl (best for IG image/carousel posts)
#   -> yt-dlp (reels/videos; thumbnail + caption metadata) -> report failure with manual fallback.
set -uo pipefail
DEST="moodboard/refs"; BROWSER="${SMP_COOKIES_BROWSER:-}"; VIDEO=0; MAX=20; URLS=()
while getopts "d:b:vf:m:" o; do case $o in
  d) DEST=$OPTARG;; m) MAX=$OPTARG;; b) BROWSER=$OPTARG;; v) VIDEO=1;;
  f) while IFS= read -r l; do [[ -z "$l" || "$l" == \#* ]] || URLS+=("$l"); done < "$OPTARG";;
  *) exit 1;; esac; done
shift $((OPTIND-1)); URLS+=("$@")
[ ${#URLS[@]} -gt 0 ] || { echo "usage: fetch_refs.sh [-d dir] [-b browser] [-v] URL... | -f urls.txt" >&2; exit 1; }
mkdir -p "$DEST"
command -v gallery-dl >/dev/null || echo "WARN: gallery-dl not installed — Instagram image posts/carousels will likely fail (uv tool install git+https://github.com/mikf/gallery-dl)" >&2
LOG="$DEST/_sources.md"; [ -f "$LOG" ] || printf '# Reference sources\n\nReferences are for inspiration only — do not reuse them in final posts.\n\n' > "$LOG"

UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
COOK=(); [ -n "$BROWSER" ] && COOK=(--cookies-from-browser "$BROWSER")
ok=0; fail=0; FAILED=()

slug() { echo "$1" | sed -E 's#https?://(www\.)?##; s#[/?&=:]+#_#g; s#_+$##' | cut -c1-60; }

for url in "${URLS[@]}"; do
  s=$(slug "$url"); got=0
  echo ">> $url"
  # 1) direct image
  ctype=$(curl -sIL -A "$UA" --max-time 15 "$url" | grep -i '^content-type:' | tail -1 | tr -d '\r' | awk '{print $2}')
  if [[ "$ctype" == image/* ]]; then
    ext=${ctype#image/}; ext=${ext%%;*}; [ "$ext" = jpeg ] && ext=jpg
    s=$(echo "$s" | sed -E "s/\.(jpe?g|png|webp|gif|avif)$//I")
    curl -sL -A "$UA" --max-time 60 "$url" -o "$DEST/$s.$ext" && got=1
  fi
  # 2) gallery-dl (handles IG image posts & carousels, Pinterest, Behance, Tumblr, ...)
  if [ $got -eq 0 ] && command -v gallery-dl >/dev/null; then
    GDC=(); [ -n "$BROWSER" ] && GDC=(--cookies-from-browser "$BROWSER")
    if gallery-dl "${GDC[@]}" --range "1-$MAX" -D "$DEST/$s" --write-metadata "$url" >/dev/null 2>&1 && [ -n "$(ls -A "$DEST/$s" 2>/dev/null)" ]; then got=1; fi
  fi
  # 3) yt-dlp (reels / video posts; grabs thumbnail + caption metadata)
  if [ $got -eq 0 ] && command -v yt-dlp >/dev/null; then
    mkdir -p "$DEST/$s"
    if yt-dlp "${COOK[@]}" --skip-download --write-thumbnail --convert-thumbnails jpg --write-info-json \
        -o "$DEST/$s/%(id)s.%(ext)s" "$url" >/dev/null 2>&1 && ls "$DEST/$s"/*.jpg >/dev/null 2>&1; then
      got=1
      if [ $VIDEO -eq 1 ]; then
        yt-dlp "${COOK[@]}" -f 'mp4/best' -o "$DEST/$s/%(id)s.%(ext)s" "$url" >/dev/null 2>&1
        for v in "$DEST/$s"/*.mp4; do
          [ -f "$v" ] || continue
          d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v" 2>/dev/null | cut -d. -f1); d=${d:-8}
          for k in 1 2 3 4; do ffmpeg -v error -y -ss $(( d*k/5 )) -i "$v" -frames:v 1 "${v%.mp4}-frame$k.jpg"; done
        done
      fi
    else
      rmdir "$DEST/$s" 2>/dev/null
    fi
  fi
  if [ $got -eq 1 ]; then ok=$((ok+1)); echo "- [$s]($url)" >> "$LOG"; echo "   saved"
  else fail=$((fail+1)); FAILED+=("$url"); echo "   FAILED"; fi
done

echo
echo "Fetched $ok, failed $fail -> $DEST"
if [ $fail -gt 0 ]; then
  echo "Failed URLs:"; printf '  %s\n' "${FAILED[@]}"
  cat <<'EOF'
Fallbacks:
  - Instagram usually needs a login: re-run with -b chrome (or firefox/brave) while logged in there.
  - Image-only IG posts: yt-dlp reports "no video"; they need gallery-dl (uv tool install git+https://github.com/mikf/gallery-dl) + login cookies (-b).
  - Or screenshot the post in the browser (Claude in Chrome) / have the user drop screenshots into the folder.
EOF
fi
