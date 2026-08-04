"""
The Verification Gate: decides whether a candidate resource is well-formed
enough to be recommended.

PLACEHOLDER: only checks required fields exist and aren't empty. Real URL
reachability checks (via the `requests` library) will be added when this
runs on a machine with normal internet access.
"""


def verify_resource(resource):
    """
    Args:
        resource (Resource): a candidate resource.

    Returns:
        bool: True if it passes our current checks.
    """
    has_title = bool(resource.title)
    has_url = bool(resource.url)
    has_topic = bool(resource.topic)

    return has_title and has_url and has_topic


def verify_resources(resources):
    """
    Args:
        resources (list): candidate Resource objects.

    Returns:
        list: only the resources that passed verification.
    """
    verified = []

    for resource in resources:
        if verify_resource(resource):
            verified.append(resource)

    return verified