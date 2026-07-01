#!/usr/bin/env python3
"""Build VisColl-inspired folio/quire map for GKS 2365 4to (144 sides)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES = 144
LEAVES_PER_QUIRE = 8  # 18 quires × 8 sides = 144


def folio_label(page: int) -> tuple[str, str, str]:
    """Map digital page 1–144 → folio number, recto/verso, quire id."""
    leaf = (page + 1) // 2
    side = "recto" if page % 2 == 1 else "verso"
    quire_num = (page - 1) // LEAVES_PER_QUIRE + 1
    pos_in_quire = (page - 1) % LEAVES_PER_QUIRE + 1
    return f"{leaf}{side[0]}", side, f"Q{quire_num:02d}"


def main() -> int:
    quires = []
    for q in range(1, PAGES // LEAVES_PER_QUIRE + 1):
        start = (q - 1) * LEAVES_PER_QUIRE + 1
        end = q * LEAVES_PER_QUIRE
        quires.append({
            "id": f"Q{q:02d}",
            "index": q,
            "page_start": start,
            "page_end": end,
            "leaves": LEAVES_PER_QUIRE // 2,
            "note": "Scaffold — verify against physical collation survey",
        })

    folios = []
    for page in range(1, PAGES + 1):
        label, side, quire = folio_label(page)
        folios.append({
            "page": page,
            "folio": label,
            "side": side,
            "quire": quire,
            "position_in_quire": (page - 1) % LEAVES_PER_QUIRE + 1,
            "binding_edge": "spine" if side == "recto" else "fore-edge",
            "signature": None,
            "catchword": None,
        })

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manuscript": "GKS 2365 4to",
        "model": "VisColl-inspired",
        "spec": "https://viscoll.org/collation/",
        "tools": [
            "https://github.com/KislakCenter/VisColl",
            "https://github.com/utlib/VisualCollation",
            "https://github.com/utlib/iiif-to-go-viscoll",
        ],
        "format": {
            "pages": "Digital facsimile index 1–144 (handrit.is pagination)",
            "quires": f"{len(quires)} quires × {LEAVES_PER_QUIRE} sides (scaffold)",
        },
        "quires": quires,
        "folios": folios,
    }
    path = REPO / "data" / "viscoll_collation.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ viscoll_collation.json — {len(folios)} folio sides, {len(quires)} quires")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())