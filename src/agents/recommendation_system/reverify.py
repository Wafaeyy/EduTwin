"""
Periodic catalog audit: re-checks stored resources and drops dead links.

Run this on a schedule (weekly is reasonable), NOT during a recommendation
request -- a learner should never wait while the catalog is audited.

    py reverify.py

A resource is only deleted after MAX_FAILED_CHECKS CONSECUTIVE failures, so a
temporary outage costs a strike, not the resource. Any single success resets
the count to zero.

SAFETY NET: if most of the batch fails at once, that is almost certainly this
machine's network rather than that many simultaneously dead links, so nothing
is recorded at all. Two total network failures happened during development;
without this guard, either one would have wiped the whole catalog.
"""

from src.agents.recommendation_system.verification.verifier import verify_url_reachable
from src.agents.recommendation_system.database.persistence import (
    get_resources_due_for_verification,
    mark_verified,
    mark_failed,
    delete_dead_resources,
    get_verification_summary,
    MAX_FAILED_CHECKS,
)
from concurrent.futures import ThreadPoolExecutor

MAX_AGE_DAYS = 30
BATCH_LIMIT = 100
MAX_PARALLEL_CHECKS = 10

# If more than this fraction of the batch fails, assume the problem is local.
SUSPICIOUS_FAILURE_RATE = 0.7


def reverify_catalog(max_age_days=MAX_AGE_DAYS, limit=BATCH_LIMIT, dry_run=False):
    """Re-checks due resources, records the outcome, and deletes dead ones."""
    summary_before = get_verification_summary()
    print(f"Catalog: {summary_before['total']} resource(s), "
          f"{summary_before['never_verified']} never re-verified, "
          f"{summary_before['with_strikes']} currently carrying strikes "
          f"(worst: {summary_before['worst_strikes']}/{MAX_FAILED_CHECKS}).\n")

    due = get_resources_due_for_verification(max_age_days=max_age_days, limit=limit)
    if not due:
        print(f"Nothing is due for re-verification (threshold: {max_age_days} days).")
        return

    print(f"Re-checking {len(due)} resource(s)...\n")
    urls = [url for url, _ in due]
    strikes_by_url = dict(due)

    worker_count = min(MAX_PARALLEL_CHECKS, len(urls))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        results = list(pool.map(verify_url_reachable, urls))

    alive = [url for url, ok in zip(urls, results) if ok]
    dead = [url for url, ok in zip(urls, results) if not ok]

    failure_rate = len(dead) / len(urls)
    print(f"{len(alive)} alive, {len(dead)} unreachable ({failure_rate:.0%} failure rate).\n")

    # Safety net: a very high failure rate means the network, not the links.
    if failure_rate > SUSPICIOUS_FAILURE_RATE and len(urls) >= 5:
        print(f"ABORTED: {failure_rate:.0%} of the batch failed, which almost certainly means")
        print("this machine's network rather than that many dead links.")
        print("Nothing was recorded. Check your connection and run again.")
        return

    if dry_run:
        print("DRY RUN -- nothing written. Would have recorded:")
        for url in dead:
            current = strikes_by_url.get(url, 0)
            fate = "DELETE" if current + 1 >= MAX_FAILED_CHECKS else f"strike {current + 1}/{MAX_FAILED_CHECKS}"
            print(f"  {fate:<22} {url}")
        return

    if alive:
        mark_verified(alive)
        print(f"Marked {len(alive)} resource(s) as verified (strike counts reset).")

    if dead:
        mark_failed(dead)
        print(f"\nRecorded a strike against {len(dead)} resource(s):")
        for url in dead:
            new_count = strikes_by_url.get(url, 0) + 1
            print(f"  {new_count}/{MAX_FAILED_CHECKS}  {url}")

    deleted = delete_dead_resources()
    if deleted:
        print(f"\nDELETED {len(deleted)} resource(s) after {MAX_FAILED_CHECKS} consecutive failures:")
        for url in deleted:
            print(f"  {url}")
        print("\nNote: learner history for these resources was also removed (ON DELETE CASCADE).")
    else:
        print(f"\nNothing reached {MAX_FAILED_CHECKS} strikes; nothing deleted.")

    summary_after = get_verification_summary()
    print(f"\nCatalog now: {summary_after['total']} resource(s), "
          f"{summary_after['with_strikes']} carrying strikes.")


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    # max_age_days=0 forces everything to be due, which is what you want the
    # first time and when testing.
    reverify_catalog(max_age_days=0, dry_run=dry_run)