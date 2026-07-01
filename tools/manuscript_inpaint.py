#!/usr/bin/env python3
"""
Parisotto/Calatroni-inspired inpainting for Codex Regius damage regions.

Seeds damage masks from grok_doodles.json region + type (stain, scratch, other),
then applies OpenCV telea/NS inpainting (TV-adjacent virtual restoration).

Output: processed/page_NNN/restored_inpaint.jpg + restoration_mask.png

Reference: Calatroni et al. Heritage Science 6:56 (2018)
https://doi.org/10.1186/s40494-018-0216-z
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent

REGION_BOXES: dict[str, tuple[float, float, float, float]] = {
    "upper margin": (0.0, 0.0, 1.0, 0.14),
    "lower margin": (0.0, 0.78, 1.0, 1.0),
    "left margin": (0.0, 0.0, 0.12, 1.0),
    "right margin": (0.88, 0.0, 1.0, 1.0),
    "text block": (0.12, 0.12, 0.88, 0.88),
    "margin": (0.0, 0.0, 0.15, 1.0),
}

INPAINT_TYPES = frozenset({"stain", "scratch", "other"})


def parse_pages(spec: str | None) -> list[int]:
    if not spec:
        return list(range(1, 145))
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


def pick_source(page_dir: Path) -> Path | None:
    for name in ("grok_clean_white.jpg", "clean_white.jpg", "artistic_vellum.jpg", "raw.png"):
        p = page_dir / name
        if p.is_file():
            return p
    return None


def region_rect(region: str, w: int, h: int) -> tuple[int, int, int, int]:
    key = region.lower().strip()
    for label, box in REGION_BOXES.items():
        if label in key:
            x0, y0, x1, y1 = box
            return int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)
    return int(0.1 * w), int(0.1 * h), int(0.9 * w), int(0.9 * h)


def stain_mask_in_roi(gray_roi: np.ndarray) -> np.ndarray:
    """Dark stain / hole detection inside a region ROI."""
    blur = cv2.GaussianBlur(gray_roi, (5, 5), 0)
    _, dark = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mean = float(gray_roi.mean())
    if mean < 120:
        _, dark2 = cv2.threshold(blur, int(mean * 0.55), 255, cv2.THRESH_BINARY_INV)
        dark = cv2.bitwise_or(dark, dark2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, kernel, iterations=2)
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, kernel, iterations=1)
    return dark


def build_mask(img: np.ndarray, doodles: dict) -> np.ndarray:
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    mask = np.zeros((h, w), dtype=np.uint8)

    for item in doodles.get("items", []):
        if item.get("type") not in INPAINT_TYPES:
            continue
        x0, y0, x1, y1 = region_rect(item.get("region", "text block"), w, h)
        roi = gray[y0:y1, x0:x1]
        if roi.size == 0:
            continue
        local = stain_mask_in_roi(roi)
        if item.get("type") == "scratch":
            edges = cv2.Canny(roi, 40, 120)
            local = cv2.bitwise_or(local, edges)
        mask[y0:y1, x0:x1] = cv2.bitwise_or(mask[y0:y1, x0:x1], local)

    if mask.sum() < 500:
        lower = gray[int(h * 0.65) :, :]
        local = stain_mask_in_roi(lower)
        mask[int(h * 0.65) :, :] = cv2.bitwise_or(mask[int(h * 0.65) :, :], local)

    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    return mask


def inpaint_page(page: int, method: str = "telea", dry_run: bool = False) -> bool:
    page_dir = REPO / "processed" / f"page_{page:03d}"
    doodle_path = page_dir / "grok_doodles.json"
    out_img = page_dir / "restored_inpaint.jpg"
    out_mask = page_dir / "restoration_mask.png"

    if out_img.is_file() and not dry_run:
        return True

    source = pick_source(page_dir)
    if not source:
        print(f"   ⏭️  page {page:3d}: no source image")
        return False

    doodles: dict = {}
    if doodle_path.is_file():
        doodles = json.loads(doodle_path.read_text(encoding="utf-8"))
    else:
        doodles = {"items": [{"region": "lower margin", "type": "stain", "description": "fallback"}]}

    img = cv2.imread(str(source))
    if img is None:
        return False

    mask = build_mask(img, doodles)
    if mask.sum() == 0:
        print(f"   ⏭️  page {page:3d}: empty mask")
        return False

    if dry_run:
        print(f"   [dry-run] page {page:3d}: mask pixels {int(mask.sum() / 255)}")
        return True

    flag = cv2.INPAINT_TELEA if method == "telea" else cv2.INPAINT_NS
    restored = cv2.inpaint(img, mask, inpaintRadius=5, flags=flag)
    cv2.imwrite(str(out_img), restored, [cv2.IMWRITE_JPEG_QUALITY, 92])
    cv2.imwrite(str(out_mask), mask)

    meta = {
        "page": page,
        "method": f"opencv_{method}",
        "reference": "10.1186/s40494-018-0216-z",
        "source": source.name,
        "mask_pixels": int(mask.sum() / 255),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (page_dir / "restoration_report.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(f"   ✅ page {page:3d}: restored_inpaint.jpg ({meta['mask_pixels']} px masked)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Manuscript damage inpainting (VisColl/Parisotto-inspired)")
    parser.add_argument("--pages", help="e.g. 98,110-114")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--method", choices=("telea", "ns"), default="telea")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--heavy-only", action="store_true", help="Only pages with grok_doodles damage items")
    args = parser.parse_args()

    if args.all:
        pages = list(range(1, 145))
    elif args.pages:
        pages = parse_pages(args.pages)
    else:
        pages = [98, 110, 111, 112, 113, 114]

    if args.heavy_only:
        filtered = []
        for p in pages:
            d = REPO / "processed" / f"page_{p:03d}" / "grok_doodles.json"
            if not d.is_file():
                continue
            data = json.loads(d.read_text(encoding="utf-8"))
            dmg = sum(1 for i in data.get("items", []) if i.get("type") in INPAINT_TYPES)
            if dmg >= 2 or len(data.get("damage_notes", [])) >= 3:
                filtered.append(p)
        pages = filtered

    ok = sum(inpaint_page(p, args.method, args.dry_run) for p in pages)
    print(f"\nDone: {ok}/{len(pages)} pages inpainted.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())