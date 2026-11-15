CURRENCY = "OMR"

# >>> EDIT THESE: printed at the top of every invoice. Empty lines are hidden. <<<
COMPANY = {
    "name": "Silver Line Group",
    "address": "",       # e.g. "P.O. Box 123, Muscat, Sultanate of Oman"
    "phone": "",         # e.g. "+968 2400 0000"
    "email": "",         # e.g. "info@silverline.example"
    "tax_no": "",        # e.g. "VAT No: OM1234567890"
}

STATUS_TONE = {
    "paid": "good",
    "partial": "fair",
    "overdue": "poor",
    "cancelled": "poor",
}


# ---------------------------- small helpers ----------------------------
def _money(value):
    return f"{float(value or 0):,.3f}"


def _num(value):
    """2.00 -> '2', 1.50 -> '1.5'"""
    text = f"{float(value or 0):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _date(value):
    return value.strftime("%d %b %Y") if value else ""


def _cell(text, align=""):
    return {"text": text, "align": align}


def _col(label, width, align=""):
    return {"label": label, "width": width, "align": align}


def _vehicle_label(vehicle):
    if not vehicle:
        return "-"
    return (
        getattr(vehicle, "vehicle_number", "")
        or getattr(vehicle, "registration_number", "")
        or str(vehicle)
    )


def _vehicle_model(vehicle):
    if not vehicle:
        return ""
    maker = getattr(getattr(vehicle, "manufacturer", None), "manufacturer_name", "") or ""
    model = getattr(getattr(vehicle, "vehicle_model", None), "model_name", "") or ""
    return f"{maker} {model}".strip()


# ---------------------------- main builder ----------------------------
def build_invoice_pdf_context(invoice):
    items = list(invoice.items.all())          # honours prefetch_related("items__...")
    parts = [i for i in items if i.item_type == "part"]
    labours = [i for i in items if i.item_type == "labour"]
    others = [i for i in items if i.item_type == "other"]

    invoice_vehicles = list(invoice.vehicles.all())
    show_veh = len(invoice_vehicles) > 1       # vehicle column only when it adds information

    customer = invoice.customer
    jobcard = invoice.jobcard

    # ---------------- company + bill-to ----------------
    company = {k: v for k, v in COMPANY.items() if v}

    bill_to = {
        "name": getattr(customer, "ledger_name", "") or "-",
        "address": invoice.customer_address or getattr(customer, "address1", "") or "",
        "mobile": invoice.customer_mobile or getattr(customer, "mobile", "") or "",
    }

    # ---------------- invoice info (empty values are left out) ----------------
    info = [
        {"label": "Invoice Date", "value": _date(invoice.invoice_date)},
        {"label": "Due Date", "value": _date(invoice.due_date)},
        {"label": "Payment Mode", "value": invoice.get_payment_mode_display()},
        {"label": "Job Card", "value": jobcard.job_number if jobcard else ""},
        {"label": "Status", "value": invoice.get_status_display(),
         "tone": STATUS_TONE.get(invoice.status, "")},
    ]
    info = [row for row in info if row["value"]]

    # ---------------- vehicles (one line each) ----------------
    vehicle_lines = []
    for iv in invoice_vehicles:
        v = iv.vehicle
        bits = [_vehicle_label(v)]
        reg = getattr(v, "registration_number", "") or ""
        if reg and reg != bits[0]:
            bits.append(reg)
        model = _vehicle_model(v)
        if model:
            bits.append(model)
        if iv.mileage:
            bits.append(f"{iv.mileage:,} km")
        vehicle_lines.append("  |  ".join(bits))

    sections = []

    # ---------------- spare parts ----------------
    if parts:
        cols = [_col("Sl No", 7)]
        if show_veh:
            cols.append(_col("Vehicle", 12))
        cols += [
            _col("Description", 17 if show_veh else 28),
            _col("Code", 11),
            _col("Qty", 5 if show_veh else 6, "r"), _col("Unit", 5 if show_veh else 6),
            _col("Rate", 10 if show_veh else 11, "r"), _col("Disc %", 7, "r"), _col("Tax %", 6, "r"),
            _col("Tax Amt", 9 if show_veh else 8, "r"), _col("Total", 11 if show_veh else 10, "r"),
        ]
        rows = []
        for n, p in enumerate(parts, 1):
            row = [_cell(n)]
            if show_veh:
                row.append(_cell(_vehicle_label(p.vehicle)))
            row += [
                _cell(p.description or "-"),
                _cell(p.item_code or "-"),
                _cell(_num(p.quantity), "r"),
                _cell(p.unit or "-"),
                _cell(_money(p.unit_price), "r"),
                _cell(_num(p.discount_pct), "r"),
                _cell(_num(p.tax_percent), "r"),
                _cell(_money(p.get_tax_amount()), "r"),
                _cell(_money(p.total_price()), "r"),
            ]
            rows.append(row)
        sections.append({
            "title": "Spare Parts", "columns": cols, "rows": rows,
            "total_label": "Spare Parts Total",
            "tax": _money(invoice.get_parts_tax()),
            "total": _money(invoice.get_parts_total()),
        })

    # ---------------- labour ----------------
    if labours:
        cols = [_col("Sl No", 7)]
        if show_veh:
            cols.append(_col("Vehicle", 12))
        cols += [
            _col("Description / Work Done", 22 if show_veh else 30),
            _col("Technician", 16 if show_veh else 18),
            _col("Hours", 7 if show_veh else 8, "r"), _col("Rate / Hr", 10 if show_veh else 11, "r"),
            _col("Tax %", 6 if show_veh else 7, "r"),
            _col("Tax Amt", 9, "r"), _col("Total", 11 if show_veh else 10, "r"),
        ]
        rows = []
        for n, l in enumerate(labours, 1):
            row = [_cell(n)]
            if show_veh:
                row.append(_cell(_vehicle_label(l.vehicle)))
            row += [
                _cell(l.description or "-"),
                _cell(l.technician.full_name if l.technician else "-"),
                _cell(_num(l.hours), "r"),
                _cell(_money(l.unit_price), "r"),
                _cell(_num(l.tax_percent), "r"),
                _cell(_money(l.get_tax_amount()), "r"),
                _cell(_money(l.total_price()), "r"),
            ]
            rows.append(row)
        sections.append({
            "title": "Labour Charges", "columns": cols, "rows": rows,
            "total_label": "Labour Total",
            "tax": _money(invoice.get_labour_tax()),
            "total": _money(invoice.get_labour_total()),
        })

    # ---------------- other charges ----------------
    if others:
        cols = [_col("Sl No", 7)]
        if show_veh:
            cols.append(_col("Vehicle", 12))
        cols += [
            _col("Description", 31 if show_veh else 43),
            _col("Amount", 14, "r"), _col("Tax %", 8, "r"),
            _col("Tax Amt", 12, "r"), _col("Total", 16, "r"),
        ]
        rows = []
        for n, o in enumerate(others, 1):
            row = [_cell(n)]
            if show_veh:
                row.append(_cell(_vehicle_label(o.vehicle)))
            row += [
                _cell(o.description or "-"),
                _cell(_money(o.unit_price), "r"),
                _cell(_num(o.tax_percent), "r"),
                _cell(_money(o.get_tax_amount()), "r"),
                _cell(_money(o.total_price()), "r"),
            ]
            rows.append(row)
        sections.append({
            "title": "Other Charges", "columns": cols, "rows": rows,
            "total_label": "Other Charges Total",
            "tax": _money(invoice.get_other_tax()),
            "total": _money(invoice.get_other_total()),
        })

    # ---------------- payment summary ----------------
    summary = [
        {"label": "Spare Parts", "value": _money(invoice.get_parts_total())},
        {"label": "Labour Charges", "value": _money(invoice.get_labour_total())},
        {"label": "Other Charges", "value": _money(invoice.get_other_total())},
        {"label": "Subtotal (Before Tax)", "value": _money(invoice.get_subtotal())},
        {"label": "Total Tax", "value": _money(invoice.get_total_tax())},
    ]
    if float(invoice.discount_pct or 0):
        summary.append({
            "label": f"Discount ({_num(invoice.discount_pct)}%)",
            "value": "-" + _money(invoice.get_discount_amount()),
        })

    return {
        "company": company,
        "document": {
            "title": "TAX INVOICE",
            "number": invoice.display_number,
            "date": invoice.invoice_date,
            "notes": invoice.notes or "",
        },
        "currency": CURRENCY,
        "bill_to": bill_to,
        "info": info,
        "vehicle_lines": vehicle_lines,
        "sections": sections,
        "summary": summary,
        "grand_total": _money(invoice.get_grand_total()),
        "amount_paid": _money(invoice.amount_paid),
        "balance_due": _money(invoice.get_balance_due()),
        "signatures": [
            {"label": "Authorized Signature"},
            {"label": "Customer Signature"},
        ],
    }