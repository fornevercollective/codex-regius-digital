#!/usr/bin/env python3
"""
Codex Regius QC + OCR Error Correction Pipeline

Usage:
  python3 qc-pipeline.py --page 10
  python3 qc-pipeline.py --batch 1-20 --auto-suggest
  python3 qc-pipeline.py --all --export-report --auto-apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from tools.qc_engine import QcEngine  # noqa: E402


def parse_pages(spec: str) -> list[int]:
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
    parser = argparse.ArgumentParser(description="Codex Regius QC + OCR correction")
    parser.add_argument("--page", type=int, help="QC a single page")
    parser.add_argument("--batch", help="Page range e.g. 1-20")
    parser.add_argument("--all", action="store_true", help="QC all 144 pages")
    parser.add_argument("--auto-suggest", action="store_true", default=True)
    parser.add_argument("--no-suggest", action="store_true", help="Skip correction suggestions")
    parser.add_argument("--auto-apply", action="store_true", help="Apply safe OCR corrections")
    parser.add_argument("--save-previews", action="store_true", help="Save preprocessing previews")
    parser.add_argument("--export-report", action="store_true", help="Write collection summary JSON")
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

    engine = QcEngine(REPO_ROOT)
    auto_suggest = not args.no_suggest

    print(f"🔍 QC Pipeline — {len(pages)} page(s)")
    results = []
    needs_review = 0

    for page in pages:
        try:
            report = engine.run_page(
                page,
                auto_suggest=auto_suggest,
                auto_apply=args.auto_apply,
                save_previews=args.save_previews,
            )
            results.append(report)
            icon = "✅" if report["status"] == "ok" else "⚠️"
            issues = len(report.get("issues", []))
            print(f"{icon} Page {page:3d} — {report['status']} ({issues} issues)")
            if report["status"] != "ok":
                needs_review += 1
        except Exception as exc:
            print(f"❌ Page {page:3d} — {exc}")
            needs_review += 1

    if args.export_report or args.all:
        summary_path = REPO_ROOT / "metadata" / "qc_summary.json"
        summary = {
            "pages_checked": len(results),
            "needs_review": needs_review,
            "ok": len(results) - needs_review,
            "reports": [
                {
                    "page": r["page"],
                    "status": r["status"],
                    "issues": len(r.get("issues", [])),
                }
                for r in results
            ],
        }
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"\n📋 Summary → {summary_path}")

    print(f"\nDone: {len(results)} checked, {needs_review} need review.")
    return 0 if needs_review == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())