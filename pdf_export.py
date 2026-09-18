"""
pdf_export.py
Builds the final PDF exactly as designed:

  Line 1: Received by
  Line 2: Date                Sent by (saved name, reusable)

  Table columns: S.No | Medicine name | Batch no. | Exp date | Qty

Merge rule (mandatory): same Medicine Name + same Batch No. -> quantities
are added together into a single row. Same name but different batch stays
as a separate row. Final rows are sorted alphabetically by name.
"""

import os
from datetime import datetime
from typing import List, Dict, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def merge_medicines(rows: List[Dict]) -> List[Dict]:
    """
    rows: list of dicts with keys name, batch_no, expiry, strips, per_strip
    Same name + same batch_no -> quantities merge (sum).
    Same name + different batch_no -> stays separate.
    Returns alphabetically sorted merged rows with a computed 'qty'.
    """
    merged: Dict[Tuple[str, str], Dict] = {}

    for r in rows:
        key = (r["name"].strip().lower(), r["batch_no"].strip().lower())
        qty = int(r["strips"]) * int(r["per_strip"])

        if key not in merged:
            merged[key] = {
                "name": r["name"],
                "batch_no": r["batch_no"],
                "expiry": r.get("expiry", ""),
                "qty": 0,
            }
        merged[key]["qty"] += qty

    return sorted(merged.values(), key=lambda x: x["name"].lower())


def generate_pdf(rows: List[Dict], received_by: str, sent_by: str,
                  date_str: str = None, output_path: str = "medicine_report.pdf") -> str:
    """
    rows: raw scanned/added medicine rows (before merge)
    Produces a ready-to-share/download PDF at output_path.
    """
    if date_str is None:
        date_str = datetime.now().strftime("%d %b %Y")

    merged_rows = merge_medicines(rows)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=16 * mm, rightMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Medicine Report</b>", styles["Title"]))
    elements.append(Spacer(1, 6))

    # Line 1: Received by
    elements.append(Paragraph(f"<b>Received by:</b> {received_by or '-'}", styles["Normal"]))
    # Line 2: Date + Sent by on the same line so it fits one page
    elements.append(Paragraph(
        f"<b>Date:</b> {date_str} &nbsp;&nbsp;&nbsp;&nbsp; <b>Sent by:</b> {sent_by or '-'}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 10))

    # Table: S.No | Medicine name | Batch no. | Exp date | Qty
    table_data = [["S.No", "Medicine name", "Batch no.", "Exp date", "Qty"]]
    for i, item in enumerate(merged_rows, start=1):
        table_data.append([
            str(i), item["name"], item["batch_no"], item["expiry"], str(item["qty"])
        ])

    table = Table(table_data, colWidths=[15 * mm, 75 * mm, 30 * mm, 30 * mm, 20 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
    ]))
    elements.append(table)

    doc.build(elements)
    return output_path


if __name__ == "__main__":
    demo_rows = [
        {"name": "Amoxicillin 250mg", "batch_no": "A7734", "expiry": "11/2026", "strips": 15, "per_strip": 1},
        {"name": "Paracetamol 500mg", "batch_no": "B4021", "expiry": "08/2027", "strips": 25, "per_strip": 15},
        {"name": "Paracetamol 500mg", "batch_no": "B4021", "expiry": "08/2027", "strips": 20, "per_strip": 1},
        {"name": "Vitamin D3", "batch_no": "D9187", "expiry": "02/2028", "strips": 30, "per_strip": 1},
    ]
    path = generate_pdf(demo_rows, received_by="Store Manager", sent_by="Vimlesh Patel",
                         output_path="demo_medicine_report.pdf")
    print(f"PDF created: {os.path.abspath(path)}")
