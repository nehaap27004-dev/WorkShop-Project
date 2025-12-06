import csv
import psycopg2
from datetime import datetime


DB_NAME = "rabwafahoud"
DB_USER = "postgres"
DB_PASS = "shnd6775"
DB_HOST = "localhost"
DB_PORT = "5432"
# Database connection
# DB_HOST = 'Rbizgroup-4102.postgres.pythonanywhere-services.com'
# DB_NAME = 'rabwafahoud'
# DB_USER = 'super'
# DB_PASS = 'pass@12345678'
# DB_PORT = '14102'

CSV_FILE = "ledger.csv"

def import_ledgers():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()

        with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            print("CSV Headers:", reader.fieldnames)

            for row in reader:
                ledger_id = int(row["id"])
                ledger_name = row["ledger_name"].strip()
                groups_id = row.get("groups_id") or None
                if groups_id:
                    groups_id = int(groups_id)

                now = datetime.now()

                cur.execute("""
                    INSERT INTO accounts_app_ledgercreation 
                        (id, ledger_name, groups_id, opening_balance, types, remark, "isDefault", created_on, updated_on)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (
                    ledger_id,
                    ledger_name,
                    groups_id,
                    0.00,   # opening_balance default
                    None,   # types
                    None,   # remark
                    False,  # isDefault
                    datetime.now(),
                    datetime.now()
                ))


        conn.commit()
        cur.close()
        conn.close()
        print("✅ Ledger import completed successfully.")

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    import_ledgers()
