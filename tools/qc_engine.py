"""Core QC engine: preprocessing → OCR → correction → ML validation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.citations import CITATIONS, HANDRIT_BASE, MANUSCRIPT_ID, references_block
from tools.image_preprocess import preprocess_pipeline
from tools.ml_metrics import compare_layers
from tools.ocr_corrector import apply_safe_fixes, run_tesseract


class QcEngine:
    def __init__(self, repo_root: Path):
        self.repo = repo_root.resolve()
        self.processed = self.repo / "processed"
        self.metadata = self.repo / "metadata"

    def page_dir(self, page: int) -> Path:
        return self.processed / f"page_{page:03d}"

    def extract_transcription(self, page_dir: Path) -> str:
        assessment = page_dir / "ai_assessment.md"
        if not assessment.is_file():
            return ""
        text = assessment.read_text(encoding="utf-8")
        match = re.search(
            r"## Original Text.*?\n```\n(.*?)```",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        return match.group(1).strip() if match else ""

    def update_transcription(self, page_dir: Path, new_text: str) -> None:
        path = page_dir / "ai_assessment.md"
        content = path.read_text(encoding="utf-8")
        if "```" in content and "Original Text" in content:
            content = re.sub(
                r"(## Original Text[^\n]*\n```\n)(.*?)(```)",
                lambda m: m.group(1) + new_text + m.group(3),
                content,
                count=1,
                flags=re.DOTALL | re.IGNORECASE,
            )
        else:
            content += f"\n\n## Original Text (OCR)\n```\n{new_text}\n```\n"
        path.write_text(content, encoding="utf-8")

    def run_page(
        self,
        page: int,
        *,
        auto_suggest: bool = True,
        auto_apply: bool = False,
        save_previews: bool = False,
    ) -> dict:
        page_dir = self.page_dir(page)
        errors: list[str] = []

        if not page_dir.is_dir():
            return {"page": page, "status": "error", "errors": [f"Missing {page_dir}"]}

        raw = page_dir / "raw.png"
        vellum = page_dir / "artistic_vellum.jpg"
        clean = page_dir / "clean_white.jpg"
        grok_v = page_dir / "grok_artistic_vellum.jpg"
        grok_w = page_dir / "grok_clean_white.jpg"

        report: dict = {
            "page": page,
            "manuscript": MANUSCRIPT_ID,
            "handrit_url": HANDRIT_BASE,
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline_steps": [],
            "image_metrics": {},
            "ocr": {},
            "corrections": {},
            "issues": [],
            "citations": references_block(
                ["handrit_viewer", "neckel_kuhn", "tesseract_ocr", "ssim_metric"]
            ),
        }

        # Step 1: Preprocess raw for OCR
        if raw.is_file():
            try:
                preview_dir = page_dir / "qc_previews" if save_previews else None
                prep = preprocess_pipeline(raw, preview_dir)
                report["pipeline_steps"].append(
                    {"step": "preprocess", "status": "ok", "detail": prep["steps"]}
                )
                report["preprocess"] = {"skew_angle": prep["skew_angle"]}

                # Step 2: OCR
                ocr_text, ocr_err = run_tesseract(prep["ocr_input"])
                report["ocr"] = {
                    "text_preview": ocr_text[:500] if ocr_text else "",
                    "char_count": len(ocr_text),
                    "error": ocr_err,
                }
                report["pipeline_steps"].append(
                    {
                        "step": "ocr",
                        "status": "ok" if ocr_text else "warning",
                        "detail": ocr_err or "Tesseract extraction complete",
                    }
                )
            except Exception as exc:
                errors.append(f"Preprocess/OCR failed: {exc}")
                report["pipeline_steps"].append(
                    {"step": "preprocess", "status": "error", "detail": str(exc)}
                )
        else:
            errors.append(f"Missing raw image: {raw}")

        # Step 3: Compare image layers (ML metrics)
        for label, enhanced in [
            ("artistic_vellum", vellum),
            ("clean_white", clean),
            ("grok_artistic_vellum", grok_v),
            ("grok_clean_white", grok_w),
        ]:
            if raw.is_file() and enhanced.is_file():
                try:
                    report["image_metrics"][label] = compare_layers(raw, enhanced)
                except Exception as exc:
                    report["image_metrics"][label] = {"error": str(exc)}

        # Step 4: Transcription QC
        transcription = self.extract_transcription(page_dir)
        ocr_text = report.get("ocr", {}).get("text_preview", "")
        text_for_qc = transcription if transcription and "[PASTE" not in transcription else ocr_text

        if auto_suggest or auto_apply:
            result = apply_safe_fixes(text_for_qc)
            report["corrections"] = {
                "raw_text_preview": result.raw_text[:300],
                "corrected_text_preview": result.corrected_text[:300],
                "issue_count": len(result.issues),
                "applied_fixes": result.applied_fixes,
            }
            for issue in result.issues:
                entry = {
                    "severity": issue.severity,
                    "code": issue.code,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "etymology": issue.etymology,
                    "citation": CITATIONS.get(issue.citation or "", {}).get("short"),
                    "auto_fixable": issue.auto_fixable,
                }
                report["issues"].append(entry)

            if auto_apply and result.applied_fixes:
                self.update_transcription(page_dir, result.corrected_text)
                report["pipeline_steps"].append(
                    {"step": "auto_apply", "status": "ok", "detail": result.applied_fixes}
                )
            elif auto_apply and ocr_text and not transcription:
                self.update_transcription(page_dir, result.corrected_text)
                report["pipeline_steps"].append(
                    {"step": "ocr_to_assessment", "status": "ok", "detail": "Inserted OCR text"}
                )

        # Step 5: Overall status
        error_issues = [i for i in report["issues"] if i["severity"] == "error"]
        if errors or error_issues:
            report["status"] = "needs_review"
        if errors:
            report["errors"] = errors

        # Persist reports
        def _json_default(obj):
            if isinstance(obj, (np.bool_, np.integer, np.floating)):
                return obj.item()
            raise TypeError(f"Not serializable: {type(obj)}")

        (page_dir / "qc_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=_json_default) + "\n",
            encoding="utf-8",
        )
        (page_dir / "qc_report.md").write_text(self._markdown_report(report), encoding="utf-8")

        meta_path = self.metadata / f"page_{page:03d}.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["qc_status"] = report["status"]
            meta["qc_at"] = report["timestamp"]
            meta["qc_issue_count"] = len(report["issues"])
            layers = list(meta.get("layers", []))
            for f in ("qc_report.json", "qc_report.md"):
                if f not in layers:
                    layers.append(f)
            meta["layers"] = layers
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        return report

    def _markdown_report(self, report: dict) -> str:
        lines = [
            f"# QC Report — Page {report['page']}",
            "",
            f"**Status**: {report['status']}",
            f"**Manuscript**: {report['manuscript']}",
            f"**Handrit**: [{report['handrit_url']}]({report['handrit_url']})",
            f"**Generated**: {report['timestamp']}",
            "",
            "## Pipeline Steps",
        ]
        for step in report.get("pipeline_steps", []):
            lines.append(f"- **{step['step']}** ({step['status']}): {step.get('detail', '')}")

        lines.extend(["", "## Image Metrics (ML)"])
        for name, metrics in report.get("image_metrics", {}).items():
            if "error" in metrics:
                lines.append(f"- **{name}**: error — {metrics['error']}")
            else:
                lines.append(
                    f"- **{name}**: SSIM={metrics['ssim']}, "
                    f"contrast Δ={metrics['enhanced_contrast'] - metrics['raw_contrast']:.1f}"
                )

        lines.extend(["", "## Issues"])
        if not report.get("issues"):
            lines.append("- None flagged.")
        for issue in report.get("issues", []):
            lines.append(f"- [{issue['severity'].upper()}] **{issue['code']}**: {issue['message']}")
            if issue.get("suggestion"):
                lines.append(f"  - Suggestion: `{issue['suggestion']}`")
            if issue.get("etymology"):
                lines.append(f"  - Etymology: {issue['etymology']}")
            if issue.get("citation"):
                lines.append(f"  - Citation: {issue['citation']}")

        lines.extend(["", "## References"])
        for ref in report.get("citations", []):
            lines.append(f"- {ref}")

        return "\n".join(lines) + "\n"