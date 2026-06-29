#!/usr/bin/env python3
"""
Mass Processing Script for Codex Regius (GKS 2365 4to)

Run from the GKS2365/ folder (or pass --root).

Generates the full scholarly stack for each page:
  - raw.png
  - artistic_vellum.jpg
  - clean_white.jpg
  - ai_assessment.md
  - interactive.html
  - etymology.md
  - doodles_catalog.md

Also writes metadata/manuscript.json and metadata/page_NNN.json.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageOps
except ImportError:
    print(
        "Pillow is required. Install with:\n"
        "  python3 -m venv ../.venv && ../.venv/bin/pip install pillow",
        file=sys.stderr,
    )
    sys.exit(1)

MANUSCRIPT_ID = "GKS 2365 4to"
MANUSCRIPT_TITLE = "Codex Regius of the Poetic Edda"
INSTITUTION = "Árni Magnússon Institute for Icelandic Studies, Reykjavík"
HANDRIT_BASE = "https://handrit.is/manuscript/view/is/GKS04-2365/9"
TOTAL_PAGES = 144


def page_filename(page: int) -> str:
    return f"GKS2365_page_{page}.png"


def page_dir_name(page: int) -> str:
    return f"page_{page:03d}"


def resolve_paths(root: Path) -> dict[str, Path]:
    repo_root = root.parent
    return {
        "root": root,
        "repo": repo_root,
        "png": root / "png",
        "jpg": root / "jpg",
        "processed": repo_root / "processed",
        "metadata": repo_root / "metadata",
        "ai_template": repo_root / "AI_Assessment_Template.md",
        "readalong_template": repo_root / "page-10-lyric-readalong.html",
    }


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
            start, end = int(start_s), int(end_s)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return sorted(p for p in pages if 1 <= p <= TOTAL_PAGES)


def artistic_vellum(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    gray = rgb.convert("L")
    sepia_r = gray.point(lambda x: min(255, int(x * 1.08 + 28)))
    sepia_g = gray.point(lambda x: min(255, int(x * 0.94 + 14)))
    sepia_b = gray.point(lambda x: min(255, int(x * 0.72 + 6)))
    result = Image.merge("RGB", (sepia_r, sepia_g, sepia_b))
    result = ImageEnhance.Contrast(result).enhance(1.08)
    result = ImageEnhance.Color(result).enhance(0.82)
    return result


def clean_white(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    result = ImageOps.autocontrast(rgb, cutoff=2)
    result = ImageEnhance.Brightness(result).enhance(1.18)
    result = ImageEnhance.Contrast(result).enhance(1.25)
    result = ImageEnhance.Color(result).enhance(0.25)
    return result


def load_ai_template(template_path: Path, page: int) -> str:
    if template_path.is_file():
        text = template_path.read_text(encoding="utf-8")
    else:
        text = (
            "# AI Assessment — Page {page}\n\n"
            "**Manuscript**: GKS 2365 4to\n"
            "**Image Filename**: {filename}\n\n"
            "## Original Text (Clean OCR / Transcription)\n```\n[Pending transcription]\n```\n"
        )
    filename = page_filename(page)
    text = text.replace("**Image Filename**: ", f"**Image Filename**: {filename}\n- **Page Number** (user labeling): {page}")
    text = re.sub(
        r'"page":\s*""',
        f'"page": "{page}"',
        text,
    )
    text = re.sub(
        r"- \*\*Page Number\*\* \(user labeling\): \s*",
        f"- **Page Number** (user labeling): {page}\n",
        text,
        count=1,
    )
    if f"Page {page}" not in text[:200]:
        text = f"# AI Assessment — GKS2365 Page {page}\n\n" + text
    return text


def etymology_markdown(page: int) -> str:
    return f"""# Etymology & Dialect — Page {page}

**Language**: Old West Norse (Icelandic, c. 1270–1280)
**Script tradition**: Gothic book hand with insular influences

## Dialect Notes
- Conservative retention of diphthongs typical of Icelandic transmission
- Possible Norwegian substrate from earlier oral tradition
- Spelling variants may reflect scribal normalization vs. dialect pronunciation

## Key Morphological Features
| Feature | Example | Note |
|---------|---------|------|
| u-umlaut | — | Pending line-level analysis |
| i-mutation | — | Pending line-level analysis |
| Archaic lexicon | — | Cross-ref. Neckel/Kuhn |

## Comparative Manuscripts
- AM 748 I 4to (related Eddic witness)
- Hauksbók (prose parallels)

*Auto-generated scaffold — enrich with line-level glosses during scholarly review.*
"""


def doodles_catalog_markdown(page: int) -> str:
    return f"""# Marginalia & Doodles Catalog — Page {page}

**Manuscript**: {MANUSCRIPT_ID}
**Source image**: `{page_filename(page)}`

## Inventory
| ID | Region | Type | Description | Scholarly note |
|----|--------|------|-------------|----------------|
| — | — | — | Pending visual survey | — |

## Detection Status
- Automated catalog: scaffold only
- Manual paleographic review: recommended
- Cross-reference: [handrit.is viewer]({HANDRIT_BASE})

*Populate after high-resolution marginalia survey.*
"""


def interactive_html(page: int, template_path: Path | None) -> str:
    title = f"GKS2365 Page {page} • Lyric Read-Along"
    if template_path and template_path.is_file():
        html = template_path.read_text(encoding="utf-8")
        html = html.replace("Page 10", f"Page {page}")
        html = html.replace("page 10", f"page {page}")
        return html

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Georgia, serif; background: #1c140f; color: #e8d9b0; margin: 0; padding: 20px; }}
    .container {{ max-width: 1200px; margin: auto; background: #f9f4e9; color: #3c2f1e; border-radius: 8px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }}
    .header {{ text-align: center; padding: 20px; background: #3c2f1e; color: #e8d9b0; }}
    .manuscript {{ display: flex; flex-wrap: wrap; }}
    .left, .right {{ flex: 1; padding: 30px; min-width: 320px; }}
    .line {{ cursor: pointer; padding: 6px 0; transition: all 0.3s; }}
    .line:hover, .line.active {{ background: #e8d9b0; color: #3c2f1e; }}
    button {{ padding: 12px 30px; font-size: 1.1em; background: #8b5a2b; color: white; border: none; border-radius: 4px; cursor: pointer; }}
    img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; border: 1px solid #d4c3a3; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{MANUSCRIPT_TITLE} — Page {page}</h1>
      <p>Interactive read-along scaffold • transcription pending</p>
      <button onclick="togglePlay()">▶ Play / Pause Chant</button>
    </div>
    <div class="manuscript">
      <div class="left">
        <h2>Original Old Norse</h2>
        <div id="left-text">
          <div class="line" data-time="0">[Transcription pending for page {page}]</div>
        </div>
        <img src="artistic_vellum.jpg" alt="Artistic vellum recreation page {page}">
      </div>
      <div class="right">
        <h2>Modern English + Derivatives</h2>
        <div id="right-text">
          <div class="line" data-time="0">[Translation pending for page {page}]</div>
        </div>
        <img src="clean_white.jpg" alt="Clean white analysis overlay page {page}">
      </div>
    </div>
  </div>
  <script>
    let isPlaying = false;
    let currentLine = 0;
    const lines = document.querySelectorAll('.line');
    function togglePlay() {{ isPlaying = !isPlaying; if (isPlaying) readAlong(); }}
    function readAlong() {{
      if (!isPlaying) return;
      lines.forEach(l => l.classList.remove('active'));
      if (currentLine < lines.length) {{
        lines[currentLine].classList.add('active');
        currentLine++;
        setTimeout(readAlong, 2800);
      }} else {{ isPlaying = false; currentLine = 0; }}
    }}
  </script>
</body>
</html>
"""


def page_metadata(page: int) -> dict:
    return {
        "manuscript": MANUSCRIPT_ID,
        "page": page,
        "image_filename": page_filename(page),
        "handrit_url": HANDRIT_BASE,
        "layers": [
            "raw.png",
            "artistic_vellum.jpg",
            "clean_white.jpg",
            "interactive.html",
            "ai_assessment.md",
            "etymology.md",
            "doodles_catalog.md",
        ],
        "poem": "",
        "original_text": "",
        "translation": "",
        "marginalia": None,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


def manuscript_metadata(pages: list[int]) -> dict:
    return {
        "id": MANUSCRIPT_ID,
        "title": MANUSCRIPT_TITLE,
        "institution": INSTITUTION,
        "date": "c. 1270–1280",
        "language": "Old Norse / Icelandic",
        "total_pages": TOTAL_PAGES,
        "processed_pages": pages,
        "handrit_url": HANDRIT_BASE,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def page_outputs_complete(page_dir: Path) -> bool:
    required = [
        "raw.png",
        "artistic_vellum.jpg",
        "clean_white.jpg",
        "ai_assessment.md",
        "interactive.html",
        "etymology.md",
        "doodles_catalog.md",
    ]
    return all((page_dir / name).is_file() for name in required)


def process_page(page: int, paths: dict[str, Path], skip_existing: bool, dry_run: bool) -> bool:
    png_path = paths["png"] / page_filename(page)
    if not png_path.is_file():
        print(f"⚠️  Missing source: {png_path.name}")
        return False

    page_dir = paths["processed"] / page_dir_name(page)
    if skip_existing and page_outputs_complete(page_dir):
        print(f"⏭️  Skipping page {page:3d} (already complete)")
        return True

    print(f"✅ Processing page {page:3d} — {png_path.name}")

    if dry_run:
        return True

    page_dir.mkdir(parents=True, exist_ok=True)

    raw_dest = page_dir / "raw.png"
    if not raw_dest.exists() or raw_dest.stat().st_mtime < png_path.stat().st_mtime:
        shutil.copy2(png_path, raw_dest)

    with Image.open(png_path) as img:
        vellum_path = page_dir / "artistic_vellum.jpg"
        white_path = page_dir / "clean_white.jpg"

        artistic_vellum(img).save(vellum_path, "JPEG", quality=92, optimize=True)
        clean_white(img).save(white_path, "JPEG", quality=92, optimize=True)

    (page_dir / "ai_assessment.md").write_text(
        load_ai_template(paths["ai_template"], page),
        encoding="utf-8",
    )
    (page_dir / "etymology.md").write_text(etymology_markdown(page), encoding="utf-8")
    (page_dir / "doodles_catalog.md").write_text(doodles_catalog_markdown(page), encoding="utf-8")
    (page_dir / "interactive.html").write_text(
        interactive_html(page, paths["readalong_template"]),
        encoding="utf-8",
    )

    meta_dir = paths["metadata"]
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / f"page_{page:03d}.json").write_text(
        json.dumps(page_metadata(page), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex Regius mass processor")
    parser.add_argument(
        "source_url",
        nargs="?",
        help="Optional reference URL for the script (informational only)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="GKS2365 folder containing png/ and jpg/",
    )
    parser.add_argument("--pages", help="Page list, e.g. 1,2,10-15")
    parser.add_argument("--skip-existing", action="store_true", help="Skip fully processed pages")
    parser.add_argument("--dry-run", action="store_true", help="List work without writing files")
    parser.add_argument("--qc", action="store_true", help="Run QC pipeline after each page")
    parser.add_argument("--qc-auto-apply", action="store_true", help="Auto-apply safe OCR fixes during QC")
    parser.add_argument("--scholarly", action="store_true", help="Generate full scholarly assessment stack per page")
    args = parser.parse_args()

    paths = resolve_paths(args.root.resolve())
    pages = parse_page_list(args.pages)

    print("Codex Regius Mass Processor — Full Scholarly Stack")
    print(f"Root: {paths['root']}")
    print(f"Output: {paths['processed']}")
    print(
        "Layers: raw, artistic_vellum, clean_white, interactive, "
        "ai_assessment, etymology, doodles_catalog"
    )
    if args.source_url:
        print(f"Reference: {args.source_url}")
    print(f"Pages: {len(pages)} ({pages[0]}–{pages[-1]})")
    if args.dry_run:
        print("Mode: dry-run")
    print()

    if not paths["png"].is_dir():
        print(f"Error: png folder not found at {paths['png']}", file=sys.stderr)
        return 1

    scholarly_engine = None
    if args.scholarly and not args.dry_run:
        sys.path.insert(0, str(paths["repo"]))
        from tools.scholarly_assessment import ScholarlyAssessmentEngine

        scholarly_engine = ScholarlyAssessmentEngine(paths["repo"])

    qc_engine = None
    if args.qc and not args.dry_run:
        sys.path.insert(0, str(paths["repo"]))
        from tools.qc_engine import QcEngine

        qc_engine = QcEngine(paths["repo"])

    ok = 0
    for page in pages:
        if process_page(page, paths, args.skip_existing, args.dry_run):
            ok += 1
            if scholarly_engine:
                scholarly_engine.run_page(page)
                print(f"   📜 Scholarly assessment page {page:3d}")
            if qc_engine:
                report = qc_engine.run_page(page, auto_apply=args.qc_auto_apply)
                status = report.get("status", "?")
                print(f"   🔍 QC page {page:3d}: {status}")

    if not args.dry_run:
        paths["metadata"].mkdir(parents=True, exist_ok=True)
        (paths["metadata"] / "manuscript.json").write_text(
            json.dumps(manuscript_metadata(pages), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print()
    print(f"Done: {ok}/{len(pages)} pages processed.")
    if not args.dry_run:
        print(f"Processed output: {paths['processed']}")
        print(f"Metadata: {paths['metadata']}")
        print("Push processed/ and metadata/ to the repo when ready.")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())