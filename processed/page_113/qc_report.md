# QC Report — Page 113

**Status**: needs_review
**Manuscript**: GKS 2365 4to
**Handrit**: [https://handrit.is/manuscript/view/is/GKS04-2365/9](https://handrit.is/manuscript/view/is/GKS04-2365/9)
**Generated**: 2026-06-29T03:59:41.259439+00:00

## Pipeline Steps
- **preprocess** (ok): [{'step': '01_raw_gray', 'note': 'Grayscale load', 'shape': [2104, 1184]}, {'step': '02_denoised', 'note': 'Non-local means denoise', 'shape': [2104, 1184]}, {'step': '03_contrast', 'note': 'CLAHE contrast', 'shape': [2104, 1184]}, {'step': '04_binarized', 'note': 'Otsu binarization', 'shape': [2104, 1184]}, {'step': '05_deskewed', 'note': 'Deskew correction (0.00°)', 'shape': [2104, 1184]}]
- **ocr** (warning): Tesseract extraction complete

## Image Metrics (ML)
- **artistic_vellum**: SSIM=0.7637, contrast Δ=2.0
- **clean_white**: SSIM=0.7295, contrast Δ=28.6
- **grok_artistic_vellum**: SSIM=0.2624, contrast Δ=4.4
- **grok_clean_white**: SSIM=0.2757, contrast Δ=-3.3

## Issues
- [ERROR] **PLACEHOLDER_TEXT**: Transcription block is still a template placeholder.
  - Suggestion: `Run OCR on preprocessed raw image and review against handrit.is.`
  - Citation: handrit.is

## References
- handrit.is: Digital manuscript viewer for GKS 2365 4to. <https://handrit.is/manuscript/view/is/GKS04-2365/9>
- Neckel & Kuhn 1983: Gustav Neckel and Hans Kuhn, *Edda: Die Lieder des Codex Regius*, 2 vols., Heidelberg: Carl Winter, 1983. <https://archive.org/details/edda00neck>
- Tesseract OCR: Smith, R. (2007). An Overview of the Tesseract OCR Engine. *ICDAR*. <https://github.com/tesseract-ocr/tesseract>
- SSIM: Wang, Zhou, et al. (2004). Image quality assessment: from error visibility to structural similarity. *IEEE TIP*. <https://doi.org/10.1109/TIP.2003.819861>
