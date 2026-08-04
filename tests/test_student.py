## to run  python -m tests.test_student
from src.twin.student import StudentTwin
from src.twin.profile import Profile
from src.twin.skill import Skill
from src.twin.knowledge import Knowledge
from src.twin.interest import Interest
from src.twin.preference import Preference
from src.twin.twin_store import TwinStore
from src.twin.enums import EducationStage, PreferenceDimension, LearningContext

def main():

    # -------------------------------------------------------
    # Create student
    # -------------------------------------------------------

    profile = Profile(
        full_name= "teez kebera",
        university= "big ass",
        fied_of_study="AI",
        education_stage= EducationStage.UNDERGRAD_YEAR_2,
    )

    student = StudentTwin(profile=profile)

    # -------------------------------------------------------
    # Add some searchable Twin items
    # -------------------------------------------------------

    skill = Skill(
        name= "building AI models",
        description="use machine learning to build ai models",
        skill_level=0.5,
        confidence=0.3
    )

    knowledge = Knowledge(
        title="machine learning",
        description="hehe",
        mastery= 0.9,
        confidence= 0.6
    )

    interest = Interest(
        topic="cats",
        affinity=0.1,
        confidence=0.9
    )

    preference = Preference(
        dimension= PreferenceDimension.EXPLANATION_DEPTH,
        context= LearningContext.GENERAL,
        affinities= {"Short":0.5,
                        "Medium": 0.7,
                        "Detailed": 0.3}
    )

    student.skills[skill.skill_id] = skill
    student.knowledge[knowledge.knowledge_id] = knowledge
    student.interests[interest.interest_id] = interest
    student.preferences[preference.preference_id] = preference

    # -------------------------------------------------------
    # Create TwinStore
    # -------------------------------------------------------

    store = TwinStore()

    print("Indexing student...")

    store.index_student(student)

    print("Done.")

    # -------------------------------------------------------
    # Search
    # -------------------------------------------------------

    print("\nSearching...\n")

    results = store.search(
        twin_id=student.twin_id,
        query="i",
        top_n=10,
    )

    print(f"Retrieved {len(results)} items\n")

    for item, score in results:
        print("=" * 60)
        print(type(item).__name__)
        print(f"Similarity: {score:.3f}")
        print(item)
        print()

    # -------------------------------------------------------
    # Delete
    # -------------------------------------------------------

    print("Deleting student...")

    store.delete_student(student.twin_id)

    print("Done.")

    results = store.search(
        twin_id=student.twin_id,
        query="machine learning",
    )

    print(f"Remaining results after delete: {len(results)}")


if __name__ == "__main__":
    main()