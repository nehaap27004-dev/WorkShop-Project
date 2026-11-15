from collections import OrderedDict


def build_custom_inspection_context(custom_inspection):
    customer = custom_inspection.customer
    vehicle = custom_inspection.vehicle
    number = custom_inspection.inspection_number or str(custom_inspection.pk)

    # First two items are shown wide (50%), the rest 25% each
    details = [
        {"label": "Customer", "value": getattr(customer, "ledger_name", "-")},
        {"label": "Vehicle", "value": str(vehicle) if vehicle else "-"},
        {"label": "Inspection Number", "value": number},
        {"label": "Inspection Date", "value": custom_inspection.inspection_date},
        {"label": "Registration Number",
         "value": getattr(vehicle, "registration_number", "-") if vehicle else "-"},
        {"label": "Inspector",
         "value": getattr(custom_inspection.inspector, "full_name", "-")
         if custom_inspection.inspector else "-"},
    ]

    # CustomInspectionAnswer already orders by (order, id) in its Meta
    grouped = OrderedDict()
    for answer in custom_inspection.answers.all():
        key = (answer.main_head_name or "Other", answer.sub_head_name or "General")
        grouped.setdefault(key, []).append({
            "label": answer.label or "-",
            "type": answer.type_name or answer.field_type or "-",
            "value": answer.value or "-",
            "remark": answer.remark or "-",
        })

    sections = [
        {"main_head": main, "sub_head": sub, "rows": rows}
        for (main, sub), rows in grouped.items()
    ]

    return {
        "company": {"name": "Silver Line Group"},
        "document": {
            "title": "Vehicle Inspection Report",
            "number": number,
            "date": custom_inspection.inspection_date,
            "notes": custom_inspection.notes or "",
        },
        "details": details,
        "sections": sections,
        "total_items": sum(len(s["rows"]) for s in sections),
        "signatures": [
            {"label": "Inspector Signature"},
            {"label": "Manager Signature"},
        ],
    }