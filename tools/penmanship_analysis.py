"""Derive penmanship metrics from glyph crops and page signals."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev


def _slant_angle(bbox: dict) -> float:
    w, h = bbox.get("w", 0.01), bbox.get("h", 0.01)
    return math.degrees(math.atan2(h, w))


def analyze_glyph_index(glyph_data: dict) -> dict:
    glyphs = glyph_data.get("glyphs", [])
    if not glyphs:
        return {
            "glyph_count": 0,
            "flow_score": 0.0,
            "dexterity_score": 0.0,
            "speed_estimate": "unknown",
            "consistency": 0.0,
            "slant_mean_deg": 0.0,
            "spacing_variance": 0.0,
        }

    heights = [g["bbox"]["h"] for g in glyphs if g.get("bbox")]
    widths = [g["bbox"]["w"] for g in glyphs if g.get("bbox")]
    slants = [_slant_angle(g["bbox"]) for g in glyphs if g.get("bbox")]

    spacings: list[float] = []
    sorted_g = sorted(glyphs, key=lambda g: g.get("reading_order", 0))
    for a, b in zip(sorted_g, sorted_g[1:]):
        if a.get("line_num") == b.get("line_num"):
            ax = a["bbox"]["x"] + a["bbox"]["w"]
            bx = b["bbox"]["x"]
            spacings.append(max(0.0, bx - ax))

    h_mean = mean(heights) if heights else 0.01
    h_std = pstdev(heights) if len(heights) > 1 else 0.0
    w_std = pstdev(widths) if len(widths) > 1 else 0.0
    sp_var = pstdev(spacings) if len(spacings) > 1 else 0.0

    consistency = max(0.0, 1.0 - min(1.0, (h_std / h_mean) * 2 + w_std * 5))
    flow = max(0.0, 1.0 - min(1.0, sp_var * 12))
    dexterity = max(0.0, min(1.0, consistency * 0.6 + flow * 0.4))

    glyphs_per_line = {}
    for g in glyphs:
        ln = g.get("line_num", 0)
        glyphs_per_line[ln] = glyphs_per_line.get(ln, 0) + 1
    avg_gpl = mean(glyphs_per_line.values()) if glyphs_per_line else 0
    if avg_gpl > 35:
        speed = "fast"
    elif avg_gpl > 20:
        speed = "moderate"
    else:
        speed = "deliberate"

    return {
        "glyph_count": len(glyphs),
        "flow_score": round(flow, 3),
        "dexterity_score": round(dexterity, 3),
        "speed_estimate": speed,
        "consistency": round(consistency, 3),
        "slant_mean_deg": round(mean(slants), 2) if slants else 0.0,
        "spacing_variance": round(sp_var, 4),
        "unique_chars": len({g["char"] for g in glyphs}),
    }


def build_penmanship_report(
    page: int,
    repo_root: Path,
    grok_penmanship: dict | None = None,
) -> dict:
    page_dir = repo_root / "processed" / f"page_{page:03d}"
    glyph_path = page_dir / "glyph_index.json"
    glyph_data = json.loads(glyph_path.read_text(encoding="utf-8")) if glyph_path.is_file() else {"glyphs": []}
    metrics = analyze_glyph_index(glyph_data)

    grok_block = {}
    if grok_penmanship:
        grok_block = {
            "ai_flow": grok_penmanship.get("flow_assessment"),
            "ai_dexterity": grok_penmanship.get("dexterity_assessment"),
            "ai_speed": grok_penmanship.get("speed_assessment"),
            "ai_penmanship_summary": grok_penmanship.get("summary"),
            "animation_sequence": grok_penmanship.get("animation_sequence", []),
        }

    report = {
        "page": page,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "grok_penmanship": grok_block,
        "hand": "CR-main-hand",
        "assessment": _verbal_assessment(metrics, grok_block),
    }
    (page_dir / "penmanship_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def _verbal_assessment(metrics: dict, grok: dict) -> str:
    parts = [
        f"Flow {metrics['flow_score']:.0%}, dexterity {metrics['dexterity_score']:.0%}, "
        f"speed {metrics['speed_estimate']}.",
    ]
    if grok.get("ai_penmanship_summary"):
        parts.append(grok["ai_penmanship_summary"])
    return " ".join(parts)


def build_corpus_summary(repo_root: Path, pages: list[int]) -> dict:
    reports = []
    for page in pages:
        path = repo_root / "processed" / f"page_{page:03d}" / "penmanship_report.json"
        if path.is_file():
            reports.append(json.loads(path.read_text(encoding="utf-8")))

    if not reports:
        return {"pages_analyzed": 0, "corpus": {}}

    flows = [r["metrics"]["flow_score"] for r in reports]
    dex = [r["metrics"]["dexterity_score"] for r in reports]
    corpus = {
        "pages_analyzed": len(reports),
        "mean_flow": round(mean(flows), 3),
        "mean_dexterity": round(mean(dex), 3),
        "hand_profile": (
            "Steady Icelandic Gothic book hand with moderate line density; "
            "single main scribe across the codex."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    out = repo_root / "data" / "penmanship_corpus.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return corpus