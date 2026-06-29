#!/usr/bin/env python3
"""
Grok vision survey for Codex Regius marginalia, doodles, and surface marks.

Analyzes manuscript page images and writes:
  processed/page_NNN/grok_doodles.json
  processed/page_NNN/doodles_catalog.md  (refreshed from vision output)

Usage:
  python3 grok-doodles-script.py --pages 1-10 --skip-existing
  python3 grok-doodles-script.py --all --skip-existing
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

GROK_BIN = shutil.which("grok") or "/Users/tref/.grok/bin/grok"
GROK_MODEL = "grok-build"  # grok-composer-2.5-fast does not accept image inputs
TOTAL_PAGES = 144

VISION_PROMPT = """You are a paleographer surveying Codex Regius (GKS 2365 4to, c. 1270 Iceland).

Examine [Image #1: {image_path}] — manuscript page {page}.

Identify ALL marginalia, doodles, pen trials, faces, animals, decorative marks, stains,
scratches, holes, offset ink, and scribal corrections visible outside or within the text block.

Reply with ONLY valid JSON (no markdown fences) using this schema:
{{
  "page": {page},
  "confidence": "high|medium|low",
  "items": [
    {{
      "id": "M-{page:03d}-01",
      "region": "upper margin|lower margin|left margin|right margin|interlinear|text block",
      "type": "doodle|pen_trial|stain|scratch|correction|decoration|other",
      "description": "brief visual description",
      "scholarly_note": "paleographic interpretation"
    }}
  ],
  "scratches": ["..."],
  "damage_notes": ["..."],
  "summary": "one paragraph overview"
}}

If nothing notable is visible, return items as an empty array with a summary explaining the clean surface.
"""


def parse_page_list(spec: str | None) -> list[int]:
    if not spec:
        return list(range(1, TOTAL_PAGES + 1))
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            pages.update(range(int(start_s), int(end_s) + 1))
        else:
            pages.add(int(part))
    return sorted(p for p in pages if 1 <= p <= TOTAL_PAGES)


def extract_json_block(text: str) -> dict | None:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def pick_source_image(page: int, repo: Path, root: Path) -> Path | None:
    page_dir = repo / "processed" / f"page_{page:03d}"
    for candidate in (
        page_dir / "grok_clean_white.jpg",
        page_dir / "clean_white.jpg",
        page_dir / "raw.png",
        root / "png" / f"GKS2365_page_{page}.png",
        root / "jpg" / f"GKS2365_page_{page}.jpg",
    ):
        if candidate.is_file():
            return candidate
    return None


def render_doodles_md(page: int, data: dict, handrit_base: str) -> str:
    rows = "\n".join(
        f"| {it.get('id', '—')} | {it.get('region', '—')} | {it.get('type', '—')} | "
        f"{it.get('description', '—')} | {it.get('scholarly_note', '—')} |"
        for it in data.get("items", [])
    ) or "| — | — | — | No marginalia detected | Grok vision pass |"

    scratches = "\n".join(f"- {s}" for s in data.get("scratches", [])) or "- None noted"
    damage = "\n".join(f"- {d}" for d in data.get("damage_notes", [])) or "- Routine vellum wear only"

    return f"""# Marginalia, Doodles & Surface Analysis — Page {page}

**Manuscript**: GKS 2365 4to
**Source**: `GKS2365_page_{page}.png`
**Handrit**: [{handrit_base}]({handrit_base})
**Survey**: Grok vision ({data.get('surveyed_at', '')}) — confidence **{data.get('confidence', 'medium')}**

## Summary
{data.get('summary', 'Visual survey complete.')}

## Doodles & Marginalia Inventory
| ID | Region | Type | Description | Scholarly note |
|----|--------|------|-------------|----------------|
{rows}

## Scratch & Damage Analysis
{scratches}

{damage}

## AI Assessment Hooks
- Machine-readable: `grok_doodles.json`
- Cross-ref: `scholarly_report.json`, `liturgy_comparison.md`
- Compare layers: `raw.png`, `clean_white.jpg`, `grok_clean_white.jpg`

*Grok vision pass — validate against handrit.is high-res facsimile.*
"""


def run_grok_vision(image: Path, page: int, dry_run: bool) -> dict | None:
    prompt = VISION_PROMPT.format(image_path=image, page=page)
    if dry_run:
        print(f"   [dry-run] grok vision → page {page}")
        return {
            "page": page,
            "confidence": "low",
            "items": [],
            "scratches": [],
            "damage_notes": [],
            "summary": "Dry-run placeholder",
        }

    cmd = [
        GROK_BIN,
        "-m",
        GROK_MODEL,
        "--always-approve",
        "--max-turns",
        "6",
        "-p",
        prompt,
    ]
    print(f"   👁️  Grok vision → page {page:3d} ({image.name})")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(image.parent))
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout on page {page}")
        return None

    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        print(f"   ⚠️  Grok exit {result.returncode}: {combined[:400]}")
        return None

    data = extract_json_block(combined)
    if not data:
        print(f"   ⚠️  No JSON parsed. Grok said:\n{combined[:500]}")
        return None
    return data


def update_metadata(meta_path: Path, data: dict) -> None:
    meta: dict = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["marginalia"] = {
        "grok_vision": True,
        "item_count": len(data.get("items", [])),
        "confidence": data.get("confidence", "medium"),
        "surveyed_at": data.get("surveyed_at"),
    }
    layers = list(meta.get("layers", []))
    for layer in ("grok_doodles.json", "doodles_catalog.md"):
        if layer not in layers:
            layers.append(layer)
    meta["layers"] = layers
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def survey_page(page: int, repo: Path, root: Path, skip_existing: bool, dry_run: bool) -> bool:
    page_dir = repo / "processed" / f"page_{page:03d}"
    out_json = page_dir / "grok_doodles.json"
    if skip_existing and out_json.is_file():
        print(f"⏭️  Skipping page {page:3d} (grok_doodles.json exists)")
        return True

    image = pick_source_image(page, repo, root)
    if not image:
        print(f"⚠️  No image for page {page:3d}")
        return False

    page_dir.mkdir(parents=True, exist_ok=True)
    data = run_grok_vision(image, page, dry_run)
    if not data:
        return False

    data["page"] = page
    data["source_image"] = str(image)
    data["surveyed_at"] = datetime.now(timezone.utc).isoformat()

    if not dry_run:
        out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        handrit = f"https://handrit.is/manuscript/view/is/GKS04-2365/{max(0, page - 1)}"
        (page_dir / "doodles_catalog.md").write_text(
            render_doodles_md(page, data, handrit), encoding="utf-8"
        )
        meta_path = repo / "metadata" / f"page_{page:03d}.json"
        if meta_path.is_file():
            update_metadata(meta_path, data)

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Grok vision marginalia survey")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--pages", help="e.g. 1,3,5-10")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    repo = root.parent
    pages = parse_page_list(args.pages) if args.pages or not args.all else list(range(1, TOTAL_PAGES + 1))

    if not Path(GROK_BIN).is_file():
        print(f"Grok CLI not found at {GROK_BIN}", file=sys.stderr)
        return 1

    print("Codex Regius Grok Doodles Survey")
    print(f"Grok: {GROK_BIN}")
    print(f"Pages: {len(pages)}")
    if args.dry_run:
        print("Mode: dry-run")
    print()

    ok = 0
    for page in pages:
        if survey_page(page, repo, root, args.skip_existing, args.dry_run):
            ok += 1

    print(f"\nDone: {ok}/{len(pages)} pages surveyed.")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())