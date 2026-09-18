# Medicine Scanner (by Vimlesh Patel)

Android app jo medicine strip/box scan karke naam, batch no., expiry date,
aur quantity automatically detect karta hai — aur ek trusted medicine list
(Essential Medicines List) ke against match karke wrong detection se bachata hai.

## Features
- **Splash screen** — app intro
- **Home screen** — scanned/added medicines ki list, har card par Edit + Delete
- **Add manually / Edit** — Medicine name, Batch no., Expiry date, Quantity
  edit karo, ya galat entry delete karo
- **Scan screen** — camera se photo lo, OCR text nikaale, aur `data/edl_medicines.txt`
  (Essential Medicines List se banayi gayi trusted list) ke against fuzzy-match
  karke sirf high-confidence naam accept karta hai. Low-confidence field
  "verify" ke liye flag ho jaata hai.
- **Reports** — pichle 30 din ke generate kiye gaye PDF gallery jaisa
- **PDF export** —
  - Line 1: Received by
  - Line 2 (ek line me): Date + Sent by (saved names list se, "+ Add new name" option ke saath)
  - Table: S.No | Medicine name | Batch no. | Exp date | Qty
  - Same medicine name + same batch no. → quantity auto-merge (jodi jaati hai)
  - Alphabetically sorted
  - Download aur Share dono options

## Files
| File | Kaam |
|---|---|
| `main.py` | Kivy app — saare screens aur unki logic |
| `database.py` | SQLite storage (add/edit/delete/list medicines) |
| `ocr_match.py` | OCR + trusted-list fuzzy matching (accuracy ke liye) |
| `pdf_export.py` | Merge logic + PDF banana (reportlab) |
| `names_store.py` | "Sent by" saved names list (JSON file) |
| `data/edl_medicines.txt` | Trusted medicine names database (aapki di gayi EDL list se) |
| `buildozer.spec` | Android APK build ke liye config |

## Desktop par test karne ke liye
```bash
pip install -r requirements.txt
python main.py
```

## Android APK banane ke liye (Linux/WSL par)
```bash
pip install buildozer cython
buildozer -v android debug
```
APK `bin/` folder me banega. Pehli baar build karne me Android SDK/NDK
download hone ki wajah se time lagega.

## Note
- `ocr_match.py` ko real camera photo ke liye Tesseract OCR chahiye
  (`pytesseract` + system me `tesseract-ocr` installed hona chahiye).
- Agar OCR available nahi hai, app demo data se scan flow simulate kar deta
  hai taaki poori app phir bhi test ho sake.
- Medicine name matching sirf `data/edl_medicines.txt` list se hoti hai —
  is file me apni poori/updated medicine list daal sakte ho, jitni badi
  aur saaf list utni behtar accuracy.
