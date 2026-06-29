# QC Report — Page 9

**Status**: ok
**Manuscript**: GKS 2365 4to
**Handrit**: [https://handrit.is/manuscript/view/is/GKS04-2365/9](https://handrit.is/manuscript/view/is/GKS04-2365/9)
**Generated**: 2026-06-29T02:58:14.678015+00:00

## Pipeline Steps
- **preprocess** (ok): [{'step': '01_raw_gray', 'note': 'Grayscale load', 'shape': [2500, 1667]}, {'step': '02_denoised', 'note': 'Non-local means denoise', 'shape': [2500, 1667]}, {'step': '03_contrast', 'note': 'CLAHE contrast', 'shape': [2500, 1667]}, {'step': '04_binarized', 'note': 'Otsu binarization', 'shape': [2500, 1667]}, {'step': '05_deskewed', 'note': 'Deskew correction (0.00°)', 'shape': [2500, 1667]}]
- **ocr** (ok): Tesseract extraction complete
- **ocr_to_assessment** (ok): ['Inserted OCR text']

## Image Metrics (ML)
- **artistic_vellum**: SSIM=0.9885, contrast Δ=1.0
- **clean_white**: SSIM=0.8439, contrast Δ=19.5

## Issues
- [WARNING] **UNUSUAL_CHARS**: Line 2: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 4: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 8: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`

## References
- handrit.is: Digital manuscript viewer for GKS 2365 4to. <https://handrit.is/manuscript/view/is/GKS04-2365/9>
- Neckel & Kuhn 1983: Gustav Neckel and Hans Kuhn, *Edda: Die Lieder des Codex Regius*, 2 vols., Heidelberg: Carl Winter, 1983. <https://archive.org/details/edda00neck>
- Tesseract OCR: Smith, R. (2007). An Overview of the Tesseract OCR Engine. *ICDAR*. <https://github.com/tesseract-ocr/tesseract>
- SSIM: Wang, Zhou, et al. (2004). Image quality assessment: from error visibility to structural similarity. *IEEE TIP*. <https://doi.org/10.1109/TIP.2003.819861>
