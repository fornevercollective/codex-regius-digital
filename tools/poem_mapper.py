"""Map GKS2365 user page numbers to Eddic poems."""

from __future__ import annotations

import json
from pathlib import Path


def load_boundaries(repo_root: Path) -> dict:
    path = repo_root / "data" / "poem_boundaries.json"
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_page(page: int, boundaries: dict | None = None, repo_root: Path | None = None) -> dict:
    if boundaries is None:
        boundaries = load_boundaries(repo_root or Path("."))

    folios = {f["page"]: f for f in boundaries.get("folios", [])}

    if page in folios:
        return folios[page]

    ext = boundaries.get("extended_pages", {})
    lo, hi = ext.get("range", [91, 144])
    cr_lo, cr_hi = ext.get("maps_to_cr", [65, 90])
    if lo <= page <= hi and hi > lo:
        cr_page = cr_lo + round((page - lo) * (cr_hi - cr_lo) / (hi - lo))
        base = folios.get(cr_page, {})
        return {
            "page": page,
            "poem": base.get("poem", "Heroic coda (extended scan)"),
            "section": base.get("section", ""),
            "type": base.get("type", "heroic"),
            "extended_scan": True,
            "maps_to_cr_page": cr_page,
        }

    return {"page": page, "poem": "", "section": "", "type": ""}


def build_page_index(boundaries: dict | None = None, repo_root: Path | None = None) -> list[dict]:
    """Full 1–144 page index for liturgy_comparisons.json."""
    if boundaries is None:
        boundaries = load_boundaries(repo_root or Path("."))

    index: list[dict] = []
    for page in range(1, boundaries.get("pages_total", 144) + 1):
        info = lookup_page(page, boundaries)
        entry = {
            "page": page,
            "poem": info.get("poem", ""),
            "section": info.get("section", ""),
            "type": info.get("type", ""),
        }
        for flag in ("lacuna_before", "lacuna_after", "extended_scan", "maps_to_cr_page"):
            if info.get(flag):
                entry[flag] = info[flag]
        index.append(entry)
    return index


def poem_ranges(boundaries: dict) -> list[dict]:
    """Collapse folios into poem page ranges."""
    ranges: list[dict] = []
    current: dict | None = None
    for folio in boundaries.get("folios", []):
        poem = folio["poem"].split(" / ")[0]
        if current and current["poem"] == poem:
            current["page_end"] = folio["page"]
            current["section_end"] = folio.get("section", "")
        else:
            if current:
                ranges.append(current)
            current = {
                "poem": poem,
                "type": folio.get("type", ""),
                "page_start": folio["page"],
                "page_end": folio["page"],
                "section_start": folio.get("section", ""),
                "section_end": folio.get("section", ""),
            }
    if current:
        ranges.append(current)
    return ranges