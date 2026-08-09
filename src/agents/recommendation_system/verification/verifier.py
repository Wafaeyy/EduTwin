"""
The Verification Gate: decides whether a candidate resource is well-formed
AND actually reachable before it's allowed to be recommended.

Install requirement (run this once in your terminal):
    pip install requests
"""

import requests

REQUEST_TIMEOUT_SECONDS = 5


def verify_url_reachable(url):
    """
    Actually visits the URL over the network and checks whether it responds
    successfully.

    Args:
        url (str): the URL to check.

    Returns:
        bool: True if the URL responded with a successful status code,
              False if it's broken, times out, or errors out in any way.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EduTwinRecommendationEngine/1.0"}

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers=headers)
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False
    
def verify_resource(resource):
    """
    Checks whether a resource is both well-formed AND actually reachable.

    Args:
        resource (Resource): a candidate resource.

    Returns:
        bool: True if it passes all checks.
    """
    has_title = bool(resource.title)
    has_url = bool(resource.url)
    has_topic = bool(resource.topic)

    if not (has_title and has_url and has_topic):
        return False

    return verify_url_reachable(resource.url)


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