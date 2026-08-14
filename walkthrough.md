# Relational Mapping & WorkshopVehicle Test Fix Walkthrough

## Overview
This walkthrough details the technical changes implemented for Job Card relational mapping and unit test updates:
1. Updated `jobcard_app/tests.py` to fix `WorkshopVehicle` instantiation using foreign key models (`Manufacturer` and `VehicleModel`).
2. Updated `_save_jobcard` in `jobcard_app/views.py` to prevent orphaned `JobCard` objects when technician skill validation fails.
3. Successfully executed `RelationalMappingTests` suite with 100% pass rate.
4. Verified dynamic filtering UI workflow across Service Categories, Complaint Types, Skill Tags, and Technician assignments.

---

## Technical Changes Made

### 1. `_get_relational_mapping_dict` Implementation
Location: [`jobcard_app/views.py`](file:///c:/Silver%20Line%20Group/Silver%20Line%20Group/accounts/jobcard_app/views.py#L942-L993)

```python
def _get_relational_mapping_dict():
    """
    Returns relational dictionary connecting Service Categories, Complaint Types,
    Required Skills, and Technician Skill Assignments.
    """
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        'complaint_types__required_skill'
    )
    # Formats categories, complaint types, skill tags, and technician skills into a JSON payload
    ...
```

### 2. `WorkshopVehicle` Creation in Tests
Location: [`jobcard_app/tests.py`](file:///c:/Silver%20Line%20Group/Silver%20Line%20Group/accounts/jobcard_app/tests.py)

Created helper function `create_test_vehicle` to instantiate valid `Manufacturer` and `VehicleModel` foreign-key objects prior to creating `WorkshopVehicle` instances across test cases:

```python
def create_test_vehicle(customer, registration_number, make_name='Toyota', model_name='Corolla'):
    cat, _ = VehicleCategory.objects.get_or_create(category_name='Sedan')
    mfr, _ = Manufacturer.objects.get_or_create(manufacturer_name=make_name)
    vmodel, _ = VehicleModel.objects.get_or_create(
        manufacturer=mfr,
        model_name=model_name,
        defaults={'vehicle_category': cat}
    )
    return WorkshopVehicle.objects.create(
        customer=customer,
        registration_number=registration_number,
        manufacturer=mfr,
        vehicle_model=vmodel,
    )
```

### 3. Technician Skill Validation Handling
Location: [`jobcard_app/views.py`](file:///c:/Silver%20Line%20Group/Silver%20Line%20Group/accounts/jobcard_app/views.py#L776-L786)

Updated POST handler to delete newly instantiated `JobCard` instances when technician skill validation fails without manual override:

```python
if tech and ct_obj and ct_obj.required_skill and not override_flag:
    has_skill = TechnicianSkill.objects.filter(technician=tech, skill=ct_obj.required_skill).exists()
    if not has_skill:
        if is_new_job and job.pk:
            job.delete()
        messages.error(...)
        return redirect(request.path)
```

---

## Test Execution Results

Command executed:
```bash
python manage.py test jobcard_app.tests.RelationalMappingTests --keepdb
```

Output:
```text
Using existing test database for alias 'default'...
System check identified 1 issue (0 silenced).
....
----------------------------------------------------------------------
Ran 4 tests in 2.997s

OK
Preserving test database for alias 'default'...
Found 4 test(s).
```

### Tests Verified:
1. `test_relational_mapping_ajax`: Verified `/jobcard/ajax/relational-mapping/` endpoint returns categories, technicians, and skills JSON structure.
2. `test_unqualified_technician_blocked_without_manual_override`: Verified submission without skill or manual override is rejected and no JobCard persists.
3. `test_unqualified_technician_allowed_with_manual_override`: Verified submission with `complaint_manual_override[] = '1'` saves JobCard with `is_manual_override = True`.
4. `test_qualified_technician_allowed_without_override`: Verified technician matching `required_skill` saves JobCard with `is_manual_override = False`.

---

## Dynamic Filtering UI Verification

1. **Service Category Selection**:
   - Selecting a Service Category dynamically populates the Complaint Type `<select>` options relevant to that category.
2. **Complaint Type Selection**:
   - Selecting a Complaint Type inspects `required_skill`. If a required skill exists, the Assigned Technician dropdown is filtered to display only qualified technicians with the required skill badge.
3. **Manual Override**:
   - Toggling **Show All** (Manual Override) shows all active technicians and renders a visual badge indicating manual override mode.
