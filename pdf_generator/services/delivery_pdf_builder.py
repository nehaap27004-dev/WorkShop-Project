CURRENCY = "OMR"
DECIMALS = 3          # OMR uses 3 decimals. Set to 2 for 1,330.75 style.

STATUS_TONE = {
    "delivered": "good",
    "cancelled": "poor",
}


# ---------------------------- small helpers ----------------------------
def _money(value):
    return f"{float(value or 0):,.{DECIMALS}f}"


def _num(value):
    """Quantities / hours: up to 3 decimals, no trailing zeros (2.000 -> 2, 1.250 -> 1.25)."""
    text = f"{float(value or 0):.3f}".rstrip("0").rstrip(".")
    return text or "0"


def _sl(n):
    return f"{n:02d}"


def _qty(part):
    text = _num(part.quantity)
    unit = (part.unit or "").strip()
    if unit and unit.lower() not in ("no", "pcs"):
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
def build_delivery_pdf_context(dn):
    parts = list(dn.parts.all())                  # honours prefetch_related(...)
    labours = list(dn.labours.all())
    services = list(dn.services.all())

    # vehicles: the attached rows, or the old single-vehicle field as a fallback
    entries = [(dv.vehicle, dv.mileage) for dv in dn.vehicles.all()]
    if not entries and dn.vehicle:
        entries = [(dn.vehicle, dn.odometer_out)]
    show_veh = len(entries) > 1                   # vehicle column only when it adds information

    customer = dn.customer
    jobcard = dn.jobcard
    number = dn.voucher_number or f"#{dn.pk}"

    # ---------------- details box ----------------
    details = [
        {"label": "Customer", "value": getattr(customer, "ledger_name", "") or "-"},
        {"label": "Contact Number",
         "value": dn.contact_number or getattr(customer, "mobile", "") or getattr(customer, "phone_no", "") or "-"},
        {"label": "Status", "value": dn.get_status_display().upper(),
         "tone": STATUS_TONE.get(dn.status, "")},
        {"label": "Delivery Number", "value": number},
        {"label": "Job Card Ref.",
         "value": (getattr(jobcard, "job_number", "") or getattr(jobcard, "voucher_number", "") or "-")
         if jobcard else "-"},
        {"label": "Payment Mode",
         "value": dn.get_payment_mode_display() if dn.payment_mode else "-"},
        {"label": "Driver Name", "value": dn.driver_name or "-"},
        {"label": "Service Advisor",
         "value": getattr(dn.advisor, "full_name", "") if dn.advisor else "-"},
        {"label": "Technician",
         "value": getattr(dn.technician, "full_name", "") if dn.technician else "-"},
    ]
    if dn.quotation:
        details.append({"label": "Quotation Ref.",
                        "value": dn.quotation.quotation_number or dn.quotation.voucher_number or "-"})
    if dn.estimate:
        details.append({"label": "Estimate Ref.",
                        "value": dn.estimate.estimate_number or dn.estimate.voucher_number or "-"})
    if dn.header_remarks:
        details.append({"label": "Remarks", "value": dn.header_remarks})

    # ---------------- handover: condition table + tick list ----------------
    condition_cells = [
        ("Exterior",     17, dn.exterior_condition),
        ("Interior",     17, dn.interior_condition),
        ("Fuel Out",     12, dn.fuel_level_out),
        ("Odometer Out", 16, f"{dn.odometer_out:,} km" if dn.odometer_out else ""),
        ("Accessories",  22, dn.accessories_returns),
        ("Cleanliness",  16, dn.vehicle_cleanliness),
    ]
    condition_table = None
    if any(v for _, _, v in condition_cells):
        condition_table = {
            "columns": [_col(label, width) for label, width, _ in condition_cells],
            "row": [_cell(v or "-") for _, _, v in condition_cells],
        }

    checklist = [
        {"label": label, "checked": bool(flag)}
        for label, flag in [
            ("Work completed", dn.work_completed),
            ("Quality checked", dn.quality_checked),
            ("Road test", dn.road_test),
            ("Vehicle washed", dn.vehicle_washed),
            ("Spare wheel", dn.spare_wheel),
            ("Tool kit", dn.tool_kit),
            ("Documents returned", dn.documents_returned),
            ("Customer signed", dn.customer_signed),
        ]
    ]
    if not any(c["checked"] for c in checklist):
        checklist = []          # nothing ticked yet (draft) -> hide the block

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

    # ---------------- completed services ----------------
    if services:
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Qty", 8), _col("Status", 14), _col("Remarks", 22)]
        cols = _with_description(fixed, 2 if show_veh else 1)
        rows = []
        for n, s in enumerate(services, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(s.vehicle)))
            row += [
                _cell(s.description or "-"),
                _cell(_num(s.quantity)),
                _cell(s.status or "-"),
                _cell(s.remarks or "-"),
            ]
            rows.append(row)
        sections.append({"title": "Completed Services", "columns": cols, "rows": rows})

    # ---------------- spare parts used ----------------
    if parts:
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Item Code", 14), _col("Qty", 9), _col("Rate", 13), _col("Amount", 13)]
        cols = _with_description(fixed, 2 if show_veh else 1)
        rows = []
        for n, p in enumerate(parts, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(p.vehicle)))
            row += [
                _cell(p.name or "-"),
                _cell(p.item_code or "-"),
                _cell(_qty(p)),
                _cell(_money(p.rate)),
                _cell(_money(float(p.quantity or 0) * float(p.rate or 0))),
            ]
            rows.append(row)
        sections.append({"title": "Spare Parts Used", "columns": cols, "rows": rows})

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
                _cell(_money(l.rate)),
                _cell(_money(float(l.hours or 0) * float(l.rate or 0))),
            ]
            rows.append(row)
        sections.append({"title": "Labour Charges", "columns": cols, "rows": rows})

    # ---------------- summary (the model's own maths) ----------------
    tax_label = f"VAT ({_num(dn.tax_percent)}%)" if dn.tax_percent else "VAT"
    summary = [
        {"label": "Spare Parts", "value": _money(dn.get_parts_total()), "kind": "line"},
        {"label": "Labour Charges", "value": _money(dn.get_labour_total()), "kind": "line"},
        {"label": "Subtotal", "value": _money(dn.get_subtotal()), "kind": "sub"},
        {"label": "Discount", "value": _money(dn.discount), "kind": ""},
        {"label": tax_label, "value": _money(dn.get_tax_amount()), "kind": ""},
        {"label": "GRAND TOTAL", "value": _money(dn.get_grand_total()), "kind": "grand"},
        {"label": "Advance Received", "value": _money(dn.advance_received), "kind": "paid"},
        {"label": "BALANCE", "value": _money(dn.get_balance()), "kind": "balance"},
    ]

    return {
        "document": {
            "title": "DELIVERY NOTE",
            "number": number,
            "date": dn.date,
            "time": dn.delivery_time,
            "condition_remarks": dn.condition_remarks or "",
            "notes": dn.notes or "",
        },
        "currency": CURRENCY,
        "details": details,
        "condition_table": condition_table,
        "checklist": checklist,
        "sections": sections,
        "summary": summary,
        "signatures": [
            {"label": "Handed Over By"},
            {"label": "Received By (Customer)"},
        ],
    }