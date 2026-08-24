"""
One-time migration: adds re-verification tracking to the resources table.

Two new columns:
  last_verified_at  -- when the url was last confirmed reachable. NULL means
                       never checked since this migration, so existing rows
                       become due immediately. That is honest: we know they
                       were alive when discovered, but not that they still are.
  failed_checks     -- CONSECUTIVE failures. Reset to 0 on any success, so a
                       link that works most of the time never accumulates
                       strikes. Only sustained failure counts.

Uses ALTER TABLE, not DROP -- your existing resources are kept.
Safe to re-run: IF NOT EXISTS means a second run does nothing.
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

cursor.execute("""
    ALTER TABLE resources
    ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS failed_checks INTEGER NOT NULL DEFAULT 0;
""")
print("Columns added (or already existed).")

connection.commit()

cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'resources'
    ORDER BY ordinal_position;
""")
print("\nColumns:")
for column_name, data_type, is_nullable in cursor.fetchall():
    print(f"  {column_name:<18} {data_type:<26} nullable={is_nullable}")

cursor.execute("SELECT COUNT(*) FROM resources WHERE last_verified_at IS NULL;")
never_verified = cursor.fetchone()[0]
print(f"\n{never_verified} resource(s) have never been re-verified and are due on the next run.")

cursor.close()
connection.close()
print("\nDone.")