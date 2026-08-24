"""
Resource Analysis: infers real difficulty and format from a resource's
actual title, description, and URL. Uses word-boundary regex to avoid
false matches (e.g. "intro" incorrectly matching inside "introducing").

Format inference is deliberately conservative: it returns None rather than
guessing. An unknown format simply scores 0 for format match, which is the
honest outcome -- better than awarding 30 points for an assumption.
"""

import re

DIFFICULTY_KEYWORDS = {
    "beginner": ["beginner", "beginners", "introduction", "intro", "basics", "getting started", "101"],
    "intermediate": ["intermediate"],
    "advanced": ["advanced", "expert", "in-depth", "deep dive", "specialization", "mastering"],
}

# Domains where the host alone is enough to know the format.
FORMAT_DOMAIN_HINTS = {
    "vimeo.com": "video",
    "arxiv.org": "research_paper",
    "leetcode.com": "practice_platform",
    "hackerrank.com": "practice_platform",
    "codewars.com": "practice_platform",
    "coursera.org": "course",
    "udemy.com": "course",
    "edx.org": "course",
    "wikipedia.org": "article",
    "medium.com": "article",
    "amazon.com": "book",
    "oreilly.com": "book",
}

# YouTube needs path inspection, not just the domain: the same host serves
# single videos, playlists, channels and search results, and only a single
# video is something we can actually analyze.
YOUTUBE_HOSTS = ["youtube.com", "youtu.be"]
YOUTUBE_VIDEO_ID_PATTERNS = [
    r"[?&]v=([0-9A-Za-z_-]{11})(?:&|$)",
    r"youtu\.be/([0-9A-Za-z_-]{11})(?:\?|$)",
    r"/embed/([0-9A-Za-z_-]{11})(?:\?|$)",
    r"/shorts/([0-9A-Za-z_-]{11})(?:\?|$)",
]


def infer_difficulty(text):
    """Guesses difficulty from wording. Returns None if nothing matches --
    an honest 'unknown' rather than a made-up answer."""
    text_lower = text.lower()
    for difficulty_level, keywords in DIFFICULTY_KEYWORDS.items():
        for keyword in keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text_lower):
                return difficulty_level
    return None


def is_single_youtube_video(url):
    """True only for a URL pointing at ONE specific video.

    Playlists, channels and search-result pages all live on youtube.com but
    have no single transcript, so they are not videos for our purposes.
    """
    for pattern in YOUTUBE_VIDEO_ID_PATTERNS:
        if re.search(pattern, url):
            return True
    return False


def infer_format_from_url(url):
    """Determines format from the URL. Returns None when unsure."""
    url_lower = url.lower()

    for host in YOUTUBE_HOSTS:
        if host in url_lower:
            return "video" if is_single_youtube_video(url) else None

    for domain, format_name in FORMAT_DOMAIN_HINTS.items():
        if domain in url_lower:
            return format_name

    return None


def analyze_resource(resource):
    """Fills in missing metadata on one resource, in place."""
    combined_text = f"{resource.title} {resource.description}"
    if resource.difficulty is None:
        resource.difficulty = infer_difficulty(combined_text)
    url_format = infer_format_from_url(resource.url)
    if url_format is not None:
        resource.format = url_format
    return resource


def analyze_resources(resources):
    """Analyzes a whole list. This is the function retriever.py imports."""
    for resource in resources:
        analyze_resource(resource)
    return resources