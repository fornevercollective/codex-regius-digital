# QC Report — Page 44

**Status**: ok
**Manuscript**: GKS 2365 4to
**Handrit**: [https://handrit.is/manuscript/view/is/GKS04-2365/9](https://handrit.is/manuscript/view/is/GKS04-2365/9)
**Generated**: 2026-06-29T03:00:14.587603+00:00

## Pipeline Steps
- **preprocess** (ok): [{'step': '01_raw_gray', 'note': 'Grayscale load', 'shape': [2372, 1582]}, {'step': '02_denoised', 'note': 'Non-local means denoise', 'shape': [2372, 1582]}, {'step': '03_contrast', 'note': 'CLAHE contrast', 'shape': [2372, 1582]}, {'step': '04_binarized', 'note': 'Otsu binarization', 'shape': [2372, 1582]}, {'step': '05_deskewed', 'note': 'Deskew correction (0.00°)', 'shape': [2372, 1582]}]
- **ocr** (ok): Tesseract extraction complete
- **ocr_to_assessment** (ok): ['Inserted OCR text']

## Image Metrics (ML)
- **artistic_vellum**: SSIM=0.9923, contrast Δ=1.6
- **clean_white**: SSIM=0.7734, contrast Δ=35.8
- **grok_artistic_vellum**: SSIM=0.4371, contrast Δ=-2.3
- **grok_clean_white**: SSIM=0.2873, contrast Δ=9.6

## Issues
- [WARNING] **UNUSUAL_CHARS**: Line 1: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 4: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 5: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 6: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 7: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 8: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 10: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 12: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 14: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 15: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 18: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 21: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 22: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 23: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 25: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 26: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 27: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 28: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 30: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 33: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 34: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`

## References
- handrit.is: Digital manuscript viewer for GKS 2365 4to. <https://handrit.is/manuscript/view/is/GKS04-2365/9>
- Neckel & Kuhn 1983: Gustav Neckel and Hans Kuhn, *Edda: Die Lieder des Codex Regius*, 2 vols., Heidelberg: Carl Winter, 1983. <https://archive.org/details/edda00neck>
- Tesseract OCR: Smith, R. (2007). An Overview of the Tesseract OCR Engine. *ICDAR*. <https://github.com/tesseract-ocr/tesseract>
- SSIM: Wang, Zhou, et al. (2004). Image quality assessment: from error visibility to structural similarity. *IEEE TIP*. <https://doi.org/10.1109/TIP.2003.819861>
