"""Export alphabet reference to FontForge/Glyphs-compatible JSON."""

from __future__ import annotations

import json
from pathlib import Path


def export_font_scaffold(repo_root: Path, out_path: Path | None = None) -> Path:
    data_path = repo_root / "data" / "alphabet_reference.json"
    alphabet = json.loads(data_path.read_text(encoding="utf-8"))

    glyphs = []
    for letter in alphabet.get("letters", []):
        glyphs.append({
            "unicode": letter["char"],
            "name": letter["name"],
            "variants": letter.get("variants", []),
            "notes": letter.get("notes", ""),
            "svg_path": None,
            "source_page": None,
        })

    font = {
        "font_name": "CodexRegius-CR-main-hand",
        "family": "Codex Regius",
        "style": "Regular",
        "script": alphabet.get("script"),
        "scribe_id": alphabet.get("scribe_id"),
        "units_per_em": 1000,
        "ascender": 800,
        "descender": -200,
        "glyphs": glyphs,
        "abbreviations": alphabet.get("abbreviations", []),
        "export_targets": ["FontForge (.glyphs)", "Glyphs app", "UFO via fontmake"],
        "instructions": (
            "1. Capture letter crops from processed/page_NNN/ into glyphs[].svg_path\n"
            "2. Import JSON in FontForge: Element → Merge → Import glyphs\n"
            "3. Or use fontmake / gftools for production OTF"
        ),
    }

    out = out_path or (repo_root / "data" / "codex_regius_font.json")
    out.write_text(json.dumps(font, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out