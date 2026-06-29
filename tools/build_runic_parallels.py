#!/usr/bin/env python3
"""Merge liturgy key_stanzas runic data into data/runic_parallels.json page index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def artifact_lookup(artifacts: list[dict]) -> dict[str, dict]:
    return {a["id"]: a for a in artifacts}


def main() -> int:
    runic_path = REPO / "data" / "runic_parallels.json"
    liturgy_path = REPO / "data" / "liturgy_comparisons.json"
    runic = json.loads(runic_path.read_text(encoding="utf-8"))
    liturgy = json.loads(liturgy_path.read_text(encoding="utf-8")) if liturgy_path.is_file() else {}

    by_id = artifact_lookup(runic.get("artifacts", []))
    page_map: dict[int, dict] = {}

    for link in runic.get("stanza_links", []):
        for page in link.get("pages_cr", []):
            entry = page_map.setdefault(page, {"page": page, "stanza_links": [], "artifact_ids": set()})
            entry["stanza_links"].append(link["id"])
            for aid in link.get("artifact_ids", []):
                entry["artifact_ids"].add(aid)

    for stanza in liturgy.get("key_stanzas", []):
        for rp in stanza.get("runic_parallels", []):
            src = rp.get("source", "")
            if not src:
                continue
            for page in stanza.get("pages_cr", []):
                entry = page_map.setdefault(page, {"page": page, "stanza_links": [], "artifact_ids": set()})
                entry["stanza_links"].append(stanza.get("id", ""))
                entry.setdefault("liturgy_notes", []).append({"stanza": stanza.get("id"), "source": src, "note": rp.get("note", "")})

    for ps in runic.get("poem_summaries", []):
        for p in range(ps["page_start"], ps["page_end"] + 1):
            entry = page_map.setdefault(p, {"page": p, "stanza_links": [], "artifact_ids": set()})
            entry["poem_summary"] = ps

    page_index = []
    for page in sorted(page_map):
        e = page_map[page]
        aids = sorted(e.get("artifact_ids", set()))
        page_index.append({
            "page": page,
            "artifact_ids": aids,
            "artifacts": [by_id[a] for a in aids if a in by_id],
            "stanza_link_ids": list(dict.fromkeys(e.get("stanza_links", []))),
            "poem_summary": e.get("poem_summary"),
            "liturgy_notes": e.get("liturgy_notes", []),
        })

    runic["page_index"] = page_index
    runic["generated_at"] = datetime.now(timezone.utc).isoformat()
    runic_path.write_text(json.dumps(runic, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ runic_parallels.json — {len(page_index)} pages indexed, {len(runic.get('artifacts', []))} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())