"""
The Resource class: a structured blueprint for what an educational resource
looks like, replacing plain dictionaries.

Using a class instead of a dictionary means every resource is guaranteed to
have exactly these properties -- a typo like resource.tittle would raise a
clear error immediately, instead of silently returning None like
resource["tittle"] would with a dictionary.
"""


class Resource:
    def __init__(self, title, url, description, topic, difficulty, format, duration):
        self.title = title
        self.url = url
        self.description = description
        self.topic = topic
        self.difficulty = difficulty
        self.format = format
        self.duration = duration

    def __repr__(self):
        """
        Controls how this object looks when printed. Without this, printing
        a Resource would show something unhelpful like
        <models.resource.Resource object at 0x000001>. With it, printing
        shows the title instead, which is much more useful for debugging.
        """
        return f"Resource(title={self.title!r}, score-relevant fields: topic={self.topic!r}, difficulty={self.difficulty!r})"