import csv
import psycopg2
from datetime import datetime

# Database credentials
DB_HOST = 'Rbizgroup-4102.postgres.pythonanywhere-services.com'
DB_NAME = 'diamondstone'
DB_USER = 'super'
DB_PASSWORD = 'pass@12345678'
DB_PORT = '14102'

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    port=DB_PORT
)
cur = conn.cursor()

# ❌ Delete existing items first
cur.execute("DELETE FROM item_master_item")
conn.commit()
print("All existing items deleted.")

# CSV import path
csv_file_path = '/home/Rbizgroup/diamond/item_master/items.csv'

# Import from CSV
with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cur.execute("""
            INSERT INTO item_master_item (
                item_name, item_code,
                item_unit_id, item_class,
                purchase_rate, sales_rate,
                is_base_unit, "CrediRateRet", "CreditRateWhol",
                "D1", "IsExpiry", "IsNonInventory",
                "IsProductSerial", "IsSkipPrint",
                "ProfitPerc", "ProfitPercRetCrdt", "ProfitPercWholeCredit",
                "SchemaPerc", "TaxIncludExclud", "TaxIncludPrchs",
                "WholeProfitPerc", "WholeSalePrice", cess,
                "isDeleted", created, updated, "IsBatch", "IsItemBarcode"
            )
            VALUES (
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, (
            row['item_name'], row['item_code'],
            1, "GEN",
            0.00, 0.00,
            True, 0.00, 0.00,
            datetime.now(), False, False,
            False, False,
            0.00, 0.00, 0.00,
            0.00, False, False,
            0.00, 0.00, 0.00,
            False, datetime.now(), datetime.now(), False, False
        ))

conn.commit()
cur.close()
conn.close()

print("Import successful.")
