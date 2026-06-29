"""Automated image preprocessing for manuscript OCR and QC."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_gray(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return img


def denoise(gray: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)


def auto_contrast(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def binarize(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def estimate_skew_angle(binary: np.ndarray) -> float:
    coords = np.column_stack(np.where(binary < 128))
    if len(coords) < 100:
        return 0.0
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    if angle < -45:
        angle = 90 + angle
    return float(angle)


def deskew(gray: np.ndarray, angle: float) -> np.ndarray:
    if abs(angle) < 0.3:
        return gray
    h, w = gray.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def preprocess_pipeline(path: Path, save_dir: Path | None = None) -> dict:
    """
    Full preprocessing chain for OCR input.
    Returns dict with arrays and diagnostic metadata.
    """
    gray = load_gray(path)
    steps: list[dict] = []

    def record(name: str, arr: np.ndarray, note: str) -> np.ndarray:
        steps.append({"step": name, "note": note, "shape": list(arr.shape)})
        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(save_dir / f"{name}.png"), arr)
        return arr

    gray = record("01_raw_gray", gray, "Grayscale load")
    den = record("02_denoised", denoise(gray), "Non-local means denoise")
    contrast = record("03_contrast", auto_contrast(den), "CLAHE contrast")
    binary = record("04_binarized", binarize(contrast), "Otsu binarization")
    angle = estimate_skew_angle(binary)
    deskewed = record(
        "05_deskewed",
        deskew(contrast, angle),
        f"Deskew correction ({angle:.2f}°)",
    )

    return {
        "ocr_input": deskewed,
        "binary": binary,
        "skew_angle": angle,
        "steps": steps,
    }