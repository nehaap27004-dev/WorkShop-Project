import psycopg2
import csv
import datetime

# Database connection details
DB_NAME = "erp_db"
DB_USER = "postgres"
DB_PASS = "Admin"
DB_HOST = "localhost"
DB_PORT = "5432"

# CSV file path
CSV_FILE = "fleet_app/vouchers.csv"

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT
)

cur = conn.cursor()

with open(CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    print("CSV headers:", reader.fieldnames)

    for row in reader:

        # Convert ID to integer
        voucher_id = int(row["id"])

        # VoucherType
        voucher_type = row["VoucherType"].strip()

        # CSV VoucherNo -> Database VoucherName
        voucher_name = row["VoucherName"].strip()

        # Handle Prefix
        prefix = row.get("Prefix")

        if prefix:
            prefix = prefix.strip()

        if prefix in ("", "None", "NULL", "null"):
            prefix = None

        # Handle Suffix
        suffix = row.get("Suffix")

        if suffix:
            suffix = suffix.strip()

        if suffix in ("", "None", "NULL", "null"):
            suffix = None

        # Convert MinLength and StartingNo to integers
        min_length = int(row["MinLength"])
        starting_no = int(row["StartingNo"])

        # Current timestamp
        now = datetime.datetime.now()

        cur.execute("""
            INSERT INTO fleet_app_vouchers
            (
                id,
                "VoucherType",
                "VoucherName",
                "Prefix",
                "Suffix",
                "MinLength",
                "StartingNo",
                ledger_id,
                "isDefault",
                created_on,
                updated_on
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

            ON CONFLICT (id) DO UPDATE SET
                "VoucherType" = EXCLUDED."VoucherType",
                "VoucherName" = EXCLUDED."VoucherName",
                "Prefix" = EXCLUDED."Prefix",
                "Suffix" = EXCLUDED."Suffix",
                "MinLength" = EXCLUDED."MinLength",
                "StartingNo" = EXCLUDED."StartingNo",
                updated_on = EXCLUDED.updated_on;
        """, (
            voucher_id,
            voucher_type,
            voucher_name,
            prefix,
            suffix,
            min_length,
            starting_no,
            None,       # ledger_id
            False,      # isDefault
            now,
            now
        ))

# Reset PostgreSQL ID sequence
cur.execute("""
    SELECT setval(
        pg_get_serial_sequence('fleet_app_vouchers', 'id'),
        COALESCE((SELECT MAX(id) FROM fleet_app_vouchers), 1),
        true
    );
""")

# Commit and close
conn.commit()

cur.close()
conn.close()

print("✅ Voucher data imported successfully!")