import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounts.settings')
django.setup()

from django.db import connection
c = connection.cursor()

cols = [
    "ALTER TABLE jobcard_app_estimate ADD COLUMN IF NOT EXISTS vehicle_id bigint NULL REFERENCES fleet_app_vehicle(id) ON DELETE RESTRICT",
    "ALTER TABLE jobcard_app_estimate ADD COLUMN IF NOT EXISTS advisor_id bigint NULL REFERENCES fleet_app_staff(id) ON DELETE SET NULL",
    "ALTER TABLE jobcard_app_estimate ADD COLUMN IF NOT EXISTS valid_until date NULL",
    "ALTER TABLE jobcard_app_estimate ADD COLUMN IF NOT EXISTS tax_percent numeric(5,2) DEFAULT 0",
    "ALTER TABLE jobcard_app_estimate ADD COLUMN IF NOT EXISTS discount numeric(10,2) DEFAULT 0",
    "ALTER TABLE jobcard_app_estimate ADD COLUMN IF NOT EXISTS terms varchar(200) DEFAULT ''",
    "ALTER TABLE jobcard_app_estimate ADD COLUMN IF NOT EXISTS notes text DEFAULT ''",
]

for sql in cols:
    try:
        c.execute(sql)
        print("OK:", sql[50:80])
    except Exception as e:
        print("SKIP:", e)

print("All done!")