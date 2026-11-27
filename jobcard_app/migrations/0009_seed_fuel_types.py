from django.db import migrations

DEFAULTS = [
    ('petrol', 'Petrol'), ('diesel', 'Diesel'), ('electric', 'Electric'),
    ('hybrid', 'Hybrid'), ('cng', 'CNG'), ('lpg', 'LPG'), ('other', 'Other'),
]

def seed(apps, schema_editor):
    FuelType = apps.get_model('jobcard_app', 'FuelType')
    for code, name in DEFAULTS:
        FuelType.objects.get_or_create(code=code, defaults={'name': name})

class Migration(migrations.Migration):
    dependencies = [('jobcard_app', '0008_fueltype_alter_workshopvehicle_fuel_type')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]