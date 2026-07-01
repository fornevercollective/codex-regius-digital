#!/usr/bin/env python3
"""Build data/completion_snapshot.json — pipeline coverage for all 144 folios."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARTIFACTS = [
    ("interactive.html", "interactive.html"),
    ("qc_report.json", "qc_report.json"),
    ("ai_assessment.md", "ai_assessment.md"),
    ("scholarly_report.json", "scholarly_report.json"),
    ("grok_clean_white.jpg", "grok_clean_white.jpg"),
    ("grok_artistic_vellum.jpg", "grok_artistic_vellum.jpg"),
    ("grok_doodles.json", "grok_doodles.json"),
    ("glyph_index.json", "glyph_index.json"),
]


def main() -> int:
    rows = []
    summary: dict[str, dict] = {}
    for key, _ in ARTIFACTS:
        summary[key] = {"count": 0, "missing": []}

    qc_ok = qc_review = 0
    for n in range(1, 145):
        d = REPO / "processed" / f"page_{n:03d}"
        row = {"page": n}
        for key, fname in ARTIFACTS:
            ok = (d / fname).is_file()
            row[key] = ok
            if ok:
                summary[key]["count"] += 1
            else:
                summary[key]["missing"].append(n)
        q = d / "qc_report.json"
        if q.is_file():
            st = json.loads(q.read_text(encoding="utf-8")).get("status", "")
            row["qc_status"] = st
            if st == "ok":
                qc_ok += 1
            elif st == "needs_review":
                qc_review += 1
        rows.append(row)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manuscript": "GKS 2365 4to",
        "pages_total": 144,
        "summary": summary,
        "qc": {"ok": qc_ok, "needs_review": qc_review},
        "pages": rows,
    }
    path = REPO / "data" / "completion_snapshot.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ completion_snapshot.json")
    for key, s in summary.items():
        print(f"   {key}: {s['count']}/144")
    print(f"   qc: {qc_ok} ok, {qc_review} needs_review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())