"""
Domain policy: which sources are never recommended, and which are trusted.

Deterministic and inspectable -- a plain list, checked with plain string
matching. No LLM involvement, so a rejection can always be explained as
"this domain is on the blocklist" rather than "a model disliked it".

BLOCKED_DOMAINS is the important one. Real discovery runs surfaced pirated
course sites, TikTok discovery pages, and anonymous free-hosting subdomains
alongside genuinely good material -- and the scorer cannot tell them apart,
because quality is not one of its four factors. This list is what keeps
them out.

TRUSTED_DOMAINS does NOT reject anything. It marks known-good educational
sources so they can be preferred later. A domain on neither list is allowed
through unchanged: blocking is deliberate, trust is a bonus, and everything
else is neutral.
"""

# Never recommended. Grouped by reason so the list stays maintainable.
BLOCKED_DOMAINS = [
    # Piracy / unauthorised redistribution of paid material
    "scanlibs.com",
    "libgen.is",
    "libgen.rs",
    "z-lib.org",
    "annas-archive.org",
    "sci-hub.se",
    "coursehero.com",
    "chegg.com",
    "freecoursesite.com",
    "downloadfreecourse.com",
    "tutsgalaxy.com",

    # Social / short-form feeds -- not structured learning resources
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "pinterest.com",
    "x.com",
    "twitter.com",
    "reddit.com",

    # Anonymous free hosting -- no accountability for content
    "netlify.app",
    "vercel.app",
    "blogspot.com",
    "wordpress.com",
    "wixsite.com",
    "weebly.com",
    "github.io",

    # Content farms / low-quality aggregators
    "answers.com",
    "ehow.com",
    "quora.com",
]

# Known-good educational sources. Informational only; never rejects.
TRUSTED_DOMAINS = [
    # Universities and academia
    ".edu",
    ".ac.uk",
    "mit.edu",
    "stanford.edu",
    "arxiv.org",
    "acm.org",
    "ieee.org",

    # Official documentation and vendor learning
    "developers.google.com",
    "learn.microsoft.com",
    "docs.python.org",
    "pytorch.org",
    "tensorflow.org",
    "scikit-learn.org",
    "developer.mozilla.org",

    # Established educational platforms
    "coursera.org",
    "edx.org",
    "khanacademy.org",
    "freecodecamp.org",
    "youtube.com",
    "wikipedia.org",
    "geeksforgeeks.org",
    "w3schools.com",
    "kaggle.com",
    "leetcode.com",
]


def is_blocked(url):
    """True if this url's domain is on the blocklist."""
    if not url:
        return False
    url_lower = url.lower()
    for domain in BLOCKED_DOMAINS:
        if domain in url_lower:
            return True
    return False


def is_trusted(url):
    """True if this url comes from a known-good educational source.

    Informational only -- nothing is rejected for failing this check.
    """
    if not url:
        return False
    url_lower = url.lower()
    for domain in TRUSTED_DOMAINS:
        if domain in url_lower:
            return True
    return False


def blocked_reason(url):
    """Returns the specific blocked domain that matched, for explainability."""
    if not url:
        return None
    url_lower = url.lower()
    for domain in BLOCKED_DOMAINS:
        if domain in url_lower:
            return domain
    return None