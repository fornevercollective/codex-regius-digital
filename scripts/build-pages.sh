#!/usr/bin/env bash
# Build a GitHub Pages artifact under 1 GB by excluding full-res raw PNGs.
# Raw scans remain in the repo via Git LFS; Pages serves JPG layers + HTML.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY="${ROOT}/deploy"
MAX_BYTES=$((950 * 1024 * 1024))  # warn below GitHub's 1 GB hard limit

rm -rf "${DEPLOY}"
mkdir -p "${DEPLOY}/processed" "${DEPLOY}/metadata"

echo "Building Pages artifact from ${ROOT}"

# Root HTML + docs
for f in index.html book-viewer.html paleography-hub.html \
         page-10-variations.html page-10-lyric-readalong.html README.md; do
  [[ -f "${ROOT}/${f}" ]] && cp "${ROOT}/${f}" "${DEPLOY}/"
done

touch "${DEPLOY}/.nojekyll"

# Metadata (JSON only, small)
if [[ -d "${ROOT}/metadata" ]]; then
  cp -r "${ROOT}/metadata/." "${DEPLOY}/metadata/"
fi

# Processed pages: JPG/HTML/MD only — skip raw.png (≈1.1 GB total)
if [[ -d "${ROOT}/processed" ]]; then
  for page_dir in "${ROOT}"/processed/page_*; do
    [[ -d "${page_dir}" ]] || continue
    name="$(basename "${page_dir}")"
    out="${DEPLOY}/processed/${name}"
    mkdir -p "${out}"

    for item in "${page_dir}"/*; do
      base="$(basename "${item}")"
      case "${base}" in
        raw.png) continue ;;
        grok_variations)
          mkdir -p "${out}/grok_variations"
          cp -r "${item}/." "${out}/grok_variations/"
          ;;
        *)
          cp -r "${item}" "${out}/"
          ;;
      esac
    done
  done
fi

SIZE="$(du -sk "${DEPLOY}" | awk '{print $1 * 1024}')"
SIZE_MB=$((SIZE / 1024 / 1024))
echo "Deploy artifact size: ${SIZE_MB} MB"

if (( SIZE > MAX_BYTES )); then
  echo "ERROR: Artifact exceeds ${MAX_BYTES} bytes (${SIZE_MB} MB). Trim assets before deploy." >&2
  exit 1
fi

echo "Pages build OK → ${DEPLOY}"