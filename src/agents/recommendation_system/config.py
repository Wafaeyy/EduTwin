"""
Shared configuration constants used across multiple modules.

Keeping these in one place means if we ever add a new valid level, format,
or duration, we only change it here -- every module that checks against
these lists automatically sees the update.
"""

KNOWN_LEVELS = ["beginner", "intermediate", "advanced"]
KNOWN_FORMATS = [
    "video",
    "article",
    "course",
    "book",
    "tutorial",
    "documentation",
    "research_paper",
    "practice_platform",
]
KNOWN_DURATIONS = ["short", "medium", "long"]

FIELD_ALIASES = {
    "twin_id": ["twin_id", "learner_id", "student_id", "id"],
    "level": ["level", "current_skill_level", "skill_level"],
    "goal": ["goal", "learning_goal", "objective"],
    "preferred_format": ["preferred_format", "format_preference"],
    "preferred_duration": ["preferred_duration", "duration_preference"],
}