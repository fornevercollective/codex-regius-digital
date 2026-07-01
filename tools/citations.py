"""Scholarly citations and reference URLs for QC reports."""

from __future__ import annotations

MANUSCRIPT_ID = "GKS 2365 4to"
HANDRIT_BASE = "https://handrit.is/manuscript/view/is/GKS04-2365/9"

CITATIONS = {
    "neckel_kuhn": {
        "short": "Neckel & Kuhn 1983",
        "full": "Gustav Neckel and Hans Kuhn, *Edda: Die Lieder des Codex Regius*, 2 vols., Heidelberg: Carl Winter, 1983.",
        "url": "https://archive.org/details/edda00neck",
    },
    "jonsson_1932": {
        "short": "Jónsson 1932",
        "full": "Finnur Jónsson, *De gamle Eddadigte*, København: G.E.C. Gad, 1932.",
        "url": None,
    },
    "ami_institute": {
        "short": "Árni Magnússon Institute",
        "full": "Stofnun Árna Magnússonar í íslenskum fræðum, Reykjavík.",
        "url": "https://arnastofnun.is/",
    },
    "handrit_viewer": {
        "short": "handrit.is",
        "full": "Digital manuscript viewer for GKS 2365 4to.",
        "url": HANDRIT_BASE,
    },
    "codex_regius_digital": {
        "short": "Codex Regius Digital",
        "full": "fornevercollective/codex-regius-digital scholarly edition pipeline.",
        "url": "https://github.com/fornevercollective/codex-regius-digital",
    },
    "tesseract_ocr": {
        "short": "Tesseract OCR",
        "full": "Smith, R. (2007). An Overview of the Tesseract OCR Engine. *ICDAR*.",
        "url": "https://github.com/tesseract-ocr/tesseract",
    },
    "ssim_metric": {
        "short": "SSIM",
        "full": "Wang, Zhou, et al. (2004). Image quality assessment: from error visibility to structural similarity. *IEEE TIP*.",
        "url": "https://doi.org/10.1109/TIP.2003.819861",
    },
    "calatroni_inpaint": {
        "short": "Calatroni et al. 2018",
        "full": "Calatroni, L. et al. Unveiling the invisible: mathematical methods for restoring and interpreting illuminated manuscripts. *Heritage Science* 6:56.",
        "url": "https://doi.org/10.1186/s40494-018-0216-z",
    },
}


def format_reference(key: str) -> str:
    cite = CITATIONS[key]
    ref = f"{cite['short']}: {cite['full']}"
    if cite.get("url"):
        ref += f" <{cite['url']}>"
    return ref


def references_block(keys: list[str]) -> list[str]:
    return [format_reference(k) for k in keys]