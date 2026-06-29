#!/usr/bin/env python3
"""Zip each processed layer variation for book-style download (excludes raw.png)."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXPORT_LAYERS = [
    ("artistic_vellum", "artistic_vellum.jpg"),
    ("clean_white", "clean_white.jpg"),
    ("grok_artistic_vellum", "grok_artistic_vellum.jpg"),
    ("grok_clean_white", "grok_clean_white.jpg"),
    ("ai_assessment", "ai_assessment.md"),
]


def build_zip(layer_id: str, filename: str, out_dir: Path) -> dict:
    zpath = out_dir / f"codex_regius_{layer_id}.zip"
    included = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in range(1, 145):
            src = REPO / "processed" / f"page_{n:03d}" / filename
            if src.is_file():
                zf.write(src, f"page_{n:03d}/{filename}")
                included += 1
    return {"id": layer_id, "file": zpath.name, "pages": included, "bytes": zpath.stat().st_size}


def main() -> int:
    out_dir = REPO / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus": "GKS 2365 4to",
        "variations": [],
    }
    for layer_id, filename in EXPORT_LAYERS:
        info = build_zip(layer_id, filename, out_dir)
        manifest["variations"].append(info)
        print(f"✅ {info['file']} — {info['pages']} pages ({info['bytes'] // 1024} KB)")

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"📦 manifest → exports/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())