#!/usr/bin/env python3
"""
Grok-enhanced processing for Codex Regius pages 10+.

Uses the Grok CLI image_edit tool to produce scholarly artistic layers
beyond the local Pillow filters in mass-process-script.py.

Outputs per page (in processed/page_NNN/):
  - grok_artistic_vellum.jpg
  - grok_clean_white.jpg
  - grok_variations/   (optional multi-pass outputs)

Page 10 also syncs pre-existing samples from GKS2365/grok/.
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
DEFAULT_MIN_PAGE = 10
TOTAL_PAGES = 144

PROMPTS = {
    "artistic_vellum": (
        "Transform this Codex Regius manuscript page (GKS 2365 4to, c. 1270 Iceland) "
        "into an artistic vellum recreation: warm aged parchment tone, subtle fiber "
        "texture, iron-gall ink preserved exactly, marginalia intact, scholarly museum "
        "quality. Keep all text legible and layout unchanged."
    ),
    "clean_white": (
        "Transform this Codex Regius manuscript scan into a clean white scholarly "
        "analysis overlay: high contrast, neutral white background, crisp iron-gall "
        "letterforms, minimal yellowing, optimized for paleographic study. Preserve "
        "every character and marginal mark; no cropping."
    ),
}


def page_filename(page: int) -> str:
    return f"GKS2365_page_{page}.png"


def page_dir_name(page: int) -> str:
    return f"page_{page:03d}"


def parse_page_list(spec: str | None, min_page: int) -> list[int]:
    if spec:
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
        return sorted(p for p in pages if min_page <= p <= TOTAL_PAGES)
    return list(range(min_page, TOTAL_PAGES + 1))


def extract_saved_path(output: str) -> Path | None:
    candidates = re.findall(r"(/[^\s\"']+\.(?:jpg|jpeg|png|webp))", output, flags=re.IGNORECASE)
    for raw in reversed(candidates):
        path = Path(raw.rstrip(".,;:)"))
        if path.is_file():
            return path
    return None


def run_grok_edit(source: Path, prompt: str, dest: Path, dry_run: bool) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        return True

    if dry_run:
        print(f"   [dry-run] grok image_edit → {dest.name}")
        return True

    cmd = [
        GROK_BIN,
        "--always-approve",
        "-p",
        (
            f"Use image_edit exactly once.\n"
            f"Source image: {source}\n"
            f"Prompt: {prompt}\n"
            f"After editing, copy or save the result to: {dest}\n"
            f"Reply with ONLY the final absolute path of the saved file."
        ),
    ]

    print(f"   🤖 Grok image_edit → {dest.name}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(source.parent),
        )
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout editing {source.name}")
        return False

    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        print(f"   ⚠️  Grok exit {result.returncode}: {combined[:300]}")
        return False

    if dest.is_file():
        return True

    saved = extract_saved_path(combined)
    if saved and saved != dest:
        shutil.copy2(saved, dest)
        return True

    print(f"   ⚠️  No output file found. Grok said:\n{combined[:400]}")
    return False


def sync_page10_grok_samples(grok_src: Path, page_dir: Path, dry_run: bool) -> int:
    if not grok_src.is_dir():
        return 0
    variations = page_dir / "grok_variations"
    if dry_run:
        count = len(list(grok_src.glob("*.jpg")))
        print(f"   [dry-run] sync {count} grok samples → grok_variations/")
        return count

    variations.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in sorted(grok_src.glob("*.jpg")):
        dest = variations / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
            copied += 1
    return copied


def patch_interactive_html(page_dir: Path) -> None:
    html_path = page_dir / "interactive.html"
    if not html_path.is_file():
        return
    html = html_path.read_text(encoding="utf-8")
    if "grok_artistic_vellum.jpg" in html:
        return
    gallery = ""
    if (page_dir / "grok_variations").is_dir():
        imgs = sorted((page_dir / "grok_variations").glob("*.jpg"))
        if imgs:
            gallery = "\n    <div class=\"references\">\n"
            for img in imgs[:6]:
                gallery += f'      <img src="grok_variations/{img.name}" alt="Grok variation" style="max-height:180px">\n'
            gallery += "    </div>\n"
    grok_imgs = (
        '\n        <img src="grok_artistic_vellum.jpg" alt="Grok artistic vellum" style="max-width:100%;margin-top:20px">\n'
        if (page_dir / "grok_artistic_vellum.jpg").is_file()
        else ""
    )
    grok_white = (
        '\n        <img src="grok_clean_white.jpg" alt="Grok clean white overlay" style="max-width:100%;margin-top:20px">\n'
        if (page_dir / "grok_clean_white.jpg").is_file()
        else ""
    )
    if grok_imgs and "</div>" in html:
        html = html.replace(
            "<!-- more lines -->\n        </div>",
            f"<!-- more lines -->{grok_imgs}        </div>",
            1,
        )
    if grok_white and "<!-- more lines -->" in html:
        parts = html.split("<!-- more lines -->", 2)
        if len(parts) >= 3:
            html = parts[0] + "<!-- more lines -->" + grok_white + parts[1] + "<!-- more lines -->" + parts[2]
    if gallery and "<div class=\"references\">" not in html:
        html = html.replace("</div>\n  </div>\n\n  <script>", f"</div>{gallery}  </div>\n\n  <script>")
    elif gallery and "<!-- Your three bottom images" in html:
        html = html.replace(
            "<div class=\"references\">\n      <!-- Your three bottom images here as img tags with local or base64 paths -->\n    </div>",
            gallery.strip(),
        )
    html_path.write_text(html, encoding="utf-8")


def update_page_metadata(meta_path: Path, page: int, grok_layers: list[str]) -> None:
    data: dict = {}
    if meta_path.is_file():
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    layers = list(data.get("layers", []))
    for layer in grok_layers:
        if layer not in layers:
            layers.append(layer)
    data["layers"] = layers
    data["grok_enhanced"] = True
    data["grok_enhanced_at"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def grok_outputs_complete(page_dir: Path) -> bool:
    return (
        (page_dir / "grok_artistic_vellum.jpg").is_file()
        and (page_dir / "grok_clean_white.jpg").is_file()
    )


def enhance_page(
    page: int,
    root: Path,
    repo: Path,
    skip_existing: bool,
    dry_run: bool,
    sync_samples: bool,
) -> bool:
    png_path = root / "png" / page_filename(page)
    page_dir = repo / "processed" / page_dir_name(page)
    meta_path = repo / "metadata" / f"page_{page:03d}.json"

    if not png_path.is_file():
        print(f"⚠️  Missing source: {png_path}")
        return False

    if skip_existing and grok_outputs_complete(page_dir):
        print(f"⏭️  Skipping page {page:3d} (grok layers complete)")
        return True

    print(f"✨ Grok enhance page {page:3d} — {png_path.name}")

    if page == 10 and sync_samples:
        n = sync_page10_grok_samples(root / "grok", page_dir, dry_run)
        if n:
            print(f"   📎 Synced {n} existing grok variation(s)")

    ok_vellum = run_grok_edit(
        png_path,
        PROMPTS["artistic_vellum"],
        page_dir / "grok_artistic_vellum.jpg",
        dry_run,
    )
    ok_white = run_grok_edit(
        png_path,
        PROMPTS["clean_white"],
        page_dir / "grok_clean_white.jpg",
        dry_run,
    )

    if not dry_run and (ok_vellum or ok_white):
        grok_layers = []
        if ok_vellum:
            grok_layers.append("grok_artistic_vellum.jpg")
        if ok_white:
            grok_layers.append("grok_clean_white.jpg")
        if (page_dir / "grok_variations").is_dir():
            grok_layers.append("grok_variations/")
        if meta_path.is_file():
            update_page_metadata(meta_path, page, grok_layers)
        patch_interactive_html(page_dir)

    return ok_vellum and ok_white


def main() -> int:
    parser = argparse.ArgumentParser(description="Grok-enhanced Codex Regius processor (page 10+)")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--pages", help="Page list, e.g. 10,11,15-20")
    parser.add_argument("--min-page", type=int, default=DEFAULT_MIN_PAGE)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-sync-samples", action="store_true", help="Skip grok/ sample import on page 10")
    args = parser.parse_args()

    root = args.root.resolve()
    repo = root.parent
    pages = parse_page_list(args.pages, args.min_page)

    if not pages:
        print("No pages in range.", file=sys.stderr)
        return 1

    if not Path(GROK_BIN).is_file():
        print(f"Grok CLI not found at {GROK_BIN}", file=sys.stderr)
        return 1

    print("Codex Regius Grok Enhancer — page 10+")
    print(f"Grok: {GROK_BIN}")
    print(f"Pages: {len(pages)} ({pages[0]}–{pages[-1]})")
    if args.dry_run:
        print("Mode: dry-run")
    print()

    ok = 0
    for page in pages:
        if enhance_page(
            page,
            root,
            repo,
            args.skip_existing,
            args.dry_run,
            sync_samples=not args.no_sync_samples,
        ):
            ok += 1

    print()
    print(f"Done: {ok}/{len(pages)} pages grok-enhanced.")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())