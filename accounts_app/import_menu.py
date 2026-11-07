import csv
from pathlib import Path
import psycopg2  # type: ignore[reportMissingModuleSource]
from datetime import datetime


DB_NAME = "erp_db"
DB_USER = "postgres"
DB_PASS = "Pass@@Azur26%"
DB_HOST = "localhost"
DB_PORT = "5432"
CSV_FILE = Path(__file__).resolve().parent / "menu.csv"


def import_menus():
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )

        cur = conn.cursor()

        with open(CSV_FILE, newline="", encoding="utf-8-sig") as csvfile:

            reader = csv.DictReader(csvfile)

            # Clean CSV headers
            reader.fieldnames = [
                field.strip().lower()
                for field in reader.fieldnames
            ]

            print("CSV Headers:", reader.fieldnames)

            for row in reader:

                # Clean values
                row = {
                    key.strip(): value.strip() if value else None
                    for key, value in row.items()
                }

                menu_id = int(row["id"])
                name = row["name"]
                url = row["url"]

                now = datetime.now()

                sql = """
                    INSERT INTO accounts_app_menu
                    (
                        id,
                        name,
                        url,
                        created_on,
                        updated_on,
                        created_by,
                        updated_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """

                values = (
                    menu_id,
                    name,
                    url,
                    now,
                    now,
                    None,
                    None
                )

                cur.execute(sql, values)

                print(f"Imported: {menu_id} - {name}")

        conn.commit()

        print("================================")
        print("✅ Menu import completed successfully.")
        print("================================")

    except Exception as e:
        if conn:
            conn.rollback()

        print("❌ Error:", e)

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


if __name__ == "__main__":
    import_menus()