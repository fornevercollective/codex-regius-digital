#!/usr/bin/env python3
"""Build data/hub_page_index.json for paleography hub page status + exports."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\[PASTE", re.I)


def page_status(meta: dict, assessment: str) -> str:
    layers = set(meta.get("layers", []))
    has_grok = "grok_clean_white.jpg" in layers or meta.get("grok_enhanced")
    has_ocr = bool(meta.get("original_text", "").strip()) or (
        assessment and not PLACEHOLDER.search(assessment) and "```" in assessment
        and len(assessment) > 400
    )
    is_placeholder = not has_ocr and (PLACEHOLDER.search(assessment) if assessment else True)
    if is_placeholder and not has_grok:
        return "blank"
    if has_grok and meta.get("scholarly_assessment"):
        return "complete"
    if has_grok or meta.get("scholarly_assessment") or "clean_white.jpg" in layers:
        return "partial"
    return "blank"


def layer_available(layers: list[str], filename: str) -> bool:
    return filename in layers


def main() -> int:
    pages = []
    counts = {"blank": 0, "partial": 0, "complete": 0}
    for n in range(1, 145):
        meta_path = REPO / "metadata" / f"page_{n:03d}.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {"page": n}
        assess_path = REPO / "processed" / f"page_{n:03d}" / "ai_assessment.md"
        assessment = assess_path.read_text(encoding="utf-8") if assess_path.is_file() else ""
        status = page_status(meta, assessment)
        counts[status] += 1
        ly = meta.get("layers", [])
        pages.append({
            "page": n,
            "status": status,
            "poem": meta.get("poem", ""),
            "qc_status": meta.get("qc_status", ""),
            "grok_enhanced": bool(meta.get("grok_enhanced")),
            "scholarly_assessment": bool(meta.get("scholarly_assessment")),
            "has_grok_doodles": "grok_doodles.json" in ly,
            "has_glyph_index": "glyph_index.json" in ly or (REPO / "processed" / f"page_{n:03d}" / "glyph_index.json").is_file(),
            "layers": {
                "raw": layer_available(ly, "raw.png"),
                "artistic_vellum": layer_available(ly, "artistic_vellum.jpg"),
                "clean_white": layer_available(ly, "clean_white.jpg"),
                "grok_artistic_vellum": layer_available(ly, "grok_artistic_vellum.jpg"),
                "grok_clean_white": layer_available(ly, "grok_clean_white.jpg"),
                "ai_assessment": layer_available(ly, "ai_assessment.md"),
            },
        })

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages_total": 144,
        "counts": counts,
        "highlights_ready": False,
        "pages": pages,
    }
    hl = REPO / "data" / "page_highlights.json"
    if hl.is_file():
        h = json.loads(hl.read_text(encoding="utf-8"))
        doodle_pages = len(h.get("by_category", {}).get("doodle", []))
        out["highlights_ready"] = doodle_pages >= 50

    path = REPO / "data" / "hub_page_index.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ hub_page_index.json — complete:{counts['complete']} partial:{counts['partial']} blank:{counts['blank']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())