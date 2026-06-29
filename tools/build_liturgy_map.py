#!/usr/bin/env python3
"""Merge poem_boundaries.json into liturgy_comparisons.json (page_index + ranges)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from tools.poem_mapper import build_page_index, load_boundaries, poem_ranges  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build liturgy page index from poem boundaries")
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--update-metadata", action="store_true", help="Patch metadata/page_NNN.json poem fields")
    args = parser.parse_args()

    repo = args.repo.resolve()
    boundaries = load_boundaries(repo)
    liturgy_path = repo / "data" / "liturgy_comparisons.json"
    liturgy = json.loads(liturgy_path.read_text(encoding="utf-8"))

    page_index = build_page_index(boundaries)
    ranges = poem_ranges(boundaries)

    liturgy["corpus"] = liturgy.get("corpus", "Poetic Edda (Codex Regius core)")
    liturgy["page_index"] = page_index
    liturgy["poem_ranges"] = ranges
    liturgy["poem_boundaries_source"] = boundaries.get("source", "")
    liturgy["lacuna_note"] = boundaries.get("lacuna_note", "")
    liturgy["mapped_at"] = datetime.now(timezone.utc).isoformat()

    # Fix exemplar stanzas that reference wrong CR pages
    for stanza in liturgy.get("key_stanzas", []):
        if stanza.get("id") == "voluspa-01":
            stanza["pages_cr"] = [1]
        elif stanza.get("id") == "voluspa-02":
            stanza["pages_cr"] = [1]

    liturgy_path.write_text(json.dumps(liturgy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ liturgy_comparisons.json — {len(page_index)} pages, {len(ranges)} poem ranges")

    if args.update_metadata:
        meta_dir = repo / "metadata"
        updated = 0
        for entry in page_index:
            page = entry["page"]
            meta_path = meta_dir / f"page_{page:03d}.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            poem = entry["poem"].split(" / ")[0] if entry.get("poem") else ""
            if meta.get("poem") != poem or meta.get("poem_section") != entry.get("section"):
                meta["poem"] = poem
                meta["poem_full"] = entry.get("poem", "")
                meta["poem_section"] = entry.get("section", "")
                meta["poem_type"] = entry.get("type", "")
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                updated += 1
        print(f"✅ metadata — {updated} page JSON files updated")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())