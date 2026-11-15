INTERIOR_ITEMS = [
    ("dashboard", "Dashboard"),
    ("seats", "Seats"),
    ("steering_wheel", "Steering Wheel"),
    ("ac_system", "AC System"),
    ("audio_system", "Audio System"),
    ("windows", "Windows"),
    ("seat_belts", "Seat Belts"),
    ("floor_carpet", "Floor Carpet"),
    ("headliner", "Headliner"),
    ("door_panels", "Door Panels"),
]

MECHANICAL_ITEMS = [
    ("oil_leak", "Oil Leak"),
    ("coolant_leak", "Coolant Leak"),
    ("abnormal_noise", "Abnormal Noise"),
    ("brake_pad", "Brake Pad"),
    ("brake_disc", "Brake Disc"),
    ("shock_absorbers", "Shock Absorbers"),
    ("bushes", "Bushes"),
    ("battery", "Battery"),
    ("starter", "Starter"),
    ("lights", "Lights"),
    ("tyre_fl", "Front Left Tyre"),
    ("tyre_fr", "Front Right Tyre"),
    ("tyre_rl", "Rear Left Tyre"),
    ("tyre_rr", "Rear Right Tyre"),
    ("tyre_spare", "Spare Tyre"),
    ("brake_fluid", "Brake Fluid"),
    ("steering_fluid", "Power Steering Fluid"),
    ("washer_fluid", "Washer Fluid"),
    ("exhaust_system", "Exhaust System"),
]

ACCESSORY_ITEMS = [
    ("spare_wheel", "Spare Wheel"),
    ("tool_kit", "Tool Kit"),
    ("service_book", "Service Book"),
    ("remote_key", "Remote Key"),
    ("safety_triangle", "Safety Triangle"),
    ("floor_mat", "Floor Mat"),
    ("jack", "Jack"),
    ("fire_extinguisher", "Fire Extinguisher"),
    ("first_aid_kit", "First Aid Kit"),
]

STATUS_TONE = {"pass": "good", "attention": "fair", "fail": "poor"}


def _rows(obj, items):
    """One row per checklist field. `tone` is used for colouring in the PDF."""
    rows = []
    for field, label in items:
        if obj is None:
            rows.append({"item": label, "status": "-", "tone": ""})
            continue
        rows.append({
            "item": label,
            "status": getattr(obj, f"get_{field}_display")(),
            "tone": getattr(obj, field, ""),
        })
    return rows


def build_regular_inspection_context(inspection):
    vehicle = inspection.vehicle
    customer = inspection.customer
    number = inspection.inspection_number or str(inspection.pk)

    # reverse one-to-one: getattr with default is safe when the record is missing
    interior = getattr(inspection, "interior", None)
    mechanical = getattr(inspection, "mechanical", None)
    accessories = getattr(inspection, "accessories", None)

    details = [
        {"label": "Customer", "value": getattr(customer, "ledger_name", "-")},
        {"label": "Vehicle", "value": str(vehicle) if vehicle else "-"},
        {"label": "Inspection Number", "value": number},
        {"label": "Inspection Date", "value": inspection.inspection_date},
        {"label": "Registration Number",
         "value": getattr(vehicle, "registration_number", "-") if vehicle else "-"},
        {"label": "Inspector",
         "value": getattr(inspection.inspector, "full_name", "-")
         if inspection.inspector else "-"},
        {"label": "Odometer", "value": inspection.odometer if inspection.odometer is not None else "-"},
        {"label": "Fuel Level", "value": inspection.get_fuel_level_display()},
        {"label": "Driver Name", "value": inspection.driver_name or "-"},
        {"label": "Overall Status",
         "value": inspection.get_overall_status_display(),
         "tone": STATUS_TONE.get(inspection.overall_status, "")},
    ]

    left_sections = [
        {"title": "Interior Inspection", "item_label": "Item", "status_label": "Condition",
         "rows": _rows(interior, INTERIOR_ITEMS)},
        {"title": "Accessories Inspection", "item_label": "Accessory", "status_label": "Status",
         "rows": _rows(accessories, ACCESSORY_ITEMS)},
    ]
    right_sections = [
        {"title": "Mechanical Inspection", "item_label": "Item", "status_label": "Condition",
         "rows": _rows(mechanical, MECHANICAL_ITEMS)},
    ]

    # Full-width sections, shown only when there is something to print
    extra_sections = []

    damages = list(inspection.exterior_damages.all())
    if damages:
        extra_sections.append({
            "title": "Exterior Damage",
            "headers": ["Sl No", "Zone", "Damage Type", "Notes"],
            "rows": [[i, d.get_zone_display(), d.get_damage_type_display(), d.notes or "-"]
                     for i, d in enumerate(damages, 1)],
        })

    all_findings = list(inspection.findings.all())
    complaints = [f for f in all_findings if f.finding_type == "complaint"]
    findings = [f for f in all_findings if f.finding_type == "finding"]
    if complaints:
        extra_sections.append({
            "title": "Customer Complaints",
            "headers": ["Sl No", "Description"],
            "rows": [[i, f.description] for i, f in enumerate(complaints, 1)],
        })
    if findings:
        extra_sections.append({
            "title": "Technician Findings",
            "headers": ["Sl No", "Description"],
            "rows": [[i, f.description] for i, f in enumerate(findings, 1)],
        })

    return {
        "document": {
            "title": "Vehicle Inspection Report",
            "number": number,
            "date": inspection.inspection_date,
            "notes": inspection.exterior_remarks or "",
        },
        "details": details,
        "columns": [left_sections, right_sections],
        "extra_sections": extra_sections,
        "signatures": [
            {"label": "Inspector Signature"},
            {"label": "Manager Signature"},
        ],
    }