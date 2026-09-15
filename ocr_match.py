"""
ocr_match.py
Scan-screen "brain": extract text from a photo of a medicine strip / box,
then match it against the known medicine reference list (data/edl_medicines.txt)
so that the app never silently accepts a wrongly recognised name.

Also pulls out batch no., expiry date and quantity with simple regex,
each with a confidence flag so the UI can show "verify" like we designed.
"""

import os
import re
import difflib
from typing import Dict, List, Optional

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

REFERENCE_LIST_PATH = os.path.join(os.path.dirname(__file__), "data", "edl_medicines.txt")


def load_reference_medicines() -> List[str]:
    """Load the trusted medicine-name database (from the Essential Medicines List)."""
    if not os.path.exists(REFERENCE_LIST_PATH):
        return []
    with open(REFERENCE_LIST_PATH, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


REFERENCE_MEDICINES = load_reference_medicines()


def extract_text_from_image(image_path: str) -> str:
    """Run OCR on the captured photo. Returns raw recognised text."""
    if not OCR_AVAILABLE:
        raise RuntimeError(
            "pytesseract/Pillow not installed. Run: pip install pytesseract pillow"
        )
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


def best_medicine_match(raw_name: str, cutoff: float = 0.6):
    """
    Match OCR-recognised text against the reference list.
    Returns (matched_name, confidence, is_high_confidence).
    This is what stops the app from accepting a name it can't
    recognise properly.
    """
    if not raw_name:
        return None, 0.0, False

    candidates = difflib.get_close_matches(
        raw_name, REFERENCE_MEDICINES, n=1, cutoff=cutoff
    )
    if not candidates:
        return raw_name, 0.0, False  # nothing close enough in the trusted list

    match = candidates[0]
    ratio = difflib.SequenceMatcher(None, raw_name.lower(), match.lower()).ratio()
    is_high_confidence = ratio >= 0.85
    return match, round(ratio, 2), is_high_confidence


def extract_batch_no(text: str) -> Optional[str]:
    m = re.search(r"(?:Batch|B\.?No\.?|Lot)\s*[:\-]?\s*([A-Z0-9]{4,10})", text, re.I)
    return m.group(1).upper() if m else None


def extract_expiry(text: str) -> Optional[str]:
    # matches MM/YYYY, MM-YYYY or "Exp 08/2027" style
    m = re.search(r"(?:Exp|Expiry|EXP)\D{0,5}(\d{1,2}[/\-]\d{4})", text, re.I)
    if m:
        return m.group(1).replace("-", "/")
    m2 = re.search(r"\b(\d{1,2}/\d{4})\b", text)
    return m2.group(1) if m2 else None


def extract_quantity(text: str) -> (int, int):
    """
    Looks for patterns like '10 x 15' (strips x tablets per strip).
    Falls back to (1, 1) if nothing found -> user must fill manually.
    """
    m = re.search(r"(\d{1,4})\s*[xX×]\s*(\d{1,4})", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m2 = re.search(r"(\d{1,4})\s*(?:tab|tabs|cap|caps|strips?)\b", text, re.I)
    if m2:
        return int(m2.group(1)), 1
    return 1, 1


def analyze_scan(image_path: str) -> Dict:
    """
    Full pipeline for the scan screen:
    OCR -> match name against trusted list -> pull batch/expiry/qty ->
    flag anything low-confidence for manual verification.
    """
    try:
        raw_text = extract_text_from_image(image_path) if OCR_AVAILABLE else ""
    except Exception as e:
        # The tesseract OCR *engine* isn't bundled in the Android build
        # (pytesseract is just a wrapper around it), so on-device OCR
        # currently isn't available. Fail gracefully instead of crashing -
        # the user can still fill in the details by hand.
        print(f"OCR failed ({e}); falling back to manual entry.")
        raw_text = ""

    # crude heuristic: first non-empty line is usually the medicine name
    first_line = next((l.strip() for l in raw_text.splitlines() if l.strip()), "")

    matched_name, confidence, high_conf = best_medicine_match(first_line)
    batch_no = extract_batch_no(raw_text)
    expiry = extract_expiry(raw_text)
    strips, per_strip = extract_quantity(raw_text)

    return {
        "name": matched_name or "(please enter name)",
        "name_confidence": confidence,
        "name_needs_review": not high_conf,
        "batch_no": batch_no or "",
        "batch_needs_review": batch_no is None,
        "expiry": expiry or "",
        "expiry_needs_review": expiry is None,
        "strips": strips,
        "per_strip": per_strip,
        "qty_needs_review": (strips, per_strip) == (1, 1),
        "raw_text": raw_text,
    }


if __name__ == "__main__":
    print(f"Loaded {len(REFERENCE_MEDICINES)} reference medicine names.")
    # quick offline test of the matcher (no image needed)
    for test_name in ["Paracetmol 500mg", "Amoxicilin 250 mg", "Vitmin D3"]:
        match, conf, ok = best_medicine_match(test_name)
        print(f"{test_name!r:30} -> {match!r:35} conf={conf} high_confidence={ok}")
