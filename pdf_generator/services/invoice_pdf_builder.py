CURRENCY = "OMR"
DECIMALS = 3          # OMR uses 3 decimals (baisa). Set to 2 if you want 1,330.75 style.

# Optional: printed under the "INVOICE" title when filled. Left empty = hidden.
COMPANY = {
    "name": "",
    "address": "",
    "phone": "",
    "email": "",
    "tax_no": "",     # e.g. "VAT No: OM1234567890"
}

STATUS_TONE = {
    "paid": "good",
    "partial": "good",
    "overdue": "poor",
    "cancelled": "poor",
}


# ---------------------------- small helpers ----------------------------
def _money(value):
    return f"{float(value or 0):,.{DECIMALS}f}"


def _num(value):
    """2.00 -> '2', 1.50 -> '1.5'"""
    text = f"{float(value or 0):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _pct(value):
    return f"{_num(value)}%"


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
        getattr(vehicle, "vehicle_number", "")
        or getattr(vehicle, "registration_number", "")
        or str(vehicle)
    )


def _vehicle_model(vehicle):
    if not vehicle:
        return "-"
    maker = getattr(getattr(vehicle, "manufacturer", None), "manufacturer_name", "") or ""
    model = getattr(getattr(vehicle, "vehicle_model", None), "model_name", "") or ""
    return f"{maker} {model}".strip() or "-"


def _with_description(fixed_cols, insert_at):
    """Put a Description column in; it takes whatever width is left so the table always totals 100%."""
    used = sum(c["width"] for c in fixed_cols)
    cols = list(fixed_cols)
    cols.insert(insert_at, _col("Description", 100 - used))
    return cols


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

    # ---------------- details box ----------------
    details = [
        {"label": "Customer", "value": getattr(customer, "ledger_name", "") or "-"},
        {"label": "Billing Address",
         "value": invoice.customer_address or getattr(customer, "address1", "") or "-"},
        {"label": "Payment Status", "value": invoice.get_status_display().upper(),
         "tone": STATUS_TONE.get(invoice.status, "")},
        {"label": "Invoice Number", "value": invoice.display_number},
        {"label": "Payment Mode", "value": invoice.get_payment_mode_display()},
        {"label": "Job Card Ref.", "value": jobcard.job_number if jobcard else "-"},
    ]
    mobile = invoice.customer_mobile or getattr(customer, "mobile", "") or ""
    if mobile:
        details.append({"label": "Mobile", "value": mobile})
    if invoice.due_date:
        details.append({"label": "Due Date", "value": invoice.due_date.strftime("%d %b %Y")})

    sections = []

    # ---------------- vehicle details ----------------
    if invoice_vehicles:
        sections.append({
            "title": "Vehicle Details",
            "columns": [_col("SL", 7), _col("Vehicle Number", 24), _col("Registration", 24),
                        _col("Model", 28), _col("Mileage", 17)],
            "rows": [[
                _cell(_sl(n)),
                _cell(_vehicle_label(iv.vehicle)),
                _cell(getattr(iv.vehicle, "registration_number", "") or "-"),
                _cell(_vehicle_model(iv.vehicle)),
                _cell(f"{iv.mileage:,} km" if iv.mileage else "-"),
            ] for n, iv in enumerate(invoice_vehicles, 1)],
        })

    # ---------------- spare parts ----------------
    if parts:
        show_disc = any(float(p.discount_pct or 0) > 0 for p in parts)
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Item Code", 14), _col("Qty", 8), _col("Rate", 13)]
        if show_disc:
            fixed.append(_col("Disc %", 8))
        fixed += [_col("Tax", 8), _col("Total", 13)]
        cols = _with_description(fixed, 2 if show_veh else 1)

        rows = []
        for n, p in enumerate(parts, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(p.vehicle)))
            row += [
                _cell(p.description or "-"),
                _cell(p.item_code or "-"),
                _cell(_qty(p)),
                _cell(_money(p.unit_price)),
            ]
            if show_disc:
                row.append(_cell(_pct(p.discount_pct)))
            row += [_cell(_pct(p.tax_percent)), _cell(_money(p.total_price()))]
            rows.append(row)
        sections.append({"title": "Spare Parts", "columns": cols, "rows": rows})

    # ---------------- labour ----------------
    if labours:
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Technician", 16), _col("Hours", 8), _col("Rate", 13),
                  _col("Tax", 8), _col("Total", 13)]
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
                _cell(_pct(l.tax_percent)),
                _cell(_money(l.total_price())),
            ]
            rows.append(row)
        sections.append({"title": "Labour Charges", "columns": cols, "rows": rows})

    # ---------------- other charges ----------------
    if others:
        fixed = [_col("SL", 6)]
        if show_veh:
            fixed.append(_col("Vehicle", 12))
        fixed += [_col("Amount", 15), _col("Tax %", 9), _col("Tax Amount", 14), _col("Total", 15)]
        cols = _with_description(fixed, 2 if show_veh else 1)

        rows = []
        for n, o in enumerate(others, 1):
            row = [_cell(_sl(n))]
            if show_veh:
                row.append(_cell(_vehicle_label(o.vehicle)))
            row += [
                _cell(o.description or "-"),
                _cell(_money(o.unit_price)),
                _cell(_pct(o.tax_percent)),
                _cell(_money(o.get_tax_amount())),
                _cell(_money(o.total_price())),
            ]
            rows.append(row)
        sections.append({"title": "Other Charges", "columns": cols, "rows": rows})

    # ---------------- payment summary ----------------
    # Section lines are tax-inclusive (same as the TOTAL column of each table).
    # Grand total = Subtotal - Discount = Taxable Amount + VAT   (same maths as the Invoice model)
    net = invoice.get_subtotal()
    tax = invoice.get_total_tax()
    disc_rate = float(invoice.discount_pct or 0) / 100
    taxable = net * (1 - disc_rate)
    vat = tax * (1 - disc_rate)

    rates = {float(i.tax_percent) for i in items if float(i.tax_percent or 0) > 0}
    vat_label = f"VAT ({_num(rates.pop())}%)" if len(rates) == 1 else "VAT"
    disc_label = f"Discount ({_num(invoice.discount_pct)}%)" if disc_rate else "Discount"

    summary = [
        {"label": "Spare Parts", "value": _money(invoice.get_parts_total()), "kind": "line"},
        {"label": "Labour Charges", "value": _money(invoice.get_labour_total()), "kind": "line"},
        {"label": "Other Charges", "value": _money(invoice.get_other_total()), "kind": "line"},
        {"label": "Subtotal (incl. tax)", "value": _money(net + tax), "kind": "sub"},
        {"label": disc_label, "value": _money(invoice.get_discount_amount()), "kind": ""},
        {"label": "Taxable Amount", "value": _money(taxable), "kind": ""},
        {"label": vat_label, "value": _money(vat), "kind": ""},
        {"label": "GRAND TOTAL", "value": _money(invoice.get_grand_total()), "kind": "grand"},
        {"label": "Amount Paid", "value": _money(invoice.amount_paid), "kind": "paid"},
        {"label": "BALANCE DUE", "value": _money(invoice.get_balance_due()), "kind": "balance"},
    ]

    return {
        "company": {k: v for k, v in COMPANY.items() if v},
        "document": {
            "title": "INVOICE",
            "number": invoice.display_number,
            "date": invoice.invoice_date,
            "notes": invoice.notes or "",
        },
        "currency": CURRENCY,
        "details": details,
        "sections": sections,
        "summary": summary,
        "signatures": [
            {"label": "Authorized Signature"},
            {"label": "Customer Signature"},
        ],
    }