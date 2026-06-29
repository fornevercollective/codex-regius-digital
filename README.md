# Codex Regius Digital Edition

Digital scholarly and artistic edition of **GKS 2365 4to** (Poetic Edda) — 144 folios, multi-layer processing, Grok vision enhancement, and an interactive paleography hub.

**Live:** [Paleography Hub](https://fornevercollective.github.io/codex-regius-digital/paleography-hub.html) · [Book Viewer](https://fornevercollective.github.io/codex-regius-digital/book-viewer.html) · [Page 10 Variations](https://fornevercollective.github.io/codex-regius-digital/page-10-variations.html)

---

## Grok image processing — Page 10 (Hávamál)

Each folio passes through a base pipeline (scholarly prep) then **Grok `image_edit`** enhancement (`grok-enhance-script.py`) producing readable transcription surfaces and artistic vellum reconstructions.

### Layer comparison

| Pipeline base | Grok enhanced |
|---------------|---------------|
| **Clean white** — OCR/glyph prep | **Grok clean** — transcription-ready surface |
| ![Clean white](docs/readme/page010-clean-white.jpg) | ![Grok clean white](docs/readme/page010-grok-clean.jpg) |
| **Artistic vellum** — warm parchment grade | **Grok vellum** — illuminated-manuscript aesthetic |
| ![Artistic vellum](docs/readme/page010-artistic-vellum.jpg) | ![Grok artistic vellum](docs/readme/page010-grok-vellum.jpg) |

### Manuscript variation passes

Grok multi-pass experiments explore **potential codex presentation styles** — alternate binding wear, ink weight, and vellum tone while preserving text block geometry. These are research variations, not facsimile replacements.

| Variation A | Variation B | Variation C |
|-------------|-------------|-------------|
| ![Var eWxhp](docs/readme/page010-variation-eWxhp.jpg) | ![Var nfHsD](docs/readme/page010-variation-nfHsD.jpg) | ![Var DLu85](docs/readme/page010-variation-DLu85.jpg) |

Full gallery (12 passes): [page-10-variations.html](page-10-variations.html) · source `processed/page_010/grok_variations/`

### Hub layer mixer

The [Paleography Hub](paleography-hub.html) stacks raw, base, and Grok layers with presets (Grok clean, scholastic mix, raw↔Grok slider) and per-page downloads.

---

## What we built

| Feature | Description |
|---------|-------------|
| **144-page hub** | Page pills (complete/partial/blank), layer mixer, scribe timeline, liturgy + chant modes |
| **Grok vision** | Marginalia/doodle survey (`grok-doodles-script.py`), penmanship analysis, QC metrics |
| **Runic parallels** | Bergen rune sticks, Rök stone, Ramsund — linked to folios ([`data/runic_parallels.json`](data/runic_parallels.json)) |
| **Book exports** | Chunked ≤95 MB zips for GitHub (vellum, white, Grok layers) |
| **Scholarly stack** | Codicology, calligraphy glyphs, liturgy collation, AI assessment per page |

Checklist: [`TODO-complete-research.md`](TODO-complete-research.md)

---

## Pipeline

| Script | Purpose |
|--------|---------|
| `GKS2365/mass-process-script.py` | Base layers (vellum, clean white, HTML, metadata) |
| `GKS2365/grok-enhance-script.py` | Grok `image_edit` — `grok_clean_white.jpg`, `grok_artistic_vellum.jpg` |
| `GKS2365/grok-doodles-script.py` | Grok vision marginalia survey → `grok_doodles.json` |
| `GKS2365/grok-penmanship-script.py` | Stroke/penmanship vision pass |
| `qc-pipeline.py` | ML preprocessing, OCR, error correction, QC reports |
| `assessment-pipeline.py` | Codicology, calligraphy, doodles, liturgy, scholarly reports |
| `glyph-pipeline.py` | Per-letter crops + `page_highlights.json` |
| `tools/build_hub_exports.py` | GitHub-safe chunked book zips |
| `tools/build_runic_parallels.py` | Runic/stone parallel page index |

---

## Setup

```bash
git clone https://github.com/fornevercollective/codex-regius-digital.git
cd codex-regius-digital
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install tesseract tesseract-lang   # OCR: isl+nor+eng
git lfs install && git lfs pull
```

## Processing commands

```bash
# Base layers (all 144 pages)
cd GKS2365
../.venv/bin/python3 mass-process-script.py --all --skip-existing

# Grok image enhancement
../.venv/bin/python3 grok-enhance-script.py --pages 10-144 --skip-existing --qc

# Grok doodle / marginalia vision survey
python3 grok-doodles-script.py --all --skip-existing

# Scholarly assessment + hub data
cd ..
.venv/bin/python3 assessment-pipeline.py --all
python3 tools/build_hub_index.py
python3 tools/build_runic_parallels.py
python3 tools/build_hub_exports.py
```

## QC + OCR

```bash
.venv/bin/python3 qc-pipeline.py --page 10
.venv/bin/python3 qc-pipeline.py --batch 1-20 --auto-apply
```

Outputs: `processed/page_NNN/qc_report.json`, `ai_assessment.md`, `scholarly_report.json`

## GitHub Pages deploy

```bash
bash scripts/build-pages.sh   # → deploy/ (excludes raw PNG, export zips; ~565 MB)
```

Workflow: `.github/workflows/pages.yml` on push to `main`.

---

## Per-page outputs

```
processed/page_NNN/
  artistic_vellum.jpg      # warm parchment grade
  clean_white.jpg          # scholarly OCR prep
  grok_artistic_vellum.jpg # Grok vellum aesthetic
  grok_clean_white.jpg     # Grok transcription surface
  grok_variations/         # multi-pass style experiments (page 10+)
  grok_doodles.json        # vision marginalia inventory
  glyph_index.json         # letter crops
  ai_assessment.md         # transcription + translation scaffold
  scholarly_report.json    # codicology + scribe context
```

---

## Links

- [handrit.is — GKS 2365 4to](https://handrit.is/manuscript/view/is/GKS04-2365/9)
- [Árni Magnússon Institute](https://www.arnastofnun.is/)
- [Neckel & Kuhn *Edda*](https://archive.org/details/edda00neck)

## Citation

When using this edition, cite the Árni Magnússon Institute facsimile ([handrit.is](https://handrit.is)) as the primary source manuscript and note that Grok-enhanced layers are **research visualizations**, not institutional facsimile replacements.