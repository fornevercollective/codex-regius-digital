# Codex Regius Digital Edition

Digital scholarly and artistic edition of **GKS 2365 4to** (Poetic Edda).

## Pipeline

| Script | Purpose |
|--------|---------|
| `GKS2365/mass-process-script.py` | Base layers (vellum, clean white, HTML, metadata) |
| `GKS2365/grok-enhance-script.py` | Grok `image_edit` layers for pages 10+ |
| `qc-pipeline.py` | ML preprocessing, OCR, error correction, QC reports |
| `assessment-pipeline.py` | Codicology, calligraphy, doodles, liturgy, AI scholarly reports |
| `paleography-hub.html` | Forbes-style interactive hub (timeline, alphabet, font export) |

## Setup

```bash
cd /Volumes/qbitOS/00.dev/projects/codex-regius-digital
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install tesseract tesseract-lang   # OCR language packs
git lfs install
```

## Mass processing

```bash
cd GKS2365
../.venv/bin/python3 mass-process-script.py --skip-existing
../.venv/bin/python3 grok-enhance-script.py --pages 10-144 --skip-existing --qc
```

## Scholarly assessment (codicology, calligraphy, liturgy)

```bash
.venv/bin/python3 assessment-pipeline.py --page 10
.venv/bin/python3 assessment-pipeline.py --all --export-font
```

Per-page outputs: `codicology.md`, `calligraphy_sheet.md`, `doodles_catalog.md`, `liturgy_comparison.md`, `scholarly_report.json`.

Open **`paleography-hub.html`** for the interactive Forbes-style timeline, alphabet reference, and script-to-font export.

## QC + OCR correction

```bash
# Single page
.venv/bin/python3 qc-pipeline.py --page 10

# Batch with suggestions
.venv/bin/python3 qc-pipeline.py --batch 1-20 --auto-suggest --export-report

# Full collection
.venv/bin/python3 qc-pipeline.py --all --export-report

# Auto-apply safe Old Norse word fixes
.venv/bin/python3 qc-pipeline.py --batch 1-20 --auto-apply
```

QC outputs per page: `processed/page_NNN/qc_report.json` and `qc_report.md`.

## Pages deploy

GitHub Pages uses `scripts/build-pages.sh` (excludes `raw.png` to stay under 1 GB).

## Links

- [handrit.is viewer](https://handrit.is/manuscript/view/is/GKS04-2365/9)
- [Live site](https://fornevercollective.github.io/codex-regius-digital/)