#!/usr/bin/env python3
"""
Grok vision penmanship analysis — flow, dexterity, speed, animation sequence.

Writes processed/page_NNN/grok_penmanship.json

Usage:
  python3 grok-penmanship-script.py --pages 10 --skip-existing
  python3 grok-penmanship-script.py --all --skip-existing
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
GROK_MODEL = "grok-build"
TOTAL_PAGES = 144

PROMPT = """You are a paleographer analyzing scribal penmanship on Codex Regius (GKS 2365 4to, c. 1270).

Examine [Image #1: {image_path}] — page {page}.

Assess the main hand's copying style as if the scribe were writing live today:
- stroke flow and rhythm (continuous vs hesitant)
- hand dexterity (control, pressure consistency)
- estimated copying speed (deliberate / moderate / fast)
- penmanship quality vs exemplar fidelity
- letterforms that suggest pause, correction, or fatigue

Reply with ONLY valid JSON (no markdown):
{{
  "page": {page},
  "confidence": "high|medium|low",
  "flow_assessment": "paragraph",
  "dexterity_assessment": "paragraph",
  "speed_assessment": "deliberate|moderate|fast",
  "penmanship_grade": "excellent|good|variable|hesitant",
  "live_animation_note": "how strokes would look animated in modern calligraphy demo",
  "animation_sequence": [
    {{"order": 1, "region": "upper-left", "letter_hint": "S", "stroke_style": "bold initial downstroke"}}
  ],
  "summary": "overall penmanship paragraph"
}}
"""


def parse_pages(spec: str | None) -> list[int]:
    if not spec:
        return list(range(1, TOTAL_PAGES + 1))
    pages: set[int] = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return sorted(p for p in pages if 1 <= p <= TOTAL_PAGES)


def extract_json(text: str) -> dict | None:
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        return json.loads(text[s : e + 1])
    except json.JSONDecodeError:
        return None


def pick_image(page_dir: Path, root: Path, page: int) -> Path | None:
    for p in (
        page_dir / "grok_clean_white.jpg",
        page_dir / "clean_white.jpg",
        root / "png" / f"GKS2365_page_{page}.png",
    ):
        if p.is_file():
            return p
    return None


def analyze_page(page: int, repo: Path, root: Path, skip_existing: bool, dry_run: bool) -> bool:
    page_dir = repo / "processed" / f"page_{page:03d}"
    out = page_dir / "grok_penmanship.json"
    if skip_existing and out.is_file():
        print(f"⏭️  Page {page:3d} (grok_penmanship exists)")
        return True

    image = pick_image(page_dir, root, page)
    if not image:
        print(f"⚠️  No image page {page}")
        return False

    prompt = PROMPT.format(image_path=image, page=page)
    if dry_run:
        print(f"   [dry-run] penmanship page {page}")
        return True

    cmd = [GROK_BIN, "-m", GROK_MODEL, "--always-approve", "--max-turns", "6", "-p", prompt]
    print(f"   ✍️  Grok penmanship → page {page:3d}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(image.parent))
    except subprocess.TimeoutExpired:
        return False

    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    data = extract_json(combined)
    if not data:
        print(f"   ⚠️  No JSON: {combined[:300]}")
        return False

    data["page"] = page
    data["source_image"] = str(image)
    data["surveyed_at"] = datetime.now(timezone.utc).isoformat()
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Grok penmanship vision")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--pages")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    repo = root.parent
    pages = parse_pages(args.pages) if args.pages or not args.all else list(range(1, TOTAL_PAGES + 1))

    if not Path(GROK_BIN).is_file():
        print(f"No grok at {GROK_BIN}", file=sys.stderr)
        return 1

    ok = sum(1 for p in pages if analyze_page(p, repo, root, args.skip_existing, args.dry_run))
    print(f"\nDone: {ok}/{len(pages)}")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())