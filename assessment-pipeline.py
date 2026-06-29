#!/usr/bin/env python3
"""
Full scholarly assessment pipeline for Codex Regius.

Generates per page: codicology, calligraphy, doodles, liturgy, etymology,
enhanced ai_assessment, scholarly_report.json

Usage:
  python3 assessment-pipeline.py --page 10
  python3 assessment-pipeline.py --all
  python3 assessment-pipeline.py --all --export-font
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.font_export import export_font_scaffold  # noqa: E402
from tools.scholarly_assessment import ScholarlyAssessmentEngine  # noqa: E402


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex Regius scholarly assessment")
    parser.add_argument("--page", type=int)
    parser.add_argument("--batch", help="e.g. 1-20")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--export-font", action="store_true")
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

    engine = ScholarlyAssessmentEngine(REPO)
    print(f"📜 Scholarly Assessment — {len(pages)} page(s)")

    ok = 0
    for page in pages:
        try:
            engine.run_page(page)
            print(f"✅ Page {page:3d} — codicology, calligraphy, doodles, liturgy, etymology, AI report")
            ok += 1
        except Exception as exc:
            print(f"❌ Page {page:3d} — {exc}")

    if args.export_font or args.all:
        out = export_font_scaffold(REPO)
        print(f"\n🔤 Font scaffold → {out}")

    print(f"\nDone: {ok}/{len(pages)}")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())