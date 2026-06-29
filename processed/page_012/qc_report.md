# QC Report — Page 12

**Status**: ok
**Manuscript**: GKS 2365 4to
**Handrit**: [https://handrit.is/manuscript/view/is/GKS04-2365/9](https://handrit.is/manuscript/view/is/GKS04-2365/9)
**Generated**: 2026-06-29T01:44:40.239774+00:00

## Pipeline Steps
- **preprocess** (ok): [{'step': '01_raw_gray', 'note': 'Grayscale load', 'shape': [2409, 1606]}, {'step': '02_denoised', 'note': 'Non-local means denoise', 'shape': [2409, 1606]}, {'step': '03_contrast', 'note': 'CLAHE contrast', 'shape': [2409, 1606]}, {'step': '04_binarized', 'note': 'Otsu binarization', 'shape': [2409, 1606]}, {'step': '05_deskewed', 'note': 'Deskew correction (0.00°)', 'shape': [2409, 1606]}]
- **ocr** (ok): Tesseract extraction complete

## Image Metrics (ML)
- **artistic_vellum**: SSIM=0.9901, contrast Δ=1.4
- **clean_white**: SSIM=0.7107, contrast Δ=41.5
- **grok_artistic_vellum**: SSIM=0.3765, contrast Δ=8.1
- **grok_clean_white**: SSIM=0.3535, contrast Δ=14.3

## Issues
- [WARNING] **UNUSUAL_CHARS**: Line 1: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 7: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 8: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`

## References
- handrit.is: Digital manuscript viewer for GKS 2365 4to. <https://handrit.is/manuscript/view/is/GKS04-2365/9>
- Neckel & Kuhn 1983: Gustav Neckel and Hans Kuhn, *Edda: Die Lieder des Codex Regius*, 2 vols., Heidelberg: Carl Winter, 1983. <https://archive.org/details/edda00neck>
- Tesseract OCR: Smith, R. (2007). An Overview of the Tesseract OCR Engine. *ICDAR*. <https://github.com/tesseract-ocr/tesseract>
- SSIM: Wang, Zhou, et al. (2004). Image quality assessment: from error visibility to structural similarity. *IEEE TIP*. <https://doi.org/10.1109/TIP.2003.819861>
