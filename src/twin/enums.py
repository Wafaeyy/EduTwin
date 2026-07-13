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