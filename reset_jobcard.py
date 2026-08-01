from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN (
            SELECT tablename
            FROM pg_tables
            WHERE schemaname='public'
            AND tablename LIKE 'jobcard_app_%'
        )
        LOOP
            EXECUTE 'DROP TABLE IF EXISTS "' || r.tablename || '" CASCADE';
            RAISE NOTICE 'Dropped %', r.tablename;
        END LOOP;

        DELETE FROM django_migrations
        WHERE app='jobcard_app';
    END $$;
    """)

print("Jobcard tables removed.")