from enum import Enum

class EducationStage(str, Enum):
    HIGH_SCHOOL = "High School"
    UNDERGRAD_YEAR_1 = "Undergraduate Year 1"
    UNDERGRAD_YEAR_2 = "Undergraduate Year 2"
    UNDERGRAD_YEAR_3 = "Undergraduate Year 3"
    UNDERGRAD_YEAR_4 = "Undergraduate Year 4"
    UNDERGRAD_YEAR_5 = "Undergraduate Year 5"
    MASTERS = "Master's"
    PHD = "PhD"
    PROFESSIONAL = "Professional"
    SELF_LEARNER = "Self Learner"

class GoalPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class GoalStatus(str, Enum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    PAUSED = "Paused"
    ABANDONED = "Abandoned"

# ============================================================
# Preference Dimensions
# ============================================================

class PreferenceDimension(str, Enum):
    EXPLANATION_DEPTH = "Explanation Depth"
    CONTENT_FORMAT = "Content Format"
    FEEDBACK_STYLE = "Feedback Style"
    DIFFICULTY = "Difficulty"


# ============================================================
# Explanation Depth
# ============================================================

class ExplanationDepth(str, Enum):
    SHORT = "Short"
    MEDIUM = "Medium"
    DETAILED = "Detailed"


# ============================================================
# Content Format
# ============================================================

class ContentFormat(str, Enum):
    TEXT = "Text"
    VIDEO = "Video"
    INTERACTIVE = "Interactive"
    AUDIO = "Audio"


# ============================================================
# Feedback Style
# ============================================================

class FeedbackStyle(str, Enum):
    DIRECT = "Direct"
    ENCOURAGING = "Encouraging"
    SOCRATIC = "Socratic"


# ============================================================
# Difficulty Preference
# ============================================================

class DifficultyPreference(str, Enum):
    EASY = "Easy"
    MODERATE = "Moderate"
    CHALLENGING = "Challenging"

PREFERENCE_OPTION_ENUMS = {
    PreferenceDimension.EXPLANATION_DEPTH: ExplanationDepth,
    PreferenceDimension.CONTENT_FORMAT: ContentFormat,
    PreferenceDimension.FEEDBACK_STYLE: FeedbackStyle,
    PreferenceDimension.DIFFICULTY: DifficultyPreference,
}

class LearningContext(str, Enum):

    GENERAL = "General"

    PROGRAMMING = "Programming"

    MATHEMATICS = "Mathematics"

    AI = "Artificial Intelligence"

    DATA_SCIENCE = "Data Science"

    RESEARCH = "Research"

    EXAM_PREPARATION = "Exam Preparation"

    PROJECT_WORK = "Project Work"