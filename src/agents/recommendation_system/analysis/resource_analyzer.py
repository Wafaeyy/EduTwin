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

# Domains where the host alone is enough to know the format. Kept broad enough
# to cover what discovery actually returns -- every domain missing from here
# scores 0 for format match, which costs a good resource 30 points.
FORMAT_DOMAIN_HINTS = {
    # Video
    "vimeo.com": "video",
    "ted.com": "video",
    "dailymotion.com": "video",

    # Courses
    "coursera.org": "course",
    "udemy.com": "course",
    "edx.org": "course",
    "udacity.com": "course",
    "pluralsight.com": "course",
    "datacamp.com": "course",
    "codecademy.com": "course",
    "khanacademy.org": "course",
    "learn.microsoft.com": "course",
    "developers.google.com": "course",
    "simplilearn.com": "course",
    "classcentral.com": "course",
    "skillshare.com": "course",

    # Research papers
    "arxiv.org": "research_paper",
    "papers.nips.cc": "research_paper",
    "openreview.net": "research_paper",
    "ieee.org": "research_paper",
    "acm.org": "research_paper",
    "researchgate.net": "research_paper",
    "sciencedirect.com": "research_paper",
    "springer.com": "research_paper",
    "nature.com": "research_paper",
    "jmlr.org": "research_paper",

    # Practice platforms
    "leetcode.com": "practice_platform",
    "hackerrank.com": "practice_platform",
    "codewars.com": "practice_platform",
    "kaggle.com": "practice_platform",
    "exercism.org": "practice_platform",
    "codeforces.com": "practice_platform",
    "hackerearth.com": "practice_platform",

    # Documentation
    "docs.python.org": "documentation",
    "docs.oracle.com": "documentation",
    "developer.mozilla.org": "documentation",
    "pytorch.org": "documentation",
    "tensorflow.org": "documentation",
    "scikit-learn.org": "documentation",
    "numpy.org": "documentation",
    "pandas.pydata.org": "documentation",
    "keras.io": "documentation",
    "readthedocs.io": "documentation",
    "docs.github.com": "documentation",

    # Tutorials
    "w3schools.com": "tutorial",
    "geeksforgeeks.org": "tutorial",
    "tutorialspoint.com": "tutorial",
    "freecodecamp.org": "tutorial",
    "realpython.com": "tutorial",
    "javatpoint.com": "tutorial",
    "programiz.com": "tutorial",
    "digitalocean.com": "tutorial",
    "machinelearningmastery.com": "tutorial",

    # Articles
    "wikipedia.org": "article",
    "medium.com": "article",
    "towardsdatascience.com": "article",
    "towardsai.net": "article",
    "dev.to": "article",
    "hackernoon.com": "article",
    "analyticsvidhya.com": "article",
    "stackoverflow.com": "article",
    "kdnuggets.com": "article",
    "substack.com": "article",

    # Books
    "amazon.com": "book",
    "oreilly.com": "book",
    "manning.com": "book",
    "packtpub.com": "book",
    "goodreads.com": "book",
}

# YouTube needs path inspection, not just the domain: the same host serves
# single videos, playlists, channels and search results. Only a single video
# has one transcript, so only a single video counts as "video".
YOUTUBE_HOSTS = ["youtube.com", "youtu.be"]
YOUTUBE_VIDEO_ID_PATTERNS = [
    r"[?&]v=([0-9A-Za-z_-]{11})(?:&|$)",
    r"youtu\.be/([0-9A-Za-z_-]{11})(?:\?|$)",
    r"/embed/([0-9A-Za-z_-]{11})(?:\?|$)",
    r"/shorts/([0-9A-Za-z_-]{11})(?:\?|$)",
]
YOUTUBE_PLAYLIST_PATTERN = r"[?&]list=([0-9A-Za-z_-]+)"


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
    """True only for a URL pointing at ONE specific video."""
    for pattern in YOUTUBE_VIDEO_ID_PATTERNS:
        if re.search(pattern, url):
            return True
    return False


def is_youtube_playlist(url):
    """True for a playlist URL with no single video id.

    A watch link can also carry a list= parameter ("play this video, from this
    playlist"). That is still one video, so the video check runs first.
    """
    return re.search(YOUTUBE_PLAYLIST_PATTERN, url) is not None


def infer_format_from_url(url):
    """Determines format from the URL. Returns None when genuinely unsure."""
    url_lower = url.lower()

    for host in YOUTUBE_HOSTS:
        if host in url_lower:
            if is_single_youtube_video(url):
                return "video"
            if is_youtube_playlist(url):
                # Honest label. A playlist is many videos, so it has no single
                # transcript -- calling it "video" would promise analysis we
                # cannot deliver, and calling it unknown hides what it is.
                return "playlist"
            # A channel, a search page, the homepage.
            return None

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