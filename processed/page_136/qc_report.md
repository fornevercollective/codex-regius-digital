# QC Report — Page 136

**Status**: needs_review
**Manuscript**: GKS 2365 4to
**Handrit**: [https://handrit.is/manuscript/view/is/GKS04-2365/9](https://handrit.is/manuscript/view/is/GKS04-2365/9)
**Generated**: 2026-06-29T04:28:35.074127+00:00

## Pipeline Steps
- **preprocess** (ok): [{'step': '01_raw_gray', 'note': 'Grayscale load', 'shape': [2696, 1798]}, {'step': '02_denoised', 'note': 'Non-local means denoise', 'shape': [2696, 1798]}, {'step': '03_contrast', 'note': 'CLAHE contrast', 'shape': [2696, 1798]}, {'step': '04_binarized', 'note': 'Otsu binarization', 'shape': [2696, 1798]}, {'step': '05_deskewed', 'note': 'Deskew correction (0.00°)', 'shape': [2696, 1798]}]
- **ocr** (ok): Tesseract extraction complete

## Image Metrics (ML)
- **artistic_vellum**: SSIM=0.991, contrast Δ=-2.1
- **clean_white**: SSIM=0.8124, contrast Δ=22.0
- **grok_artistic_vellum**: SSIM=0.5853, contrast Δ=-13.0
- **grok_clean_white**: SSIM=0.6465, contrast Δ=4.7

## Issues
- [ERROR] **DIGIT_NOISE**: Line 1: high digit ratio — likely OCR noise.
  - Suggestion: `Re-run preprocessing with deskew; verify iron-gall letterforms.`
- [ERROR] **DIGIT_NOISE**: Line 3: high digit ratio — likely OCR noise.
  - Suggestion: `Re-run preprocessing with deskew; verify iron-gall letterforms.`
- [WARNING] **UNUSUAL_CHARS**: Line 4: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`

## References
- handrit.is: Digital manuscript viewer for GKS 2365 4to. <https://handrit.is/manuscript/view/is/GKS04-2365/9>
- Neckel & Kuhn 1983: Gustav Neckel and Hans Kuhn, *Edda: Die Lieder des Codex Regius*, 2 vols., Heidelberg: Carl Winter, 1983. <https://archive.org/details/edda00neck>
- Tesseract OCR: Smith, R. (2007). An Overview of the Tesseract OCR Engine. *ICDAR*. <https://github.com/tesseract-ocr/tesseract>
- SSIM: Wang, Zhou, et al. (2004). Image quality assessment: from error visibility to structural similarity. *IEEE TIP*. <https://doi.org/10.1109/TIP.2003.819861>
