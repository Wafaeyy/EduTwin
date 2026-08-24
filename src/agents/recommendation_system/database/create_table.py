"""
One-time setup script: builds the `resources` table from zero in the real
PostgreSQL database (Supabase).

WARNING -- THIS SCRIPT IS DESTRUCTIVE.
It DROPS the existing resources table, permanently deleting every row in it,
and then recreates it empty. Because recommendation_history has a foreign
key pointing at resources.url, CASCADE also drops the history table -- so a
reset wipes learner history too. Re-run create_history_table.py afterwards.
"""

import os
import psycopg2

connection = psycopg2.connect(
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT"),
    dbname=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
)
cursor = connection.cursor()

# CASCADE is required: recommendation_history depends on this table.
cursor.execute("DROP TABLE IF EXISTS resources CASCADE;")
print("Old resources table dropped (and any dependent history table).")

cursor.execute("""
    CREATE TABLE resources (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        description TEXT,
        topic TEXT,
        difficulty TEXT,
        format TEXT,
        duration TEXT
    );
""")
print("New resources table created.")

connection.commit()

cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'resources'
    ORDER BY ordinal_position;
""")
for column_name, data_type, is_nullable in cursor.fetchall():
    print(f"  {column_name:<12} {data_type:<10} nullable={is_nullable}")

cursor.close()
connection.close()
print("\nDone. Table is empty and ready.")
print("NOTE: run create_history_table.py again to rebuild learner history.")