"""Generate full scholarly assessments per page: codicology, calligraphy, doodles, liturgy."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from tools.citations import HANDRIT_BASE, MANUSCRIPT_ID, references_block
from tools.poem_mapper import lookup_page


def load_json(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def extract_transcription(page_dir: Path) -> str:
    md = page_dir / "ai_assessment.md"
    if not md.is_file():
        return ""
    text = md.read_text(encoding="utf-8")
    m = re.search(r"## Original Text.*?\n```\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def detect_misprints(text: str) -> list[dict]:
    issues = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"(.)\1{3,}", line):
            issues.append({"line": i, "type": "repeated_glyph", "note": "Possible scribal hesitation or stain"})
        if "?" in line or "□" in line:
            issues.append({"line": i, "type": "uncertain_reading", "note": "Editorial uncertainty mark"})
    return issues


def load_grok_doodles(page_dir: Path) -> dict | None:
    path = page_dir / "grok_doodles.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def generate_doodles_catalog(page: int, transcription: str, codicology: dict, page_dir: Path | None = None) -> str:
    grok = load_grok_doodles(page_dir) if page_dir else None
    misprints = detect_misprints(transcription)

    if grok and grok.get("items"):
        rows = "\n".join(
            f"| {it.get('id', '—')} | {it.get('region', '—')} | {it.get('type', '—')} | "
            f"{it.get('description', '—')} | {it.get('scholarly_note', '—')} |"
            for it in grok["items"]
        )
        grok_note = f"\n*Grok vision survey ({grok.get('surveyed_at', 'unknown')}) — confidence: {grok.get('confidence', 'medium')}*\n"
    else:
        rows = (
            f"| M-{page:03d}-01 | margin | pending | Visual survey required | Cross-ref. grok_variations/ |\n"
            f"| M-{page:03d}-02 | text block | scratch | Hair-side abrasion check | Compare raw vs clean_white |\n"
            f"| M-{page:03d}-03 | lower margin | doodle | [pending identification] | Animal/face/pen trial? |"
        )
        grok_note = ""

    damage = ""
    if grok:
        for note in grok.get("damage_notes", []):
            damage += f"- {note}\n"
        for scratch in grok.get("scratches", []):
            damage += f"- **Scratch**: {scratch}\n"
    if not damage:
        damage = (
            f"- **Parchment**: {codicology.get('vellum', {}).get('preparation', {}).get('quality', 'High')} preparation\n"
            f"- **Ink**: {codicology.get('ink', {}).get('type', 'Iron-gall')} — check for offset and ghosting\n"
            "- **Automated flags**: Compare `raw.png`, `clean_white.jpg`, `grok_clean_white.jpg`"
        )

    return f"""# Marginalia, Doodles & Surface Analysis — Page {page}

**Manuscript**: {MANUSCRIPT_ID}
**Source**: `GKS2365_page_{page}.png`
**Handrit**: [{HANDRIT_BASE}]({HANDRIT_BASE})

## Doodles & Marginalia Inventory
| ID | Region | Type | Description | Scholarly note |
|----|--------|------|-------------|----------------|
{rows}
{grok_note}
## Misprints & Scribal Corrections
| Line | Type | Note |
|------|------|------|
{chr(10).join(f"| {m['line']} | {m['type']} | {m['note']} |" for m in misprints) if misprints else "| — | — | None auto-detected; manual paleographic pass recommended |"}

## Scratch & Damage Analysis
{damage}

## AI Assessment Hooks
- Link to `scholarly_report.json` for LLM ingestion
- Doodle bounding boxes: pending computer-vision pass
- Thematic tags: see `liturgy_comparison.md`

*Enrich with handrit.is high-res survey and AM 748 collation.*
"""


def generate_codicology_page(page: int, master: dict) -> str:
    v = master.get("vellum", {})
    return f"""# Vellum Codicology — Page {page}

## Manuscript-Level Assessment (GKS 2365 4to)
| Field | Assessment |
|-------|------------|
| **Animal** | {v.get('animal', 'Calf')} ({v.get('animal_confidence', 'high')} confidence) |
| **Region / Origin** | {v.get('region_origin', 'Iceland')} |
| **Age estimate** | {v.get('age_estimate', 'c. 1260–1280')} |
| **Preparation** | {v.get('preparation', {}).get('notes', v.get('preparation', {}).get('quality', 'High'))} |

### Preparation Notes
- Fiber pattern: {v.get('preparation', {}).get('fiber_pattern', 'Icelandic typical')}
- Finish: {v.get('preparation', {}).get('finish', 'Well-prepared sheets')}
- Common defects: {', '.join(v.get('preparation', {}).get('defects_common', []))}

## Page-Specific Physical Notes (Page {page})
- **Hair vs flesh side**: [pending per-folio identification]
- **Sheet continuity**: [quire mapping pending]
- **Thickness / opacity**: Visual compare across `artistic_vellum.jpg` layers

## Provenance Chain
See `data/scribe_timeline.json` for full timeline from copying (c. 1270) to modern stewardship.

## Citations
{chr(10).join('- ' + c for c in master.get('citations', []))}
"""


def generate_calligraphy_sheet(page: int, alphabet: dict, scribe: dict) -> str:
    letters = alphabet.get("letters", [])
    rows = "\n".join(
        f"| {L['char']} | {L['name']} | {', '.join(L.get('variants', []))} | {L.get('notes', '')} |"
        for L in letters[:20]
    )
    return f"""# Calligraphy Reference — Page {page}

**Scribe**: {scribe.get('label', 'CR-main-hand')}
**Script**: {alphabet.get('script', 'Gothic book hand')}

## Alphabet Overview (excerpt — full set in `data/alphabet_reference.json`)
| Glyph | Name | Variants on this page | Notes |
|-------|------|----------------------|-------|
{rows}
| … | … | See paleography hub for full A–þ set | |

## Scribe Timeline Descriptor
- **Life**: {scribe.get('biography', {}).get('life_dates', 'fl. c. 1260–1280')}
- **Training**: {scribe.get('training_context', 'Icelandic scriptorium')}
- **Hand consistency**: Single main hand (pending page-level exception log)

## Script-to-Font Export
- Status: `{alphabet.get('font_export', {}).get('status', 'scaffold')}`
- Export: `python3 assessment-pipeline.py --export-font`
- Targets: {', '.join(alphabet.get('font_export', {}).get('target_tools', ['FontForge']))}

## Cross-Manuscript Hand Comparison
{chr(10).join('- **' + x['manuscript'] + '**: ' + x['relation'] for x in scribe.get('cross_manuscript_hands', []))}

*Capture letterform crops from page {page} to populate font glyphs.*
"""


def page_poem_entry(page: int, liturgy: dict, repo_root: Path) -> dict:
    index = {e["page"]: e for e in liturgy.get("page_index", [])}
    if page in index:
        return index[page]
    return lookup_page(page, repo_root=repo_root)


def generate_liturgy_comparison(
    page: int, liturgy: dict, themes: dict, transcription: str, repo_root: Path
) -> str:
    poem_info = page_poem_entry(page, liturgy, repo_root)
    poem_block = ""
    if poem_info.get("poem"):
        flags = []
        if poem_info.get("lacuna_before"):
            flags.append("lacuna before")
        if poem_info.get("lacuna_after"):
            flags.append("lacuna after")
        if poem_info.get("extended_scan"):
            flags.append(f"extended scan → CR p.{poem_info.get('maps_to_cr_page', '?')}")
        flag_text = f" ({'; '.join(flags)})" if flags else ""
        poem_block = (
            f"\n### Poem boundary (page {page})\n"
            f"| Field | Value |\n|-------|-------|\n"
            f"| **Poem** | {poem_info['poem']} |\n"
            f"| **Section** | {poem_info.get('section', '—')} |\n"
            f"| **Corpus type** | {poem_info.get('type', '—')}{flag_text} |\n"
        )

    stanzas = [s for s in liturgy.get("key_stanzas", []) if page in s.get("pages_cr", [])]
    stanza_block = poem_block
    for s in stanzas:
        stanza_block += f"\n### {s['poem']} st. {s['stanza']} (`{s['id']}`)\n"
        stanza_block += f"**CR text**: {s.get('cr_text', transcription[:80] or '[pending]')}\n\n"
        stanza_block += "| Witness | Text | Note |\n|---------|------|------|\n"
        for v in s.get("variants", []):
            stanza_block += f"| {v['witness']} | {v['text']} | {v.get('note', '')} |\n"
        if s.get("runic_parallels"):
            stanza_block += "\n**Runic / carving parallels**:\n"
            for r in s["runic_parallels"]:
                stanza_block += f"- {r['source']}: {r['note']}\n"

    if not stanza_block:
        stanza_block = "\n*No poem boundary mapped — run `tools/build_liturgy_map.py`.*\n"

    poem_name = poem_info.get("poem", "").split(" / ")[0]
    relevant = [
        t for t in themes.get("themes", [])
        if not poem_name or any(p in poem_name or poem_name in p for p in t.get("cr_poems", []))
    ]
    theme_lines = "\n".join(
        f"- **{t['label']}**: {', '.join(t.get('pagan_concepts', [])[:3])} ↔ {', '.join(t.get('christian_parallels', [])[:2])}"
        for t in (relevant or themes.get("themes", []))[:4]
    )

    return f"""# Comparative Liturgy & Text Evolution — Page {page}

## Witness Manuscripts
| Siglum | Name | Date | Role |
|--------|------|------|------|
{chr(10).join('| ' + w['siglum'] + ' | ' + w['name'] + ' | ' + w['date'] + ' | ' + w['role'] + ' |' for w in liturgy.get('witnesses', []))}

## Stanza Collation (this page)
{stanza_block}

## Organ of the Language
- **Phonology**: {liturgy.get('organ_of_language', {}).get('phonology', 'Old West Norse')}
- **Meter**: {liturgy.get('organ_of_language', {}).get('meter', 'Eddic fornyrðislag / ljóðaháttr')}
- **Oral layer**: {liturgy.get('organ_of_language', {}).get('oral_layer', '')}
- **Carving trace**: {liturgy.get('organ_of_language', {}).get('carving_trace', '')}

## Thematic Cross-References (Christian ↔ Pagan parallels)
{theme_lines}

*Expand stanza keys as poem boundaries are mapped across all 144 pages.*
"""


def generate_enhanced_etymology(page: int, transcription: str) -> str:
    tokens = re.findall(r"\b[\wþðæöáíúóéǫꝩ]+\b", transcription[:500], re.UNICODE)[:15]
    token_rows = "\n".join(f"| {t} | [etymology pending] | [cognates] | Neckel/Kuhn |" for t in tokens) if tokens else "| — | — | — | — |"
    return f"""# Etymology & Dialect — Page {page}

**Language**: Old West Norse (Icelandic, c. 1270–1280)
**Dialect**: Conservative Icelandic transmission; possible Norwegian substrate in oral exemplar

## Line-Level Lexicon (auto-extracted tokens)
| Form | Etymology | Cognates | Edition ref |
|------|-----------|----------|-------------|
{token_rows}

## Morphological Features
| Feature | Example on page | Note |
|---------|-----------------|------|
| u-umlaut | [pending] | Icelandic retention |
| i-mutation | [pending] | |
| Archaic ǫ/ö | [pending] | Normalisation vs manuscript |

## Religious-Lexical Layer
- Pagan theonyms and mythic place-names: cross-ref `liturgy_comparison.md`
- Christian loan or framing vocabulary: compare Hauksbók prose

## Comparative Manuscripts
- AM 748 I 4to · Hauksbók · Snorra Edda

*Aid AI assessment: pair with `thematic_crossrefs.json` for concept clustering.*
"""


def generate_ai_assessment_enhanced(
    page: int,
    template_path: Path,
    transcription: str,
    codicology: dict,
    scribe: dict,
) -> str:
    base = template_path.read_text(encoding="utf-8") if template_path.is_file() else ""
    if not base:
        base = f"# AI Assessment — Page {page}\n\n"
    base = re.sub(r"- \*\*Page Number\*\* \(user labeling\):\s*", f"- **Page Number**: {page}\n", base, count=1)
    if transcription and "[PASTE" not in transcription:
        base = re.sub(
            r"(## Original Text[^\n]*\n```\n)(.*?)(```)",
            lambda m: m.group(1) + transcription + m.group(3),
            base,
            count=1,
            flags=re.DOTALL,
        )

    extra = f"""

---

## Integrated Scholarly Modules (auto-linked)
| Module | File |
|--------|------|
| Vellum codicology | `codicology.md` |
| Doodles & misprints | `doodles_catalog.md` |
| Calligraphy / font | `calligraphy_sheet.md` |
| Liturgy comparison | `liturgy_comparison.md` |
| Etymology | `etymology.md` |
| Machine report | `scholarly_report.json` |

## Vellum Codicology Summary
- **Animal**: {codicology.get('vellum', {}).get('animal', 'Calf')}
- **Origin**: {codicology.get('vellum', {}).get('region_origin', 'Iceland')}
- **Age**: {codicology.get('vellum', {}).get('age_estimate', 'c. 1260–1280')}

## Scribe Context
- **Hand**: {scribe.get('hand_type', 'Gothic book hand')}
- **Timeline**: {scribe.get('biography', {}).get('life_dates', 'fl. c. 1270')}

## AI / LLM Optimized Block (extended)
```json
{json.dumps({
    "manuscript": MANUSCRIPT_ID,
    "page": page,
    "modules": ["codicology", "doodles", "calligraphy", "liturgy", "etymology"],
    "vellum": codicology.get("vellum", {}),
    "scribe_id": scribe.get("scribe_id"),
    "transcription_preview": transcription[:300] if transcription else "",
    "handrit_url": HANDRIT_BASE,
    "assessment_at": datetime.now(timezone.utc).isoformat(),
}, indent=2, ensure_ascii=False)}
```
"""
    if "## Integrated Scholarly Modules" not in base:
        base += extra
    return base


def generate_scholarly_report_json(
    page: int,
    page_dir: Path,
    codicology: dict,
    scribe: dict,
    alphabet: dict,
    liturgy: dict,
    themes: dict,
    transcription: str,
    repo_root: Path,
) -> dict:
    poem_info = page_poem_entry(page, liturgy, repo_root)
    grok_doodles = load_grok_doodles(page_dir)
    return {
        "manuscript": MANUSCRIPT_ID,
        "page": page,
        "handrit_url": HANDRIT_BASE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "codicology": codicology.get("vellum", {}),
        "scribe": {
            "id": scribe.get("scribe_id"),
            "label": scribe.get("label"),
            "timeline": scribe.get("timeline", []),
        },
        "calligraphy": {
            "script": alphabet.get("script"),
            "letter_count": len(alphabet.get("letters", [])),
            "font_export_ready": True,
        },
        "doodles": {
            "inventory_status": "grok_vision" if grok_doodles else "scaffold",
            "item_count": len(grok_doodles.get("items", [])) if grok_doodles else 0,
            "misprints_detected": len(detect_misprints(transcription)),
        },
        "poem": {
            "name": poem_info.get("poem", ""),
            "section": poem_info.get("section", ""),
            "type": poem_info.get("type", ""),
            "extended_scan": poem_info.get("extended_scan", False),
        },
        "liturgy": {
            "witnesses": [w["siglum"] for w in liturgy.get("witnesses", [])],
            "stanzas_on_page": [s["id"] for s in liturgy.get("key_stanzas", []) if page in s.get("pages_cr", [])],
        },
        "themes": [t["id"] for t in themes.get("themes", [])],
        "transcription_chars": len(transcription),
        "layers": [p.name for p in page_dir.iterdir() if p.is_file()],
        "citations": references_block(["neckel_kuhn", "handrit_viewer", "ami_institute"]),
    }


class ScholarlyAssessmentEngine:
    def __init__(self, repo_root: Path):
        self.repo = repo_root.resolve()
        self.processed = self.repo / "processed"
        self.data = self.repo / "data"
        self.template = self.repo / "AI_Assessment_Template.md"

    def run_page(self, page: int) -> dict:
        page_dir = self.processed / f"page_{page:03d}"
        page_dir.mkdir(parents=True, exist_ok=True)

        codicology = load_json(self.data / "codicology.json")
        scribe = load_json(self.data / "scribe_timeline.json")
        alphabet = load_json(self.data / "alphabet_reference.json")
        liturgy = load_json(self.data / "liturgy_comparisons.json")
        themes = load_json(self.data / "thematic_crossrefs.json")

        transcription = extract_transcription(page_dir)

        (page_dir / "doodles_catalog.md").write_text(
            generate_doodles_catalog(page, transcription, codicology, page_dir), encoding="utf-8"
        )
        (page_dir / "codicology.md").write_text(
            generate_codicology_page(page, codicology), encoding="utf-8"
        )
        (page_dir / "calligraphy_sheet.md").write_text(
            generate_calligraphy_sheet(page, alphabet, scribe), encoding="utf-8"
        )
        (page_dir / "liturgy_comparison.md").write_text(
            generate_liturgy_comparison(page, liturgy, themes, transcription, self.repo), encoding="utf-8"
        )
        (page_dir / "etymology.md").write_text(
            generate_enhanced_etymology(page, transcription), encoding="utf-8"
        )

        ai_path = page_dir / "ai_assessment.md"
        ai_path.write_text(
            generate_ai_assessment_enhanced(page, self.template, transcription, codicology, scribe),
            encoding="utf-8",
        )

        report = generate_scholarly_report_json(
            page, page_dir, codicology, scribe, alphabet, liturgy, themes, transcription, self.repo
        )
        (page_dir / "scholarly_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        meta_path = self.repo / "metadata" / f"page_{page:03d}.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            for f in (
                "codicology.md",
                "calligraphy_sheet.md",
                "liturgy_comparison.md",
                "scholarly_report.json",
            ):
                if f not in meta.get("layers", []):
                    meta.setdefault("layers", []).append(f)
            meta["scholarly_assessment"] = True
            meta["scholarly_assessment_at"] = report["generated_at"]
            poem = report.get("poem", {})
            if poem.get("name"):
                meta["poem"] = poem["name"].split(" / ")[0]
                meta["poem_full"] = poem["name"]
                meta["poem_section"] = poem.get("section", "")
                meta["poem_type"] = poem.get("type", "")
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        return {"page": page, "status": "ok", "modules": 6}