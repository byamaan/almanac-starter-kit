#!/usr/bin/env bash
# Almanac carousel renderer — Chrome headless + PIL crop.
# Renders 1080x1350 viewport at 2x DPR → 2160x2700 PNG.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$DIR/.tmp"
mkdir -p "$TMP"

# Cross-platform Chrome detection. Override with CHROME=... env var if needed.
if [ -z "${CHROME:-}" ]; then
  if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  elif command -v google-chrome >/dev/null 2>&1; then
    CHROME="$(command -v google-chrome)"
  elif command -v chromium >/dev/null 2>&1; then
    CHROME="$(command -v chromium)"
  elif command -v chromium-browser >/dev/null 2>&1; then
    CHROME="$(command -v chromium-browser)"
  else
    echo "error: Google Chrome / Chromium not found. Install one, or set CHROME env var to its path." >&2
    exit 1
  fi
fi

STAGE_W=1080
STAGE_H=1350
DPR=2

RENDER_W=${STAGE_W}
RENDER_H=$(( STAGE_H + 100 ))   # +100 buffer for the Chrome ~85px viewport-truncation bug

OUT_W=$(( STAGE_W * DPR ))
OUT_H=$(( STAGE_H * DPR ))

PREVIEW_W=${STAGE_W}
PREVIEW_H=${STAGE_H}

# Args: zero or more carousel folder names (e.g. almanac-01-<slug>) or specific
# html paths. With zero args, render every almanac-*/ folder.
TARGETS=()
if [ "$#" -eq 0 ]; then
  for d in "$DIR"/almanac-*/; do
    [ -d "$d" ] && TARGETS+=("$d")
  done
else
  for arg in "$@"; do
    if [ -d "$DIR/$arg" ]; then
      TARGETS+=("$DIR/$arg")
    elif [ -d "$arg" ]; then
      TARGETS+=("$arg")
    elif [ -f "$arg" ]; then
      TARGETS+=("$arg")
    else
      echo "skip: $arg (not found)" >&2
    fi
  done
fi

render_one() {
  local html="$1" outdir="$2" previewdir="$3" name
  name="$(basename "$html" .html)"
  echo "  $name @ ${OUT_W}x${OUT_H}"
  "$CHROME" \
    --headless=new \
    --hide-scrollbars \
    --disable-gpu \
    --force-device-scale-factor=${DPR} \
    --virtual-time-budget=4000 \
    --window-size=${RENDER_W},${RENDER_H} \
    --screenshot="$TMP/$name.png" \
    "file://$html" \
    >/dev/null 2>&1

  python3 -c "
from PIL import Image
img = Image.open('$TMP/$name.png').crop((0, 0, ${OUT_W}, ${OUT_H}))
img.save('$outdir/$name.png', optimize=True)
img.resize((${PREVIEW_W}, ${PREVIEW_H}), Image.LANCZOS).save('$previewdir/$name.png', optimize=True)
"
}

for target in "${TARGETS[@]}"; do
  if [ -d "$target" ]; then
    folder="$(cd "$target" && pwd)"
    out="$folder/out"
    preview="$folder/previews"
    mkdir -p "$out" "$preview"
    echo "rendering $(basename "$folder")/"
    # Normalize illustration whitespace before render (idempotent).
    if [ -d "$folder/illustrations" ]; then
      python3 "$DIR/crop.py" "$folder" >/dev/null 2>&1 || true
    fi
    for html in "$folder"/*.html; do
      [ -f "$html" ] || continue
      render_one "$html" "$out" "$preview"
    done
  elif [ -f "$target" ]; then
    parent="$(cd "$(dirname "$target")" && pwd)"
    out="$parent/out"
    preview="$parent/previews"
    mkdir -p "$out" "$preview"
    render_one "$target" "$out" "$preview"
  fi
done

rm -rf "$TMP"
echo "done."
