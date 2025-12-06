import psycopg2
import csv
import datetime
# Database connection details
DB_NAME = "rabwafahoud"
DB_USER = "postgres"
DB_PASS = "shnd6775"
DB_HOST = "localhost"
DB_PORT = "5432"
# DB_HOST = 'Rbizgroup-4102.postgres.pythonanywhere-services.com'
# DB_NAME = 'rabwafahoud'
# DB_USER = 'super'
# DB_PASS = 'pass@12345678'
# DB_PORT = '14102'

# CSV file path
CSV_FILE = "Accounts.csv"

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
)
cur = conn.cursor()

with open(CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("CSV headers:", reader.fieldnames)  # Debug: see your actual headers

    for row in reader:
        # Convert isDefault from string to boolean
        is_default = row["isDefault"].strip().lower() in ("true", "1", "yes")

        # Handle nulls
        group_id = row.get("groupId_id") or None
        nature_of_group = row.get("natureOfGroup") or None

        # Convert to int if provided
        if nature_of_group not in (None, ""):
            nature_of_group = int(nature_of_group)

        # Current timestamp
        now = datetime.datetime.now()

        cur.execute("""
            INSERT INTO accounts_app_groups 
            (id, "groupName", "groupId_id", "isDefault", "natureOfGroup", created_on, updated_on)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            row["id"],
            row["groupName"],
            group_id,
            is_default,
            nature_of_group,
            now,
            now
        ))
# Commit and close
conn.commit()
cur.close()
conn.close()

print("✅ Data imported successfully!")
