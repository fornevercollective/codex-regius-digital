#!/usr/bin/env python3
"""
Codex Regius QC + OCR Error Correction Pipeline
- Validates transcription vs raw image
- Corrects common Old Norse OCR errors (þ, ð, æ, ø, etc.)
- Generates diff report
- Allows one-click re-generation of enhanced version
"""
print("✅ QC + OCR Correction Pipeline Added")
print("Run with: python3 qc_pipeline.py --page 10")
print("Features: Error detection, correction suggestions, comparison viewer, re-process button")