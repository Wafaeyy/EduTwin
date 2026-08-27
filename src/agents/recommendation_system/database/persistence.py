"""
The ONLY module in this project that talks to the real PostgreSQL database
(Supabase). Everything else goes through these functions.

Four tables:
  resources               -- the catalog of known educational resources
  recommendation_history  -- which resources each learner has already seen
  resource_analysis       -- cached deep content analysis, shared by all learners
  extraction_cache        -- cached LLM extractions, keyed by input text

Install: pip install psycopg2-binary

Requires these environment variables to be set:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os
import json
import hashlib

import psycopg2
from psycopg2.extras import RealDictCursor

from src.agents.recommendation_system.models.resource import Resource


# The columns we read and write, in a fixed order. Deliberately excludes `id`,
# which Postgres fills in itself and which a Resource object does not have.
RESOURCE_COLUMNS = ["title", "url", "description", "topic", "difficulty", "format", "duration"]

EVENT_SHOWN = "shown"
EVENT_REJECTED = "rejected"

MAX_FAILED_CHECKS = 5


def get_connection():
    """Opens a fresh connection to the Supabase Postgres database.

    Uses five separate arguments rather than one combined connection-string
    URL, because the real password contains characters (@, [, ]) that break
    URL parsing when embedded in a single string.
    """
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

def _insert_resource(cursor, resource):
    """Inserts ONE resource using a cursor the caller already opened.

    Private helper (the leading underscore is the Python convention for
    "internal use"). It does not open, commit, or close anything -- that is
    the caller's job. This is what lets save_resources() insert many
    resources over a single connection.

    Returns True if a new row was actually created, False if the url was
    already present and the insert was skipped.
    """
    cursor.execute(
        """
        INSERT INTO resources (title, url, description, topic, difficulty, format, duration)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
        """,
        (
            resource.title,
            resource.url,
            resource.description,
            resource.topic,
            resource.difficulty,
            resource.format,
            resource.duration,
        ),
    )
    return cursor.rowcount == 1


def save_resource(resource):
    """Saves a single resource. Returns True if newly stored, False if it was
    already in the database."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        was_inserted = _insert_resource(cursor, resource)
        connection.commit()
        cursor.close()
        return was_inserted
    finally:
        connection.close()


def save_resources(resources):
    """Saves many resources over ONE connection.

    Returns the number of resources that were genuinely new. Resources whose
    url is already in the database are skipped silently, not counted, and
    never cause an error.
    """
    if not resources:
        return 0

    connection = get_connection()
    try:
        cursor = connection.cursor()
        inserted_count = 0
        for resource in resources:
            if _insert_resource(cursor, resource):
                inserted_count += 1
        connection.commit()
        cursor.close()
        return inserted_count
    finally:
        connection.close()


def load_resources():
    """Loads every resource from the database as real Resource objects."""
    connection = get_connection()
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        column_list = ", ".join(RESOURCE_COLUMNS)
        cursor.execute(f"SELECT {column_list} FROM resources ORDER BY id;")
        rows = cursor.fetchall()
        cursor.close()
    finally:
        connection.close()

    return [Resource.from_dict(dict(row)) for row in rows]


def count_resources():
    """Returns how many resources are currently stored. Cheaper than loading
    them all -- used to decide whether the table needs seeding."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM resources;")
        total = cursor.fetchone()[0]
        cursor.close()
        return total
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Recommendation history
# ---------------------------------------------------------------------------

def record_shown(twin_id, resource_urls):
    """Records that these resources were shown to this learner.

    Never downgrades an existing 'rejected' row back to 'shown' -- a
    rejection is a deliberate learner decision and must survive being
    re-recommended. The WHERE clause on the conflict branch enforces that.

    Returns the number of rows inserted or updated.
    """
    if not twin_id or not resource_urls:
        return 0

    connection = get_connection()
    try:
        cursor = connection.cursor()
        affected = 0
        for url in resource_urls:
            cursor.execute(
                """
                INSERT INTO recommendation_history (twin_id, resource_url, event)
                VALUES (%s, %s, %s)
                ON CONFLICT (twin_id, resource_url) DO UPDATE
                    SET updated_at = NOW()
                    WHERE recommendation_history.event = %s;
                """,
                (str(twin_id), url, EVENT_SHOWN, EVENT_SHOWN),
            )
            affected += cursor.rowcount
        connection.commit()
        cursor.close()
        return affected
    finally:
        connection.close()


def record_rejected(twin_id, resource_urls):
    """Records that this learner rejected these resources.

    Always wins over an existing 'shown' row: rejection is the stronger
    signal, so there is no guard here.

    Returns the number of rows inserted or updated.
    """
    if not twin_id or not resource_urls:
        return 0

    connection = get_connection()
    try:
        cursor = connection.cursor()
        affected = 0
        for url in resource_urls:
            cursor.execute(
                """
                INSERT INTO recommendation_history (twin_id, resource_url, event)
                VALUES (%s, %s, %s)
                ON CONFLICT (twin_id, resource_url) DO UPDATE
                    SET event = EXCLUDED.event,
                        updated_at = NOW();
                """,
                (str(twin_id), url, EVENT_REJECTED),
            )
            affected += cursor.rowcount
        connection.commit()
        cursor.close()
        return affected
    finally:
        connection.close()


def get_seen_urls(twin_id, events=None):
    """Returns the set of resource urls this learner has already encountered.

    events=None          -> everything (both shown and rejected)
    events=['rejected']  -> only what they actively refused

    Returns a set, not a list: membership checks are instant regardless of
    size, which matters because retrieval checks every candidate against it.
    """
    if not twin_id:
        return set()

    connection = get_connection()
    try:
        cursor = connection.cursor()
        if events:
            cursor.execute(
                "SELECT resource_url FROM recommendation_history WHERE twin_id = %s AND event = ANY(%s);",
                (str(twin_id), list(events)),
            )
        else:
            cursor.execute(
                "SELECT resource_url FROM recommendation_history WHERE twin_id = %s;",
                (str(twin_id),),
            )
        rows = cursor.fetchall()
        cursor.close()
        return {row[0] for row in rows}
    finally:
        connection.close()


def clear_history(twin_id):
    """Deletes all history for one learner. Useful for testing and for a
    learner-facing 'start fresh' option. Returns rows deleted."""
    if not twin_id:
        return 0

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM recommendation_history WHERE twin_id = %s;", (str(twin_id),))
        deleted = cursor.rowcount
        connection.commit()
        cursor.close()
        return deleted
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Content analysis cache
# ---------------------------------------------------------------------------

def save_analysis(resource_url, analysis_type, analysis):
    """Stores one content analysis so it never needs regenerating.

    Only SUCCESSFUL analyses should be passed here -- caching a failure would
    freeze a temporary Gemini outage permanently, and the resource could then
    never be analyzed again.
    """
    if not resource_url or not analysis:
        return False

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO resource_analysis (resource_url, analysis_type, analysis_json)
            VALUES (%s, %s, %s)
            ON CONFLICT (resource_url) DO UPDATE
                SET analysis_type = EXCLUDED.analysis_type,
                    analysis_json = EXCLUDED.analysis_json,
                    analyzed_at = NOW();
            """,
            (resource_url, analysis_type, json.dumps(analysis)),
        )
        connection.commit()
        cursor.close()
        return True
    finally:
        connection.close()


def load_analysis(resource_url):
    """Returns a stored analysis, or None if this resource has never been
    analyzed. A stored analysis is served regardless of age."""
    if not resource_url:
        return None

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT analysis_json FROM resource_analysis WHERE resource_url = %s;",
            (resource_url,),
        )
        row = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()

    if row is None:
        return None

    try:
        return json.loads(row[0])
    except json.JSONDecodeError as error:
        print(f"[analysis cache] Stored analysis for {resource_url} is not valid JSON ({error}); ignoring it.")
        return None


def count_analyses():
    """How many resources have a cached analysis."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM resource_analysis;")
        total = cursor.fetchone()[0]
        cursor.close()
        return total
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Extraction cache
# ---------------------------------------------------------------------------

def hash_input(text):
    """Stable short key for a piece of input text.

    A briefing can be thousands of characters, which is far too long for a
    primary key, so we store a hash of it instead.
    """
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def save_extraction(text, extraction_kind, extracted):
    """Caches one extraction result, keyed by a hash of its input.

    The same briefing or the same learner message always produces the same
    answer, so there is no reason to pay Gemini for it twice. This also means
    a repeat request survives an API outage -- during development Gemini
    returned 429 and 503 on separate occasions, and with an empty learner
    state every recommendation scored 0/100.
    """
    if not text or extracted is None:
        return False

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO extraction_cache (input_hash, extraction_kind, extracted_json)
            VALUES (%s, %s, %s)
            ON CONFLICT (input_hash) DO UPDATE
                SET extracted_json = EXCLUDED.extracted_json,
                    created_at = NOW();
            """,
            (hash_input(text), extraction_kind, json.dumps(extracted)),
        )
        connection.commit()
        cursor.close()
        return True
    finally:
        connection.close()


def load_extraction(text):
    """Returns a cached extraction for this exact input, or None."""
    if not text:
        return None

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT extracted_json FROM extraction_cache WHERE input_hash = %s;",
            (hash_input(text),),
        )
        row = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()

    if row is None:
        return None

    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None


def count_extractions():
    """How many extractions are currently cached."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM extraction_cache;")
        total = cursor.fetchone()[0]
        cursor.close()
        return total
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Re-verification tracking
# ---------------------------------------------------------------------------

def get_resources_due_for_verification(max_age_days=30, limit=100):
    """Returns (url, failed_checks) for resources that need re-checking.

    Due means: never re-verified since the migration, or last verified longer
    ago than max_age_days. Resources with existing strikes are returned first,
    since they are the ones closest to being dropped.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT url, failed_checks
            FROM resources
            WHERE last_verified_at IS NULL
               OR last_verified_at < NOW() - (%s * INTERVAL '1 day')
            ORDER BY failed_checks DESC, last_verified_at ASC NULLS FIRST
            LIMIT %s;
            """,
            (max_age_days, limit),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [(row[0], row[1]) for row in rows]
    finally:
        connection.close()


def mark_verified(resource_urls):
    """Records that these urls are alive. Resets failed_checks to 0 --
    strikes are CONSECUTIVE, so any success wipes the slate clean."""
    if not resource_urls:
        return 0

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE resources
            SET last_verified_at = NOW(), failed_checks = 0
            WHERE url = ANY(%s);
            """,
            (list(resource_urls),),
        )
        updated = cursor.rowcount
        connection.commit()
        cursor.close()
        return updated
    finally:
        connection.close()


def mark_failed(resource_urls):
    """Increments the strike count for urls that did not respond.

    Deliberately does NOT touch last_verified_at: that field means "last
    confirmed alive", and a failure confirms nothing.
    """
    if not resource_urls:
        return 0

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE resources
            SET failed_checks = failed_checks + 1
            WHERE url = ANY(%s);
            """,
            (list(resource_urls),),
        )
        updated = cursor.rowcount
        connection.commit()
        cursor.close()
        return updated
    finally:
        connection.close()


def delete_dead_resources(max_failed=MAX_FAILED_CHECKS):
    """Removes resources that have failed max_failed times IN A ROW.

    NOTE: recommendation_history has ON DELETE CASCADE on resource_url, so
    this also erases every learner's history for these resources -- including
    rejections. If a deleted resource is rediscovered later, a learner who
    rejected it could see it again.

    Returns the list of deleted urls.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM resources WHERE failed_checks >= %s RETURNING url;",
            (max_failed,),
        )
        deleted = [row[0] for row in cursor.fetchall()]
        connection.commit()
        cursor.close()
        return deleted
    finally:
        connection.close()


def get_verification_summary():
    """Counts by strike level, for reporting."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                COUNT(*),
                COUNT(*) FILTER (WHERE last_verified_at IS NULL),
                COUNT(*) FILTER (WHERE failed_checks > 0),
                COALESCE(MAX(failed_checks), 0)
            FROM resources;
        """)
        total, never, failing, worst = cursor.fetchone()
        cursor.close()
        return {"total": total, "never_verified": never, "with_strikes": failing, "worst_strikes": worst}
    finally:
        connection.close()


if __name__ == "__main__":
    print("=== Database contents ===")
    print(f"  {count_resources()} resource(s)")
    print(f"  {count_analyses()} cached analysis/analyses")
    print(f"  {count_extractions()} cached extraction(s)")

    print("\n=== Resources ===")
    for resource in load_resources():
        print(f"  {str(resource.format):<16} | {resource.url}")