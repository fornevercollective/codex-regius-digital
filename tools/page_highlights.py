"""Aggregate per-page highlights for hub overlay and event index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REGION_BOXES = {
    "upper margin": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.12},
    "lower margin": {"x": 0.0, "y": 0.88, "w": 1.0, "h": 0.12},
    "left margin": {"x": 0.0, "y": 0.0, "w": 0.1, "h": 1.0},
    "right margin": {"x": 0.9, "y": 0.0, "w": 0.1, "h": 1.0},
    "interlinear": {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.6},
    "text block": {"x": 0.08, "y": 0.1, "w": 0.84, "h": 0.8},
}


def region_to_bbox(region: str) -> dict:
    key = region.lower().strip()
    for k, box in REGION_BOXES.items():
        if k in key:
            return {**box, "region": k}
    return {**REGION_BOXES["text block"], "region": region}


def load_json(path: Path) -> dict | list | None:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def build_page_highlights(page: int, repo_root: Path) -> dict:
    page_dir = repo_root / "processed" / f"page_{page:03d}"
    events: list[dict] = []

    doodles = load_json(page_dir / "grok_doodles.json")
    if isinstance(doodles, dict):
        for item in doodles.get("items", []):
            bbox = region_to_bbox(item.get("region", "text block"))
            events.append({
                "id": item.get("id", f"M-{page:03d}"),
                "type": item.get("type", "marginalia"),
                "category": "doodle",
                "label": item.get("description", "")[:80],
                "bbox": bbox,
                "source": "grok_doodles",
            })

    glyphs = load_json(page_dir / "glyph_index.json")
    if isinstance(glyphs, dict) and glyphs.get("glyph_count", 0) > 0:
        events.append({
            "id": f"G-{page:03d}-ALL",
            "type": "glyph_field",
            "category": "calligraphy",
            "label": f"{glyphs['glyph_count']} glyph crops",
            "bbox": {"x": 0.08, "y": 0.1, "w": 0.84, "h": 0.8, "region": "text block"},
            "source": "glyph_index",
            "glyph_count": glyphs["glyph_count"],
        })
        for g in glyphs.get("glyphs", [])[:50]:
            if g.get("confidence", 0) < 30 and g["char"] != "?":
                events.append({
                    "id": g["id"],
                    "type": "low_confidence_glyph",
                    "category": "ocr",
                    "label": f"{g['char']} (conf {g.get('confidence', 0)})",
                    "bbox": g.get("bbox", {}),
                    "source": "glyph_index",
                })

    qc = load_json(page_dir / "qc_report.json")
    if isinstance(qc, dict):
        for issue in qc.get("issues", [])[:10]:
            events.append({
                "id": f"QC-{page:03d}-{issue.get('line', 0)}",
                "type": issue.get("type", "qc_issue"),
                "category": "qc",
                "label": issue.get("suggestion", issue.get("message", ""))[:80],
                "bbox": {"x": 0.1, "y": min(0.85, 0.05 + issue.get("line", 1) * 0.02), "w": 0.8, "h": 0.03},
                "source": "qc_report",
            })

    pen = load_json(page_dir / "penmanship_report.json")
    if isinstance(pen, dict) and pen.get("metrics", {}).get("glyph_count", 0) > 0:
        m = pen["metrics"]
        if m.get("flow_score", 1) < 0.5 or m.get("dexterity_score", 1) < 0.5:
            events.append({
                "id": f"P-{page:03d}-FLOW",
                "type": "penmanship_flag",
                "category": "penmanship",
                "label": f"Flow {m['flow_score']:.0%} · dexterity {m['dexterity_score']:.0%}",
                "bbox": {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9, "region": "text block"},
                "source": "penmanship_report",
            })

    meta = load_json(repo_root / "metadata" / f"page_{page:03d}.json")
    poem = ""
    if isinstance(meta, dict):
        poem = meta.get("poem_full") or meta.get("poem", "")

    return {
        "page": page,
        "poem": poem,
        "event_count": len(events),
        "has_events": len(events) > 0,
        "events": events,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_highlights_index(repo_root: Path, pages: list[int]) -> dict:
    page_entries: list[dict] = []
    by_category: dict[str, list[int]] = {}
    by_type: dict[str, list[int]] = {}

    for page in pages:
        entry = build_page_highlights(page, repo_root)
        (repo_root / "processed" / f"page_{page:03d}" / "page_highlights.json").write_text(
            json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if entry["has_events"]:
            page_entries.append({
                "page": page,
                "poem": entry.get("poem", ""),
                "event_count": entry["event_count"],
                "categories": list({e["category"] for e in entry["events"]}),
                "types": list({e["type"] for e in entry["events"]}),
            })
            for e in entry["events"]:
                by_category.setdefault(e["category"], [])
                if page not in by_category[e["category"]]:
                    by_category[e["category"]].append(page)
                by_type.setdefault(e["type"], [])
                if page not in by_type[e["type"]]:
                    by_type[e["type"]].append(page)

    for k in by_category:
        by_category[k].sort()
    for k in by_type:
        by_type[k].sort()

    index = {
        "corpus": "GKS 2365 4to",
        "pages_with_events": len(page_entries),
        "pages_total": len(pages),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": sorted(page_entries, key=lambda p: p["page"]),
        "by_category": by_category,
        "by_type": by_type,
    }
    out = repo_root / "data" / "page_highlights.json"
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return index