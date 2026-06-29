#!/usr/bin/env python3
"""Zip processed layer variations in GitHub-safe chunks (default max 95 MB per file)."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# GitHub hard limit 100 MB; stay under for non-LFS pushes
MAX_CHUNK_BYTES = 95 * 1024 * 1024

EXPORT_LAYERS = [
    ("artistic_vellum", "artistic_vellum.jpg"),
    ("clean_white", "clean_white.jpg"),
    ("grok_artistic_vellum", "grok_artistic_vellum.jpg"),
    ("grok_clean_white", "grok_clean_white.jpg"),
    ("ai_assessment", "ai_assessment.md"),
]


def page_files(filename: str) -> list[tuple[int, Path]]:
    found: list[tuple[int, Path]] = []
    for n in range(1, 145):
        src = REPO / "processed" / f"page_{n:03d}" / filename
        if src.is_file():
            found.append((n, src))
    return found


def build_chunked_zips(layer_id: str, filename: str, out_dir: Path) -> list[dict]:
    pages = page_files(filename)
    if not pages:
        return []

    parts: list[dict] = []
    chunk_idx = 0
    current_pages: list[tuple[int, Path]] = []
    current_size = 0

    def flush() -> None:
        nonlocal chunk_idx, current_pages, current_size
        if not current_pages:
            return
        chunk_idx += 1
        start, end = current_pages[0][0], current_pages[-1][0]
        name = (
            f"codex_regius_{layer_id}.zip"
            if chunk_idx == 1 and len(pages) == len(current_pages)
            else f"codex_regius_{layer_id}_p{start:03d}-{end:03d}.zip"
        )
        zpath = out_dir / name
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as zf:
            for n, src in current_pages:
                zf.write(src, f"page_{n:03d}/{filename}")
        parts.append({
            "id": layer_id,
            "file": name,
            "page_start": start,
            "page_end": end,
            "pages": len(current_pages),
            "bytes": zpath.stat().st_size,
            "chunk": chunk_idx,
        })
        current_pages = []
        current_size = 0

    for n, src in pages:
        sz = src.stat().st_size
        if current_pages and current_size + sz > MAX_CHUNK_BYTES:
            flush()
        current_pages.append((n, src))
        current_size += sz

    flush()

    # Single part that fits — use simple name without page range
    if len(parts) == 1:
        old = out_dir / parts[0]["file"]
        simple = out_dir / f"codex_regius_{layer_id}.zip"
        if old != simple and old.is_file():
            if simple.is_file():
                simple.unlink()
            old.rename(simple)
            parts[0]["file"] = simple.name

    return parts


def cleanup_old_zips(out_dir: Path, layer_id: str) -> None:
    for z in out_dir.glob(f"codex_regius_{layer_id}*.zip"):
        z.unlink()


def main() -> int:
    out_dir = REPO / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus": "GKS 2365 4to",
        "max_chunk_bytes": MAX_CHUNK_BYTES,
        "note": "Large layers split into ≤95 MB parts for GitHub file limit",
        "variations": [],
    }

    for layer_id, filename in EXPORT_LAYERS:
        cleanup_old_zips(out_dir, layer_id)
        parts = build_chunked_zips(layer_id, filename, out_dir)
        if not parts:
            print(f"⏭️  {layer_id} — no files")
            continue
        total_pages = sum(p["pages"] for p in parts)
        manifest["variations"].append({
            "id": layer_id,
            "filename": filename,
            "pages_total": total_pages,
            "parts": parts,
        })
        for p in parts:
            mb = p["bytes"] / (1024 * 1024)
            flag = " ⚠️ OVER LIMIT" if p["bytes"] > 100 * 1024 * 1024 else ""
            print(f"✅ {p['file']} — pages {p['page_start']}-{p['page_end']} ({mb:.1f} MB){flag}")

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"📦 manifest → exports/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())