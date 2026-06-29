# QC Report — Page 139

**Status**: needs_review
**Manuscript**: GKS 2365 4to
**Handrit**: [https://handrit.is/manuscript/view/is/GKS04-2365/9](https://handrit.is/manuscript/view/is/GKS04-2365/9)
**Generated**: 2026-06-29T03:04:43.856486+00:00

## Pipeline Steps
- **preprocess** (ok): [{'step': '01_raw_gray', 'note': 'Grayscale load', 'shape': [2696, 1798]}, {'step': '02_denoised', 'note': 'Non-local means denoise', 'shape': [2696, 1798]}, {'step': '03_contrast', 'note': 'CLAHE contrast', 'shape': [2696, 1798]}, {'step': '04_binarized', 'note': 'Otsu binarization', 'shape': [2696, 1798]}, {'step': '05_deskewed', 'note': 'Deskew correction (0.00°)', 'shape': [2696, 1798]}]
- **ocr** (ok): Tesseract extraction complete
- **ocr_to_assessment** (ok): ["'bid' → 'bið'"]

## Image Metrics (ML)
- **artistic_vellum**: SSIM=0.9921, contrast Δ=-2.5
- **clean_white**: SSIM=0.8632, contrast Δ=19.1

## Issues
- [WARNING] **UNUSUAL_CHARS**: Line 2: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [ERROR] **DIGIT_NOISE**: Line 2: high digit ratio — likely OCR noise.
  - Suggestion: `Re-run preprocessing with deskew; verify iron-gall letterforms.`
- [ERROR] **DIGIT_NOISE**: Line 3: high digit ratio — likely OCR noise.
  - Suggestion: `Re-run preprocessing with deskew; verify iron-gall letterforms.`
- [WARNING] **UNUSUAL_CHARS**: Line 13: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 15: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 21: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **UNUSUAL_CHARS**: Line 35: unusual characters detected.
  - Suggestion: `Compare glyph-by-glyph with raw scan.`
- [WARNING] **WORD_NORMALIZATION**: 'bid' → 'bið'
  - Suggestion: `bið`
  - Etymology: Verb 'ask, bid' — formulaic request for hearing in Eddic openings.
  - Citation: Neckel & Kuhn 1983

## References
- handrit.is: Digital manuscript viewer for GKS 2365 4to. <https://handrit.is/manuscript/view/is/GKS04-2365/9>
- Neckel & Kuhn 1983: Gustav Neckel and Hans Kuhn, *Edda: Die Lieder des Codex Regius*, 2 vols., Heidelberg: Carl Winter, 1983. <https://archive.org/details/edda00neck>
- Tesseract OCR: Smith, R. (2007). An Overview of the Tesseract OCR Engine. *ICDAR*. <https://github.com/tesseract-ocr/tesseract>
- SSIM: Wang, Zhou, et al. (2004). Image quality assessment: from error visibility to structural similarity. *IEEE TIP*. <https://doi.org/10.1109/TIP.2003.819861>
