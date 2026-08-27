"""
One-time setup script: creates the extraction_cache table.

Both extractors (context_extractor and request_extractor) send text to Gemini
and get back a small JSON object. The same briefing or the same learner
message produces the same answer every time, so there is no reason to pay for
it twice.

Caching also removes a real failure mode. During development Gemini returned
429 (quota exhausted) and 503 (overloaded) on separate occasions; with an
empty learner state every recommendation scored 0/100. A cached extraction is
served with no API call at all, so a repeat request survives an outage.

And it closes a reproducibility gap: the same briefing now always yields the
same extraction, which prose extraction alone could not guarantee.

Keyed by a hash of the input text rather than the text itself -- a briefing
can be thousands of characters, which is too long for a primary key.

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
    CREATE TABLE IF NOT EXISTS extraction_cache (
        input_hash       TEXT PRIMARY KEY,
        extraction_kind  TEXT NOT NULL CHECK (extraction_kind IN ('briefing', 'request')),
        extracted_json   TEXT NOT NULL,
        created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
""")
print("extraction_cache table created (or already existed).")

connection.commit()

cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'extraction_cache'
    ORDER BY ordinal_position;
""")
print("\nColumns:")
for column_name, data_type, is_nullable in cursor.fetchall():
    print(f"  {column_name:<18} {data_type:<26} nullable={is_nullable}")

cursor.close()
connection.close()
print("\nDone.")