#!/usr/bin/env python3
"""
Glyph crop + penmanship + highlights pipeline for Codex Regius.

Per page:
  - glyphs/*.png + glyph_index.json
  - penmanship_report.json
  - page_highlights.json

Corpus:
  - data/page_highlights.json (pages where events occur)
  - data/penmanship_corpus.json
  - data/penmanship_wai.json (AI batch ingestion schema)

Usage:
  python3 glyph-pipeline.py --page 10
  python3 glyph-pipeline.py --all
  python3 glyph-pipeline.py --all --force-glyphs
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.glyph_cropper import extract_page_glyphs  # noqa: E402
from tools.page_highlights import build_highlights_index, build_page_highlights  # noqa: E402
from tools.penmanship_analysis import build_corpus_summary, build_penmanship_report  # noqa: E402


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


def update_wai_schema(repo: Path, pages: list[int]) -> Path:
    """Workflow-AI ingestion manifest for batch penmanship / glyph enrichment."""
    entries = []
    for page in pages:
        page_dir = repo / "processed" / f"page_{page:03d}"
        entries.append({
            "page": page,
            "glyph_index": f"processed/page_{page:03d}/glyph_index.json",
            "penmanship_report": f"processed/page_{page:03d}/penmanship_report.json",
            "page_highlights": f"processed/page_{page:03d}/page_highlights.json",
            "grok_penmanship": f"processed/page_{page:03d}/grok_penmanship.json",
            "layers": {
                "raw": f"processed/page_{page:03d}/raw.png",
                "artistic_vellum": f"processed/page_{page:03d}/artistic_vellum.jpg",
                "clean_white": f"processed/page_{page:03d}/clean_white.jpg",
                "grok_artistic_vellum": f"processed/page_{page:03d}/grok_artistic_vellum.jpg",
                "grok_clean_white": f"processed/page_{page:03d}/grok_clean_white.jpg",
            },
            "ai_tasks": [
                "classify_glyph_crops",
                "assess_penmanship_flow",
                "estimate_scribal_speed",
                "generate_stroke_animation_sequence",
                "refine_highlight_bboxes",
            ],
        })

    wai = {
        "schema": "codex-regius-penmanship-wai/v1",
        "corpus": "GKS 2365 4to",
        "purpose": "Batch AI ingestion for glyph classification, penmanship flow, and live animation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": entries,
        "batch_prompts": {
            "penmanship": (
                "Assess scribal flow, hand dexterity, copying speed, and penmanship quality. "
                "Return animation_sequence: ordered glyph ids for stroke-reveal animation."
            ),
            "glyph_classify": "Re-classify each glyph crop to Old Norse letterforms with variant tags.",
            "highlights": "Refine bounding boxes for marginalia, stains, corrections on this folio.",
        },
    }
    out = repo / "data" / "penmanship_wai.json"
    out.write_text(json.dumps(wai, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex Regius glyph & penmanship pipeline")
    parser.add_argument("--page", type=int)
    parser.add_argument("--batch", help="e.g. 1-20")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--force-glyphs", action="store_true")
    args = parser.parse_args()

    if args.page:
        pages = [args.page]
    elif args.batch:
        pages = parse_pages(args.batch)
    elif args.all:
        pages = list(range(1, 145))
    else:
        parser.print_help()
        return 1

    print(f"🔤 Glyph Pipeline — {len(pages)} page(s)")
    ok = 0
    for page in pages:
        try:
            glyph_data = extract_page_glyphs(page, REPO, force=args.force_glyphs)
            grok_path = REPO / "processed" / f"page_{page:03d}" / "grok_penmanship.json"
            grok_pen = json.loads(grok_path.read_text(encoding="utf-8")) if grok_path.is_file() else None
            build_penmanship_report(page, REPO, grok_pen)
            build_page_highlights(page, REPO)
            n = glyph_data.get("glyph_count", 0)
            print(f"✅ Page {page:3d} — {n} glyphs, penmanship, highlights")
            ok += 1
        except Exception as exc:
            print(f"❌ Page {page:3d} — {exc}")

    idx = build_highlights_index(REPO, pages)
    corpus = build_corpus_summary(REPO, pages)
    wai = update_wai_schema(REPO, pages)
    print(f"\n📍 Highlights index: {idx['pages_with_events']} pages with events")
    print(f"✍️  Penmanship corpus: {corpus.get('pages_analyzed', 0)} pages")
    print(f"🤖 WAI manifest → {wai}")
    print(f"\nDone: {ok}/{len(pages)}")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())