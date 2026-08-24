"""
The resource catalog: the single gatekeeper between the pipeline and stored
resources.

Loads from the real PostgreSQL database (Supabase) on first use. If the
database cannot be reached, falls back to SEED_RESOURCES in memory so the
program still runs -- degraded, but honest about it.

SEED_RESOURCES is deliberately EMPTY. The engine now sources everything from
the real database, populated by real internet discovery. The seeding
mechanism is kept intact so a starting catalog can be dropped back in later
(e.g. a curated list from the team) without any code change.

Nothing outside this module should touch the resource list directly. Use
get_all_resources(), retrieve_from_database(), or add_resources().
"""

from database.persistence import load_resources, save_resources, count_resources


# Deliberately empty -- see module docstring. Add Resource objects here to
# pre-populate an empty database on first run.
SEED_RESOURCES = []


# Module-level state. Filled in on first use, then reused for the rest of the run.
_resource_cache = None
_database_available = False


def _load_cache():
    """Fills the cache. Called automatically on first use; does nothing after."""
    global _resource_cache, _database_available

    if _resource_cache is not None:
        return

    try:
        existing_count = count_resources()

        if existing_count == 0 and SEED_RESOURCES:
            print(f"[resource store] Database is empty; seeding {len(SEED_RESOURCES)} starting resources.")
            save_resources(SEED_RESOURCES)

        _resource_cache = load_resources()
        _database_available = True

        if _resource_cache:
            print(f"[resource store] Loaded {len(_resource_cache)} resource(s) from PostgreSQL.")
        else:
            print("[resource store] Catalog is empty; retrieval will fall through to internet discovery.")

    except Exception as error:
        print(f"[resource store] Database unavailable ({error}); using the in-memory seed list instead.")
        _resource_cache = list(SEED_RESOURCES)
        _database_available = False


def get_all_resources():
    """Returns every known resource. The only way to read the catalog."""
    _load_cache()
    return _resource_cache


def add_resources(resources):
    """Adds newly discovered resources to the catalog.

    Saves them to PostgreSQL (duplicate urls are skipped by the database) and
    adds them to the in-memory cache so the rest of this run sees them
    immediately. Returns the number genuinely new to the database.
    """
    _load_cache()

    if not resources:
        return 0

    saved_count = 0
    if _database_available:
        try:
            saved_count = save_resources(resources)
        except Exception as error:
            print(f"[resource store] Could not save discovered resources ({error}); keeping them in memory only.")

    known_urls = {resource.url for resource in _resource_cache}
    for resource in resources:
        if resource.url not in known_urls:
            _resource_cache.append(resource)
            known_urls.add(resource.url)

    return saved_count


def retrieve_from_database(search_requirement):
    """Filters the catalog by topic and level. None means 'no constraint'."""
    matches = []
    for resource in get_all_resources():
        topic_matches = (
            search_requirement["topic"] is None
            or resource.topic == search_requirement["topic"]
        )
        level_matches = (
            search_requirement["level"] is None
            or resource.difficulty == search_requirement["level"]
        )
        if topic_matches and level_matches:
            matches.append(resource)
    return matches