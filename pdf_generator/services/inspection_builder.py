
from django.utils import timezone


def get_related_object(instance, related_name):
    """
    Safely get an optional OneToOne related object.
    Returns None if the related object does not exist.
    """
    try:
        return getattr(instance, related_name)
    except Exception:
        return None


def get_display_value(instance, field_name):
    """
    Get the human-readable choice value of a model field.
    """
    display_method = getattr(
        instance,
        f"get_{field_name}_display",
        None
    )

    if callable(display_method):
        return display_method()

    return getattr(instance, field_name, "") or "-"


def build_inspection_context(inspection):

    vehicle = inspection.vehicle
    customer = inspection.customer

    # -------------------------------------------------
    # 1. Basic inspection details
    # -------------------------------------------------

    details = [
        {
            "label": "Inspection Number",
            "value": inspection.voucher_number or "-"
        },
        {
            "label": "Inspection Date",
            "value": inspection.inspection_date
        },
        {
            "label": "Customer",
            "value": getattr(customer, "ledger_name", "-")
        },
        {
            "label": "Vehicle",
            "value": str(vehicle)
        },
        {
            "label": "Registration Number",
            "value": getattr(vehicle, "registration_number", "-")
        },
        {
            "label": "Inspector",
            "value": (
                getattr(inspection.inspector, "full_name", "-")
                if inspection.inspector else "-"
            )
        },
        {
            "label": "Odometer",
            "value": inspection.odometer or "-"
        },
        {
            "label": "Fuel Level",
            "value": get_display_value(inspection, "fuel_level")
        },
        {
            "label": "Driver Name",
            "value": inspection.driver_name or "-"
        },
        {
            "label": "Overall Status",
            "value": get_display_value(inspection, "overall_status")
        },
    ]

    sections = []

    # -------------------------------------------------
    # 2. Exterior Damage
    # -------------------------------------------------

    exterior_rows = []

    for damage in inspection.exterior_damages.all():
        exterior_rows.append({
            "zone": damage.get_zone_display(),
            "damage_type": damage.get_damage_type_display(),
            "notes": damage.notes or "-"
        })

    if exterior_rows:
        sections.append({
            "title": "Exterior Damage",
            "columns": [
                {"key": "zone", "label": "Vehicle Area"},
                {"key": "damage_type", "label": "Damage Type"},
                {"key": "notes", "label": "Remarks"},
            ],
            "rows": exterior_rows
        })

    # -------------------------------------------------
    # 3. Interior Inspection
    # -------------------------------------------------

    interior = get_related_object(inspection, "interior")

    if interior:
        interior_fields = [
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

        sections.append({
            "title": "Interior Inspection",
            "columns": [
                {"key": "item", "label": "Item"},
                {"key": "condition", "label": "Condition"},
            ],
            "rows": [
                {
                    "item": label,
                    "condition": get_display_value(interior, field)
                }
                for field, label in interior_fields
            ]
        })

    # -------------------------------------------------
    # 4. Mechanical Inspection
    # -------------------------------------------------

    mechanical = get_related_object(inspection, "mechanical")

    if mechanical:
        mechanical_fields = [
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

        sections.append({
            "title": "Mechanical Inspection",
            "columns": [
                {"key": "item", "label": "Item"},
                {"key": "condition", "label": "Condition"},
            ],
            "rows": [
                {
                    "item": label,
                    "condition": get_display_value(mechanical, field)
                }
                for field, label in mechanical_fields
            ]
        })

    # -------------------------------------------------
    # 5. Accessories Inspection
    # -------------------------------------------------

    accessories = get_related_object(inspection, "accessories")

    if accessories:
        accessory_fields = [
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

        sections.append({
            "title": "Accessories Inspection",
            "columns": [
                {"key": "item", "label": "Accessory"},
                {"key": "status", "label": "Status"},
            ],
            "rows": [
                {
                    "item": label,
                    "status": get_display_value(accessories, field)
                }
                for field, label in accessory_fields
            ]
        })

    # -------------------------------------------------
    # 6. Customer Complaints and Technician Findings
    # -------------------------------------------------

    finding_rows = []

    for finding in inspection.findings.all():
        finding_rows.append({
            "type": finding.get_finding_type_display(),
            "description": finding.description
        })

    if finding_rows:
        sections.append({
            "title": "Customer Complaints & Technician Findings",
            "columns": [
                {"key": "type", "label": "Type"},
                {"key": "description", "label": "Description"},
            ],
            "rows": finding_rows
        })

    # -------------------------------------------------
    # 7. Exterior Remarks
    # -------------------------------------------------

    if inspection.exterior_remarks:
        sections.append({
            "title": "Exterior Remarks",
            "text": inspection.exterior_remarks
        })

    # -------------------------------------------------
    # 8. Custom Inspection
    # -------------------------------------------------

    custom_inspection = get_related_object(
        inspection,
        "custom_inspection"
    )

    if custom_inspection:
        answers = custom_inspection.answers.all().order_by("order")

        grouped_answers = {}

        for answer in answers:
            group_key = (
                answer.main_head_name or "Other",
                answer.sub_head_name or "General"
            )

            grouped_answers.setdefault(group_key, []).append({
                "label": answer.label,
                "type": answer.type_name or answer.field_type or "-",
                "value": answer.value or "-",
                "remark": answer.remark or "-"
            })

        for (main_head, sub_head), answer_rows in grouped_answers.items():
            sections.append({
                "title": f"{main_head} - {sub_head}",
                "columns": [
                    {"key": "label", "label": "Inspection Item"},
                    {"key": "type", "label": "Type"},
                    {"key": "value", "label": "Value"},
                    {"key": "remark", "label": "Remarks"},
                ],
                "rows": answer_rows
            })

    # -------------------------------------------------
    # 9. Final PDF Context
    # -------------------------------------------------

    return {
        "company": {
            "name": "",
            "address": "",
            "phone": "",
            "email": "",
        },
        "document": {
            "title": "VEHICLE INSPECTION REPORT",
            "subtitle": "Standard & Custom Inspection",
            "number": inspection.voucher_number or str(inspection.pk),
            "date": inspection.inspection_date,
            "notes": inspection.customer_signature_note or "",
        },
        "details": details,
        "sections": sections,
        "rows": [],
        "columns": [],
        "totals": [],
        "amount_in_words": "",
        "signatures": [],
    }
