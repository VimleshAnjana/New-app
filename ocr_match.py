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


def best_medicine_match(raw_name: str, cutoff: float = 0.65):
    """
    Match OCR-recognised text against the reference list.
    Returns (matched_name, confidence, is_high_confidence).
    
    Cutoff at 0.65 (up from 0.6) makes matching stricter - we'd rather
    show "could not match" than confidently pick the wrong medicine.
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
    is_high_confidence = ratio >= 0.90  # Raise bar from 0.85 to 0.90
    if ratio < 0.75:  # Raise from 0.70 to 0.75
        # Too different from anything in the trusted list to safely swap in -
        # showing a confidently WRONG real medicine name is worse than just
        # showing what OCR actually read, so keep the raw text here instead.
        return raw_name, ratio, False
    return match, round(ratio, 2), is_high_confidence


# Lines containing any of these are almost never the medicine name itself -
# they're packaging/regulatory boilerplate that sits right next to the name
# on most Indian government-supply labels.
_NON_NAME_KEYWORDS = [
    "batch", "mfg", "mfg.", "mfg date", "exp", "exp.", "exp date", "expiry",
    "quantity", "qty", "net wt", "net weight", "packing",
    "storage", "store in", "manufactured", "manufactured by", "govt", "supply",
    "not for sale", "plot no", "distt", "lic. no", "licence", "license",
    "shipper", "composition", "protected from", "keep out of reach", "caution",
    "qc", "passed", "prescription", "registered medical", "shakir", "shake well",
    "dosage", "directions", "warnings", "side effects", "directions for use",
    "box", "consignee", "district", "barmer", "rajasthan",
]
# A line that mentions the dosage form is a strong signal it IS the name.
_DOSAGE_KEYWORDS = [
    "tablet", "tablets", "tab", "tabs", "capsule", "capsules", "cap", "caps",
    "syrup", "injection", "solution", "drops", "suspension", "cream", "ointment",
    "oral", "topical", "ip", "usp", "bp", "inhaler", "spray", "gel", "powder",
]


def clean_ocr_text(raw_text: str) -> str:
    """
    Pre-process OCR output to remove junk, extra spaces, and govt boilerplate
    that clutters the text and makes name extraction harder.
    """
    # Remove obvious junk patterns (seal text, govt marks, plot addresses, etc.)
    junk_patterns = [
        r"rajasthan\s+govt\.?\s+supply[^a-z]*",
        r"not\s+for\s+sale[^a-z]*",
        r"plot\s+no\.?[^a-z]*",
        r"distt\.?[^a-z]*",
        r"\(\s*name\s+of\s+drugs?\s+etc\.?\s*\)[^a-z]*",
        r"qc\s+passed[^a-z]*",
        r"protected?\s+from\s+light[^a-z]*",
        r"keep\s+(?:out\s+)?of\s+reach[^a-z]*",
        r"composition\s*:[^a-z]*",
    ]
    text = raw_text
    for pattern in junk_patterns:
        text = re.sub(pattern, "\n", text, flags=re.I)
    
    # Collapse multiple spaces and newlines
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    
    return text.strip()


def pick_name_line(raw_text: str) -> str:
    """
    Real labels are cluttered (seal text, batch/date columns, addresses),
    so "just take the first line" often grabs the wrong thing. This looks
    for the line that actually reads like a drug name instead.
    """
    # Clean the text first
    cleaned = clean_ocr_text(raw_text)
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    if not lines:
        return ""

    # 1) An explicit "Name of the Drug" label - take what follows it.
    for line in lines:
        if re.search(r"name\s*of\s*the\s*drug", line, re.I):
            result = re.sub(r"^.*?name\s*of\s*the\s*drug[:.,]?\s*", "", line, flags=re.I)
            result = re.sub(r"^\(name\s*of\s*drugs?\s*etc\.?\)\s*", "", result, flags=re.I)
            if len(result) > 3:
                return result

    # 2) The longest line that mentions a dosage form and isn't boilerplate.
    candidates = [
        line for line in lines
        if any(k in line.lower() for k in _DOSAGE_KEYWORDS)
        and not any(k in line.lower() for k in _NON_NAME_KEYWORDS)
    ]
    if candidates:
        # Pick the longest one - usually the actual drug name line
        return max(candidates, key=len)

    # 3) Skip very short lines (likely junk) and pick first sensible line
    for line in lines:
        if (len(line) >= 5  # At least 5 chars
            and not any(k in line.lower() for k in _NON_NAME_KEYWORDS)
            and re.search(r"[A-Za-z]{3,}", line)):
            return line

    # 4) Fall back to the first non-empty line if nothing else works
    return lines[0] if lines else ""


def extract_batch_no(text: str) -> Optional[str]:
    # Batch label and value are sometimes OCR'd onto separate lines (two-column
    # layouts), and the code itself sometimes has a space in the middle
    # (e.g. "CXT 26049"), so allow an optional line break and internal spaces.
    m = re.search(
        r"Batch\s*(?:No\.?)?\s*[:\-.]?\s*\n?\s*([A-Z]{1,6}[\s\-]?\d{3,8})",
        text, re.I,
    )
    if m:
        return re.sub(r"\s+", "", m.group(1)).upper()
    m2 = re.search(r"(?:B\.?No\.?|Lot)\s*[:\-]?\s*\n?\s*([A-Z0-9]{4,10})", text, re.I)
    return m2.group(1).upper() if m2 else None


def extract_expiry(text: str) -> Optional[str]:
    # matches MM/YYYY, MM-YYYY or "Exp 08/2027" style
    m = re.search(r"(?:Exp|Expiry|EXP)\D{0,5}(\d{1,2}[/\-]\d{4})", text, re.I)
    if m:
        return m.group(1).replace("-", "/")
    m2 = re.search(r"\b(\d{1,2}/\d{4})\b", text)
    return m2.group(1) if m2 else None


def extract_quantity(text: str) -> (int, int):
    """
    Real labels use several different quantity formats:
    - "100 X 100 ml"          -> 100 (ml = volume, ignore the 100ml part, just count bottles)
    - "50 X 10ml"             -> 50 (ml = volume)
    - "20 X 50gm"             -> 20 (gm = weight)
    - "150 X 10 X 10 TABS"    -> 150*10*10 = 15000 tablets total
    - "24000 Tablets"         -> 24000 directly
    - "10 x 15"               -> 10 strips x 15 per strip (no unit given)
    Falls back to (1, 1) if nothing found -> user must fill manually.
    """
    # Liquid/weight style: the second number has a volume/weight unit (ml, gm, litre, etc),
    # NOT a count - only the first number (bottle/vial/tube count) matters.
    m = re.search(r"(\d{1,6})\s*[xX×]\s*\d{1,4}\s*(?:ml|gm|g|litre?|l)\b", text, re.I)
    if m:
        return int(m.group(1)), 1

    # Three-number multiply, e.g. "150 X 10 X 10 TABS"
    m3 = re.search(r"(\d{1,4})\s*[xX×]\s*(\d{1,4})\s*[xX×]\s*(\d{1,4})", text)
    if m3:
        total = int(m3.group(1)) * int(m3.group(2)) * int(m3.group(3))
        return total, 1

    # Two-number multiply (no units), e.g. "10 x 15"
    m2 = re.search(r"(\d{1,4})\s*[xX×]\s*(\d{1,4})\b", text)
    if m2:
        return int(m2.group(1)), int(m2.group(2))

    # A single count, e.g. "24000 Tablets" (allow up to 6 digits for bulk supply)
    m1 = re.search(r"(\d{1,6})\s*(?:tab|tabs|tablets?|cap|caps|capsules?|strips?|bottles?|vials?|tubes?)\b", text, re.I)
    if m1:
        return int(m1.group(1)), 1

    return 1, 1


def parse_ocr_text(raw_text: str) -> Dict:
    """
    Pure text -> structured-result pipeline (no image/OCR engine involved):
    match name against trusted list -> pull batch/expiry/qty -> flag
    anything low-confidence for manual verification. Used both by the
    pytesseract path below and by the Android ML Kit OCR path in main.py.
    """
    name_line = pick_name_line(raw_text)

    matched_name, confidence, high_conf = best_medicine_match(name_line)
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


def analyze_scan(image_path: str) -> Dict:
    """
    Full pipeline for the scan screen (desktop/pytesseract path):
    OCR -> parse_ocr_text(). On Android, main.py calls Google ML Kit
    directly instead and feeds the recognised text into parse_ocr_text().
    """
    try:
        raw_text = extract_text_from_image(image_path) if OCR_AVAILABLE else ""
    except Exception as e:
        print(f"OCR failed ({e}); falling back to manual entry.")
        raw_text = ""

    return parse_ocr_text(raw_text)


if __name__ == "__main__":
    print(f"Loaded {len(REFERENCE_MEDICINES)} reference medicine names.")
    # quick offline test of the matcher (no image needed)
    for test_name in ["Paracetmol 500mg", "Amoxicilin 250 mg", "Vitmin D3"]:
        match, conf, ok = best_medicine_match(test_name)
        print(f"{test_name!r:30} -> {match!r:35} conf={conf} high_confidence={ok}")
