from decimal import Decimal

CURRENCY = "OMR"
DECIMALS = 3          # OMR uses 3 decimals. Set to 2 for 1,330.75 style.

STATUS_TONE = {
    "approved": "good",
    "sent": "fair",
    "rejected": "poor",
    "expired": "poor",
}


# ---------------------------- small helpers ----------------------------
def _money(value):
    return f"{float(value or 0):,.{DECIMALS}f}"


def _num(value):
    """2.00 -> '2', 1.50 -> '1.5'"""
    text = f"{float(value or 0):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _date(value):
    return value.strftime("%d %b %Y") if value else ""


def _sl(n):
    return f"{n:02d}"


def _qty(item):
    text = _num(item.quantity)
    unit = (item.unit or "").strip()
    if unit and unit.lower() not in ("pcs", "no"):
        text += f" {unit}"
    return text


def _cell(text):
    return {"text": text}


def _col(label, width):
    return {"label": label, "width": width}


def _vehicle_label(vehicle):
    if not vehicle:
        return "-"
    return (
        getattr(vehicle, "registration_number", "")
        or getattr(vehicle, "vehicle_number", "")
        or str(vehicle)
    )


def _vehicle_model(vehicle):
    if not vehicle:
        return "-"
    maker = getattr(getattr(vehicle, "manufacturer", None), "manufacturer_name", "") or ""
    model = getattr(getattr(vehicle, "vehicle_model", None), "model_name", "") or ""
    return f"{maker} {model}".strip() or "-"


def _with_description(fixed_cols, insert_at):
    """Description takes the leftover width so every table totals exactly 100%."""
    used = sum(c["width"] for c in fixed_cols)
    cols = list(fixed_cols)
    cols.insert(insert_at, _col("Description", 100 - used))
    return cols


# ---------------------------- main builder ----------------------------
def build_quotation_pdf_context(quotation):
    items = list(quotation.items.all())           # honours prefetch_related("items__...")
    parts = [i for i in items if i.item_type == "part"]
    labours = [i for i in items if i.item_type == "labour"]

    all_complaints = list(quotation.complaints.all())
    complaints = [c for c in all_complaints if c.complaint_type == "customer"]
    findings = [c for c in all_complaints if c.complaint_type == "technician"]

    # vehicles: the attached rows, or the old single-vehicle fields as a fallback
    entries = [(qv.vehicle, qv.mileage) for qv in quotation.vehicles.all()]
    if not entries and quotation.vehicle:
        entries = [(quotation.vehicle, quotation.mileage)]
    show_veh = len(entries) > 1                   # vehicle column only when it adds information

    customer = quotation.customer
    estimate = quotation.estimate
    jobcard = quotation.jobcard
    number = quotation.voucher_number or quotation.quotation_number or f"#{quotation.pk}"

    # ---------------- details box ----------------
    details = [
        {"label": "Customer", "value": getattr(customer, "ledger_name", "") or "-"},
        {"label": "Phone",
         "value": getattr(customer, "mobile", "") or getattr(customer, "phone_no", "") or "-"},
        {"label": "Status", "value": quotation.get_status_display().upper(),
         "tone": STATUS_TONE.get(quotation.status, "")},
        {"label": "Quotation Number", "value": number},
        {"label": "Service Advisor",
         "value": getattr(quotation.advisor, "full_name", "") if quotation.advisor else "-"},
        {"label": "Valid Until", "value": _date(quotation.valid_until) or "-"},
    ]
    if estimate:
        details.append({"label": "Estimate Ref.",
                        "value": estimate.estimate_number or estimate.voucher_number or "-"})
    if jobcard:
        details.append({"label": "Job Card Ref.",
                        "value": getattr(jobcard, "voucher_number", "") or getattr(jobcard, "job_number", "") or "-"})

    sections = []

    # ---------------- vehicle details ----------------
    if entries:
        sections.append({
            "title": "Vehicle Details",
            "columns": [_col("SL", 7), _col("Vehicle Number", 24), _col("Registration", 24),
                        _col("Model", 28), _col("Mileage", 17)],
            "rows": [[
                _cell(_sl(n)),
                _cell(getattr(v, "vehicle_number", "") or "-"),
                _cell(getattr(v, "registration_number", "") or "-"),
                _cell(_vehicle_model(v)),
                _cell(f"{mileage:,} km" if mileage else "-"),
            ] for n, (v, mileage) in enumerate(entries, 1)],
        })

    # ---------------- customer complaints ----------------
    if complaints:
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Category", 14), _col("Type", 16), _col("Technician", 14), _col("Status", 10)]
        cols = _with_description(fixed, 4 if show_veh else 3)
        rows = []
        for n, c in enumerate(complaints, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(c.vehicle)))
            row += [
                _cell(c.category or "-"),
                _cell(c.type or "-"),
                _cell(c.description or "-"),
                _cell(c.technician.full_name if c.technician else "-"),
                _cell(c.status or "-"),
            ]
            rows.append(row)
        sections.append({"title": "Customer Complaints", "columns": cols, "rows": rows})

    # ---------------- technician findings ----------------
    if findings:
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        cols = _with_description(fixed, 2 if show_veh else 1)
        rows = []
        for n, f in enumerate(findings, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(f.vehicle)))
            row.append(_cell(f.description or "-"))
            rows.append(row)
        sections.append({"title": "Technician Findings", "columns": cols, "rows": rows})

    # ---------------- spare parts ----------------
    if parts:
        show_warranty = any((p.warranty or "").strip() not in ("", "None") for p in parts)
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Qty", 9), _col("Rate", 13), _col("Amount", 13)]
        if show_warranty:
            fixed.append(_col("Warranty", 11))
        cols = _with_description(fixed, 2 if show_veh else 1)

        rows = []
        for n, p in enumerate(parts, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(p.vehicle)))
            row += [
                _cell(p.description or "-"),
                _cell(_qty(p)),
                _cell(_money(p.unit_price)),
                _cell(_money(p.total_price())),
            ]
            if show_warranty:
                w = (p.warranty or "").strip()
                row.append(_cell("-" if w in ("", "None") else w))
            rows.append(row)
        sections.append({"title": "Spare Parts", "columns": cols, "rows": rows})

    # ---------------- labour ----------------
    if labours:
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Technician", 16), _col("Hours", 8), _col("Rate / Hr", 13), _col("Total", 13)]
        cols = _with_description(fixed, 2 if show_veh else 1)

        rows = []
        for n, l in enumerate(labours, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(l.vehicle)))
            row += [
                _cell(l.description or "-"),
                _cell(l.technician.full_name if l.technician else "-"),
                _cell(_num(l.hours)),
                _cell(_money(l.unit_price)),
                _cell(_money(l.total_price())),
            ]
            rows.append(row)
        sections.append({"title": "Labour Charges", "columns": cols, "rows": rows})

    # ---------------- quotation summary (subtotal / tax / grand total = the model's own maths) ----------------
    parts_total = sum((Decimal(str(i.total_price())) for i in parts), Decimal("0"))
    labour_total = sum((Decimal(str(i.total_price())) for i in labours), Decimal("0"))
    tax_label = f"VAT ({_num(quotation.tax_percent)}%)" if quotation.tax_percent else "VAT"

    summary = [
        {"label": "Spare Parts", "value": _money(parts_total), "kind": "line"},
        {"label": "Labour Charges", "value": _money(labour_total), "kind": "line"},
        {"label": "Subtotal", "value": _money(quotation.get_subtotal()), "kind": "sub"},
        {"label": "Discount", "value": _money(quotation.discount), "kind": ""},
        {"label": tax_label, "value": _money(quotation.get_tax_amount()), "kind": ""},
        {"label": "GRAND TOTAL", "value": _money(quotation.get_grand_total()), "kind": "grand"},
    ]

    return {
        "document": {
            "title": "QUOTATION",
            "number": number,
            "date": quotation.date,
            "terms": quotation.terms or "",
            "notes": quotation.notes or "",
        },
        "currency": CURRENCY,
        "details": details,
        "sections": sections,
        "summary": summary,
        "signatures": [
            {"label": "Authorized Signature"},
            {"label": "Customer Acceptance"},
        ],
    }