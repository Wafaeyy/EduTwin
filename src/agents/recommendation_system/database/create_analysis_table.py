"""
One-time setup script: creates the resource_analysis table.

Caches deep content analysis (video chapters, article sections) so a given
resource is only ever sent to Gemini once. Every learner benefits from an
analysis any learner paid for -- the same shared-catalog logic used for
resources.

Design notes:
  - resource_url is the PRIMARY KEY: one analysis per resource, instant
    lookup, and repeat analyses overwrite rather than duplicate.
  - analysis_json stores the whole result as text. Videos return chapters and
    articles return sections -- different shapes -- so forcing them into
    columns would mean a table that fits neither well.
  - NO foreign key to resources. The button may analyze a url the learner
    pasted in that is not in the catalog, and an analysis stays valid even if
    the resource later leaves the catalog.
  - analyzed_at exists so a staleness policy can be added later. Nothing
    expires today: a cached analysis is served forever.

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
    CREATE TABLE IF NOT EXISTS resource_analysis (
        resource_url TEXT PRIMARY KEY,
        analysis_type TEXT NOT NULL CHECK (analysis_type IN ('video', 'article')),
        analysis_json TEXT NOT NULL,
        analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
""")
print("resource_analysis table created (or already existed).")

connection.commit()

cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'resource_analysis'
    ORDER BY ordinal_position;
""")
print("\nColumns:")
for column_name, data_type, is_nullable in cursor.fetchall():
    print(f"  {column_name:<15} {data_type:<26} nullable={is_nullable}")

cursor.close()
connection.close()
print("\nDone.")