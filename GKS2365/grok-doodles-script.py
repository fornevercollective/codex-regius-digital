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
MAX_VISION_EDGE = 1568

DOODLES_JSON_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "page": {"type": "integer"},
        "confidence": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "region": {"type": "string"},
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                    "scholarly_note": {"type": "string"},
                },
                "required": ["id", "region", "type", "description"],
            },
        },
        "scratches": {"type": "array", "items": {"type": "string"}},
        "damage_notes": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["page", "confidence", "items", "summary"],
})

VISION_PROMPT = """Paleographer survey: Codex Regius (GKS 2365 4to) page {page}.

Image: [Image #1: {image_path}]

List marginalia, doodles, pen trials, stains, scratches, corrections, and damage on this folio.
Return JSON only — no prose, no tool use."""


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


def parse_grok_payload(combined: str) -> dict | None:
    data = extract_json_block(combined)
    if data and "page" in data:
        return data
    try:
        payload = json.loads(combined.strip())
    except json.JSONDecodeError:
        return data
    if not isinstance(payload, dict):
        return data
    structured = payload.get("structuredOutput")
    if isinstance(structured, dict) and "page" in structured:
        return structured
    text = payload.get("text")
    if isinstance(text, str) and text.strip():
        inner = extract_json_block(text)
        if inner and "page" in inner:
            return inner
        try:
            inner = json.loads(text)
            if isinstance(inner, dict):
                return inner
        except json.JSONDecodeError:
            pass
    for key in ("response", "result"):
        candidate = payload.get(key)
        if isinstance(candidate, dict) and "page" in candidate:
            return candidate
    return data


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


def grok_clean_unreliable(page_dir: Path) -> bool:
    """Skip grok_clean_white when QC shows it diverged from the scan."""
    qc_path = page_dir / "qc_report.json"
    if not qc_path.is_file():
        return False
    try:
        metrics = json.loads(qc_path.read_text(encoding="utf-8")).get("image_metrics", {})
        grok = metrics.get("grok_clean_white", {})
        return grok.get("ssim_ok") is False or (grok.get("ssim") or 1) < 0.45
    except (json.JSONDecodeError, OSError):
        return False


def pick_source_image(page: int, repo: Path, root: Path, prefer_raw: bool = False) -> Path | None:
    page_dir = repo / "processed" / f"page_{page:03d}"
    skip_grok = prefer_raw or grok_clean_unreliable(page_dir)
    candidates: list[Path] = []
    if not skip_grok:
        candidates.append(page_dir / "grok_clean_white.jpg")
    candidates.extend([
        page_dir / "clean_white.jpg",
        page_dir / "raw.png",
        root / "png" / f"GKS2365_page_{page}.png",
        root / "jpg" / f"GKS2365_page_{page}.jpg",
    ])
    for candidate in candidates:
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


def image_long_edge(path: Path) -> int:
    try:
        out = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        dims = [int(line.split()[-1]) for line in out.stdout.splitlines() if "pixel" in line]
        return max(dims) if dims else 0
    except (subprocess.CalledProcessError, ValueError):
        return 0


def prepare_vision_image(image: Path) -> Path:
    """Downscale large scans so Grok does not exhaust turns on compression."""
    edge = image_long_edge(image)
    if edge <= MAX_VISION_EDGE and image.suffix.lower() in {".jpg", ".jpeg"}:
        return image
    out = image.parent / f"_grok_vision_{image.stem}.jpg"
    subprocess.run(
        ["sips", "-Z", str(MAX_VISION_EDGE), "-s", "format", "jpeg", str(image), "--out", str(out)],
        check=True,
        capture_output=True,
    )
    return out


def run_grok_vision(image: Path, page: int, dry_run: bool) -> dict | None:
    try:
        vision_image = prepare_vision_image(image)
    except subprocess.CalledProcessError as exc:
        print(f"   ⚠️  Image prep failed on page {page}: {exc.stderr.decode()[:200]}")
        vision_image = image

    prompt = VISION_PROMPT.format(image_path=vision_image, page=page)
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
        "--no-subagents",
        "--max-turns",
        "1",
        "--output-format",
        "json",
        "--json-schema",
        DOODLES_JSON_SCHEMA,
        "--disallowed-tools",
        "run_terminal_cmd,web_search,web_fetch,search_replace,Write,Edit,Grep,list_dir,Agent,Task",
        "-p",
        prompt,
    ]
    label = vision_image.name if vision_image != image else image.name
    print(f"   👁️  Grok vision → page {page:3d} ({label})")

    combined = ""
    for attempt in range(1, 4):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(image.parent))
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Timeout on page {page} (attempt {attempt})")
            continue
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        if result.returncode == 0 and "Cancelled" not in combined:
            break
        print(f"   ⚠️  Grok attempt {attempt} failed on page {page}: {combined[:200]}")
    else:
        return None

    data = parse_grok_payload(combined)
    if not data or not isinstance(data, dict) or "page" not in data:
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


def survey_page(
    page: int, repo: Path, root: Path, skip_existing: bool, dry_run: bool, prefer_raw: bool = False
) -> bool:
    page_dir = repo / "processed" / f"page_{page:03d}"
    out_json = page_dir / "grok_doodles.json"
    if skip_existing and out_json.is_file():
        print(f"⏭️  Skipping page {page:3d} (grok_doodles.json exists)")
        return True

    image = pick_source_image(page, repo, root, prefer_raw=prefer_raw)
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
    parser.add_argument("--prefer-raw", action="store_true", help="Use raw.png over enhanced layers")
    parser.add_argument("--force", action="store_true", help="Re-survey even if grok_doodles.json exists")
    parser.add_argument("--retries", type=int, default=3, help="Grok attempts per page (default 3)")
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

    skip_existing = args.skip_existing and not args.force
    ok = 0
    for page in pages:
        if survey_page(page, repo, root, skip_existing, args.dry_run, args.prefer_raw):
            ok += 1

    print(f"\nDone: {ok}/{len(pages)} pages surveyed.")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())