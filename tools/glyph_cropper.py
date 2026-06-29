"""Extract per-letter glyph crops from manuscript page images."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore

from tools.image_preprocess import binarize, load_gray


def pick_glyph_source(page_dir: Path) -> Path | None:
    for name in ("grok_clean_white.jpg", "clean_white.jpg", "raw.png"):
        path = page_dir / name
        if path.is_file():
            return path
    return None


def _normalize_char(ch: str) -> str:
    ch = ch.strip()
    if not ch or ch in {"|", "_", "~", "`", "'", '"', ".", ",", ";", ":"}:
        return ""
    if ch in ("ﬁ", "ﬂ"):
        return ch
    return ch.lower() if len(ch) == 1 and ch.isalpha() else ch


def extract_boxes_tesseract(gray: np.ndarray, psm: int = 6) -> list[dict]:
    if pytesseract is None:
        return []
    config = f"--psm {psm} -c preserve_interword_spaces=1"
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config=config)
    boxes: list[dict] = []
    n = len(data["text"])
    for i in range(n):
        text = _normalize_char(data["text"][i])
        if not text:
            continue
        conf = int(data["conf"][i]) if str(data["conf"][i]).isdigit() else -1
        w, h = int(data["width"][i]), int(data["height"][i])
        if w < 4 or h < 6 or w > gray.shape[1] * 0.15:
            continue
        boxes.append({
            "char": text,
            "left": int(data["left"][i]),
            "top": int(data["top"][i]),
            "width": w,
            "height": h,
            "confidence": conf,
            "line_num": int(data["line_num"][i]),
            "word_num": int(data["word_num"][i]),
        })
    return boxes


def extract_boxes_contours(binary: np.ndarray, min_area: int = 40, max_area: int = 8000) -> list[dict]:
    """Fallback: connected-component boxes when OCR yields few glyphs."""
    inv = 255 - binary
    contours, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[dict] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area < min_area or area > max_area:
            continue
        aspect = w / max(h, 1)
        if aspect > 4 or aspect < 0.15:
            continue
        boxes.append({
            "char": "?",
            "left": x,
            "top": y,
            "width": w,
            "height": h,
            "confidence": 0,
            "line_num": y // 40,
            "word_num": x // 80,
        })
    boxes.sort(key=lambda b: (b["line_num"], b["left"]))
    return boxes


def pad_box(box: dict, img_w: int, img_h: int, pad: int = 3) -> tuple[int, int, int, int]:
    x1 = max(0, box["left"] - pad)
    y1 = max(0, box["top"] - pad)
    x2 = min(img_w, box["left"] + box["width"] + pad)
    y2 = min(img_h, box["top"] + box["height"] + pad)
    return x1, y1, x2, y2


def extract_page_glyphs(page: int, repo_root: Path, force: bool = False) -> dict:
    page_dir = repo_root / "processed" / f"page_{page:03d}"
    out_dir = page_dir / "glyphs"
    index_path = page_dir / "glyph_index.json"

    if index_path.is_file() and not force:
        return json.loads(index_path.read_text(encoding="utf-8"))

    source = pick_glyph_source(page_dir)
    if not source:
        return {"page": page, "status": "no_image", "glyphs": []}

    gray = load_gray(source)
    binary = binarize(gray)
    boxes = extract_boxes_tesseract(gray)
    if len(boxes) < 8:
        boxes = extract_boxes_contours(binary)

    out_dir.mkdir(parents=True, exist_ok=True)
    img = cv2.imread(str(source))
    if img is None:
        img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    h_img, w_img = img.shape[:2]
    glyphs: list[dict] = []
    char_counts: dict[str, int] = {}

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = pad_box(box, w_img, h_img)
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        ch = box["char"]
        char_counts[ch] = char_counts.get(ch, 0) + 1
        fname = f"{page:03d}_{ch}_{char_counts[ch]:03d}.png"
        crop_path = out_dir / fname
        cv2.imwrite(str(crop_path), crop)

        glyphs.append({
            "id": f"G-{page:03d}-{i:04d}",
            "char": ch,
            "file": f"glyphs/{fname}",
            "bbox": {
                "x": x1 / w_img,
                "y": y1 / h_img,
                "w": (x2 - x1) / w_img,
                "h": (y2 - y1) / h_img,
            },
            "bbox_px": {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1},
            "confidence": box.get("confidence", 0),
            "reading_order": i,
            "line_num": box.get("line_num", 0),
        })

    result = {
        "page": page,
        "status": "ok",
        "source_image": source.name,
        "image_size": {"width": w_img, "height": h_img},
        "glyph_count": len(glyphs),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "glyphs": glyphs,
    }
    index_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result