from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname='public'
        AND tablename LIKE 'jobcard_app_%';
    """)

    tables = [row[0] for row in cursor.fetchall()]

    print("Tables found:", tables)

    for table in tables:
        print("Dropping:", table)
        cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')

    cursor.execute("""
        DELETE FROM django_migrations
        WHERE app='jobcard_app';
    """)

print("Jobcard app reset completed.")