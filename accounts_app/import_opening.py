import csv
import os
import sys
import django
import psycopg2
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounts.settings')
django.setup()

from django.conf import settings

DB_NAME = "rabwafahoud"
DB_USER = "postgres"
DB_PASS = "shnd6775"
DB_HOST = "localhost"
DB_PORT = "5432"

CSV_FILE = "billwise_opening.csv"

def import_billwise_opening():
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
        cur = conn.cursor()

        fy_date = datetime.strptime(settings.FINYEAR, "%Y-%m-%d").date()
        fy_year = fy_date.year
        imported_at = datetime.now()

        inserted = 0
        skipped = 0

        with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            print("CSV Headers:", reader.fieldnames)

            for row in reader:
                ledger_id = int(row["ledger_id"])
                voucher_type_id = int(row["voucherType_id"])
                inv_no = row["InvNo"].strip()
                inv_date = row["InvDate"]
                inv_amount = float(row["InvAmount"])
                inv_balance = float(row["InvBalance"])
                dr_cr = row["dr_cr"].strip().upper()
                is_closed = row.get("IsClosed", "False").lower() == "true"

                if inv_balance <= 0:
                    continue

                is_cleared = True if is_closed or inv_balance <= 0 else False

                debit = inv_balance if dr_cr == "DR" else 0
                credit = inv_balance if dr_cr == "CR" else 0

                cur.execute("""
                    INSERT INTO accounts_app_billwiseopening
                    (ledger_id,"voucherType_id","InvNo","InvDate","InvAmount","InvBalance","dr_cr","IsCleared","IsClosed","CreatedOn","UpdatedOn")
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (ledger_id,"InvNo","voucherType_id") DO NOTHING
                    RETURNING id;
                """, (
                    ledger_id,
                    voucher_type_id,
                    inv_no,
                    inv_date,
                    inv_amount,
                    inv_balance,
                    dr_cr,
                    is_cleared,
                    is_closed,
                    imported_at,
                    imported_at
                ))

                result = cur.fetchone()
                if not result:
                    skipped += 1
                    continue

                bill_id = result[0]

                cur.execute("""
                    INSERT INTO accounts_app_ledgerposting
                    ("date","VoucherType_id","VoucherNo","ledger_id","debit","credit",
                     "RefVoucherNo","RefVoucherType_id","CostCenter_id","FY",
                     "IsDeleted","created_on","updated_on","created_by","updated_by")
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                """, (
                    fy_date,
                    voucher_type_id,
                    bill_id,
                    ledger_id,
                    debit,
                    credit,
                    None,
                    None,
                    None,
                    fy_year,
                    False,
                    imported_at,
                    imported_at,
                    None,
                    None
                ))

                inserted += 1

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Import completed | Inserted: {inserted} | Skipped (duplicates): {skipped}")

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    import_billwise_opening()
