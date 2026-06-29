"""Old Norse / Icelandic OCR correction with etymology hints and citations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Common OCR confusions in Gothic book hand / Tesseract on vellum
CHAR_REPLACEMENTS = {
    "þ": ["th", "p", "b", "f"],
    "ð": ["d", "o", "0", "6"],
    "æ": ["ae", "a", "oe"],
    "ö": ["o", "oe", "oo"],
    "á": ["a", "á", "a'"],
    "í": ["i", "l", "1"],
    "ú": ["u", "n", "ii"],
    "ó": ["o", "0", "6"],
    "é": ["e", "c"],
    "ǫ": ["o", "a", "q"],
    "ꝩ": ["w", "v", "u"],
}

# Word-level safe auto-corrections (attested Eddic forms)
SAFE_WORD_FIXES = {
    "hlioos": "Hlióðs",
    "hlioðs": "Hlióðs",
    "hliods": "Hlióðs",
    "bið": "bið",
    "bid": "bið",
    "ek": "ek",
    "allar": "allar",
    "helgar": "helgar",
    "kindir": "kindir",
    "vǫluspá": "Völuspá",
    "voluspa": "Völuspá",
    "völuspá": "Völuspá",
}

ETYMOLOGY_HINTS = {
    "Hlióðs": "From *hljóð* 'hearing, silence' — opening formula of Völuspá (cf. Neckel/Kuhn st. 1).",
    "helgar": "Adj. 'holy, sacred' < *heilagaz; conservative West Norse spelling.",
    "kindir": "Kin, kindred — plural of *kyn*, mythological audiences of the seeress.",
    "bið": "Verb 'ask, bid' — formulaic request for hearing in Eddic openings.",
}


@dataclass
class OcrIssue:
    severity: str  # error | warning | info
    code: str
    message: str
    suggestion: str | None = None
    etymology: str | None = None
    citation: str | None = None
    auto_fixable: bool = False


@dataclass
class CorrectionResult:
    raw_text: str
    corrected_text: str
    issues: list[OcrIssue] = field(default_factory=list)
    applied_fixes: list[str] = field(default_factory=list)


def detect_placeholder(text: str) -> list[OcrIssue]:
    issues = []
    if not text.strip() or "[PASTE" in text or "[Pending" in text or "[Transcription pending" in text:
        issues.append(
            OcrIssue(
                severity="error",
                code="PLACEHOLDER_TEXT",
                message="Transcription block is still a template placeholder.",
                suggestion="Run OCR on preprocessed raw image and review against handrit.is.",
                citation="handrit_viewer",
            )
        )
    return issues


def detect_garbled_lines(text: str) -> list[OcrIssue]:
    issues = []
    for i, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if re.search(r"[^\w\sþðæöáíúóéǫꝩ.,;:!?'\-—\[\]()/0-9]", line, re.UNICODE):
            issues.append(
                OcrIssue(
                    severity="warning",
                    code="UNUSUAL_CHARS",
                    message=f"Line {i}: unusual characters detected.",
                    suggestion="Compare glyph-by-glyph with raw scan.",
                )
            )
        if len(line) > 5 and sum(c.isdigit() for c in line) / len(line) > 0.25:
            issues.append(
                OcrIssue(
                    severity="error",
                    code="DIGIT_NOISE",
                    message=f"Line {i}: high digit ratio — likely OCR noise.",
                    suggestion="Re-run preprocessing with deskew; verify iron-gall letterforms.",
                )
            )
    return issues


def suggest_word_corrections(text: str) -> list[OcrIssue]:
    issues = []
    tokens = re.findall(r"\b[\wþðæöáíúóéǫꝩ]+\b", text, re.UNICODE)
    for token in tokens:
        lower = token.lower()
        if lower in SAFE_WORD_FIXES and token != SAFE_WORD_FIXES[lower]:
            fixed = SAFE_WORD_FIXES[lower]
            issues.append(
                OcrIssue(
                    severity="warning",
                    code="WORD_NORMALIZATION",
                    message=f"'{token}' → '{fixed}'",
                    suggestion=fixed,
                    etymology=ETYMOLOGY_HINTS.get(fixed),
                    citation="neckel_kuhn",
                    auto_fixable=True,
                )
            )
    return issues


def apply_safe_fixes(text: str) -> CorrectionResult:
    issues = (
        detect_placeholder(text)
        + detect_garbled_lines(text)
        + suggest_word_corrections(text)
    )
    corrected = text
    applied: list[str] = []
    for issue in issues:
        if issue.auto_fixable and issue.suggestion:
            pattern = re.compile(re.escape(issue.message.split("'")[1]), re.IGNORECASE)
            new = pattern.sub(issue.suggestion, corrected, count=1)
            if new != corrected:
                corrected = new
                applied.append(issue.message)
    return CorrectionResult(
        raw_text=text,
        corrected_text=corrected,
        issues=issues,
        applied_fixes=applied,
    )


def run_tesseract(ocr_input, lang: str = "isl+nor+eng") -> tuple[str, str | None]:
    """Run Tesseract; returns (text, error)."""
    try:
        import pytesseract
    except ImportError:
        return "", "pytesseract not installed"

    try:
        config = "--psm 6 -c preserve_interword_spaces=1"
        text = pytesseract.image_to_string(ocr_input, lang=lang, config=config)
        return text.strip(), None
    except Exception as exc:
        try:
            text = pytesseract.image_to_string(ocr_input, lang="eng", config="--psm 6")
            return text.strip(), f"Fallback to eng OCR: {exc}"
        except Exception as exc2:
            return "", str(exc2)