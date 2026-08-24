"""
The Verification Gate: structural checks, domain policy, and real network
checks -- in that order, cheapest first.

Network checks run in PARALLEL. Verifying 15 urls one at a time means adding
up 15 waits (two minutes in real runs, since a dead link burns the full
timeout). Sending them together means waiting once, for the slowest.

Threads are the right tool here specifically because this is network waiting,
not calculation: Python releases the GIL while waiting on a socket, so the
other threads genuinely run.

Install: pip install requests
"""

from concurrent.futures import ThreadPoolExecutor

import requests

from verification.domain_policy import is_blocked, blocked_reason

REQUEST_TIMEOUT_SECONDS = 5

# How many urls to check simultaneously. Threads are not free (each costs
# memory) and too many at once can look like an attack to a server, so this
# is a deliberate ceiling rather than "as many as there are urls".
MAX_PARALLEL_CHECKS = 10

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EduTwinRecommendationEngine/1.0"
}


def verify_url_reachable(url):
    """One real network request. Returns True if the page responds."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers=REQUEST_HEADERS)
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False


def check_free_gates(resource, verbose=False):
    """The two checks that cost nothing: structure and domain policy.

    Returns True if the resource is still a candidate, False if it is already
    rejected. Running these first means we never spend a network request on a
    resource we were always going to refuse.
    """
    if not (resource.title and resource.url and resource.topic):
        if verbose:
            print(f"[verification] Rejected (missing fields): {resource.title!r}")
        return False

    if is_blocked(resource.url):
        if verbose:
            print(f"[verification] Rejected (blocked domain '{blocked_reason(resource.url)}'): {resource.url}")
        return False

    return True


def verify_resource(resource, verbose=False):
    """Verifies ONE resource, all three gates, sequentially.

    Kept for single-resource checks and for anything that imports it. Batch
    work should use verify_resources(), which parallelises the network gate.
    """
    if not check_free_gates(resource, verbose=verbose):
        return False

    if not verify_url_reachable(resource.url):
        if verbose:
            print(f"[verification] Rejected (unreachable): {resource.url}")
        return False

    return True


def verify_resources(resources, verbose=False):
    """Verifies a whole list, checking urls in parallel.

    Order is preserved: results are reassembled by their original position,
    not by whichever thread finished first. Ranking depends on order (ties
    keep their original placement), so this matters.
    """
    if not resources:
        return []

    # Free gates first, single-threaded -- they cost nothing and shrink the
    # list before we open any connections.
    candidates = [resource for resource in resources if check_free_gates(resource, verbose=verbose)]

    if not candidates:
        return []

    # One network check per surviving candidate, all at once.
    worker_count = min(MAX_PARALLEL_CHECKS, len(candidates))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        reachable_flags = list(pool.map(verify_url_reachable, [c.url for c in candidates]))

    verified = []
    for resource, is_reachable in zip(candidates, reachable_flags):
        if is_reachable:
            verified.append(resource)
        elif verbose:
            print(f"[verification] Rejected (unreachable): {resource.url}")

    return verified


if __name__ == "__main__":
    import time
    from models.resource import Resource

    TEST_URLS = [
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://en.wikipedia.org/wiki/Data_structure",
        "https://developers.google.com/machine-learning/crash-course",
        "https://www.python.org",
        "https://en.wikipedia.org/wiki/This_page_definitely_does_not_exist_xyz123",
        "https://this-domain-definitely-does-not-exist-xyz789.com",
        "https://www.wikipedia.org",
        "https://docs.python.org/3/",
    ]

    test_resources = [
        Resource(
            title=f"Test resource {index}",
            url=url,
            description="A test resource.",
            topic="machine learning",
            difficulty=None,
            format=None,
            duration=None,
        )
        for index, url in enumerate(TEST_URLS, start=1)
    ]

    print(f"Verifying {len(test_resources)} urls...\n")

    print("=== SEQUENTIAL (the old way) ===")
    start = time.time()
    sequential = [r for r in test_resources if verify_resource(r)]
    sequential_seconds = time.time() - start
    print(f"{len(sequential)} verified in {sequential_seconds:.1f}s")

    print("\n=== PARALLEL (the new way) ===")
    start = time.time()
    parallel = verify_resources(test_resources, verbose=True)
    parallel_seconds = time.time() - start
    print(f"{len(parallel)} verified in {parallel_seconds:.1f}s")

    print(f"\nSpeedup: {sequential_seconds / parallel_seconds:.1f}x faster")
    print(f"Same results: {[r.url for r in sequential] == [r.url for r in parallel]}  <- should be True")