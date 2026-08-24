"""
One-time setup script: creates the recommendation_history table.

Records which resources have already been shown to (or rejected by) a
learner, so the engine never recommends the same thing twice. This is what
makes the engine stateful -- the core claim of the project's research
question, versus a stateless assistant that repeats itself.

Design notes:
  - Composite primary key (twin_id, resource_url): one row per learner per
    resource, ever. A learner cannot simultaneously have "shown" and
    "rejected" for the same resource; rejecting UPDATES the existing row.
  - Foreign key on resource_url (not id): SERIAL ids are reassigned whenever
    the resources table is rebuilt, which would silently corrupt history.
    URLs are stable, and resources.url is UNIQUE, so it is a valid FK target.
  - ON DELETE CASCADE: deleting a resource removes its history rows.

Safe to re-run. Creates only; never drops anything.
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
    CREATE TABLE IF NOT EXISTS recommendation_history (
        twin_id TEXT NOT NULL,
        resource_url TEXT NOT NULL,
        event TEXT NOT NULL CHECK (event IN ('shown', 'rejected')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        PRIMARY KEY (twin_id, resource_url),

        FOREIGN KEY (resource_url)
            REFERENCES resources (url)
            ON DELETE CASCADE
    );
""")
print("recommendation_history table created (or already existed).")

# Speeds up the one query this table exists for: "what has this learner seen?"
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_history_twin
    ON recommendation_history (twin_id);
""")
print("Index on twin_id created (or already existed).")

connection.commit()

cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'recommendation_history'
    ORDER BY ordinal_position;
""")
print("\nColumns:")
for column_name, data_type, is_nullable in cursor.fetchall():
    print(f"  {column_name:<14} {data_type:<26} nullable={is_nullable}")

cursor.close()
connection.close()
print("\nDone.")