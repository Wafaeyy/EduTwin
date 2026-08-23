"""
The Resource class: a structured blueprint for what an educational resource
looks like, replacing plain dictionaries.
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
        return f"Resource(title={self.title!r}, score-relevant fields: topic={self.topic!r}, difficulty={self.difficulty!r})"

    def to_dict(self):
        """Converts this Resource into a plain dictionary (JSON/DB-safe)."""
        return dict(vars(self))

    @classmethod
    def from_dict(cls, data):
        """Builds a new Resource from a plain dictionary.

        Used to turn a database row back into a real Resource object.
        """
        return cls(
            title=data["title"],
            url=data["url"],
            description=data["description"],
            topic=data["topic"],
            difficulty=data["difficulty"],
            format=data["format"],
            duration=data["duration"],
        )