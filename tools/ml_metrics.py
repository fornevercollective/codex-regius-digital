"""ML-style image quality metrics for enhanced layer validation."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


def load_resized_pair(path_a: Path, path_b: Path, max_dim: int = 1200) -> tuple[np.ndarray, np.ndarray]:
    def load(path: Path) -> np.ndarray:
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(path)
        h, w = img.shape
        scale = min(1.0, max_dim / max(h, w))
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        return img

    a, b = load(path_a), load(path_b)
    h = min(a.shape[0], b.shape[0])
    w = min(a.shape[1], b.shape[1])
    return a[:h, :w], b[:h, :w]


def blur_score(gray: np.ndarray) -> float:
    """Laplacian variance — higher = sharper."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def contrast_score(gray: np.ndarray) -> float:
    return float(gray.std())


def compare_layers(raw_path: Path, enhanced_path: Path) -> dict:
    """SSIM and sharpness delta between raw and enhanced."""
    raw, enhanced = load_resized_pair(raw_path, enhanced_path)
    score = ssim(raw, enhanced, data_range=255)
    return {
        "ssim": round(float(score), 4),
        "raw_blur": round(blur_score(raw), 2),
        "enhanced_blur": round(blur_score(enhanced), 2),
        "raw_contrast": round(contrast_score(raw), 2),
        "enhanced_contrast": round(contrast_score(enhanced), 2),
        "ssim_ok": bool(score >= 0.35),
        "contrast_improved": bool(contrast_score(enhanced) >= contrast_score(raw) * 0.9),
    }