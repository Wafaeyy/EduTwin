
from twin.mock_twin import get_relevant_digital_twin_state, normalize_learner_state
from retrieval.search_requirement import build_search_requirement
from retrieval.retriever import retrieve_with_fallback
from verification.verifier import verify_resources
from recommendation.engine import recommend


def get_recommendations(raw_learner):
    """
    The full pipeline, start to finish, with fallback handling built in at
    every stage. Safe to call with messy, partial, or completely empty
    learner data -- it will never crash.

    Args:
        raw_learner (dict or None): raw learner data, in any schema.

    Returns:
        dict: {"recommendations": [...], "message": ...}
    """
    learner = normalize_learner_state(raw_learner)
    search_requirement = build_search_requirement(learner)
    resources = retrieve_with_fallback(search_requirement)
    verified_resources = verify_resources(resources)

    if not verified_resources:
        return {
            "recommendations": [],
            "message": "No suitable verified resources were found for this learner.",
        }

    recommendations = recommend(learner, verified_resources)

    return {
        "recommendations": recommendations,
        "message": "OK",
    }


SCENARIO_EXAMPLES = {
    "A - no data at all": None,
    "B - partial data": {"goal": "machine learning"},
    "C - different field names": {
        "current_skill_level": "beginner",
        "learning_goal": "machine learning",
        "format_preference": "video",
        "duration_preference": "short",
    },
    "D - invalid values": {
        "level": "intermediate-beginner",
        "goal": "machine learning",
        "preferred_format": None,
        "preferred_duration": "short",
    },
}


if __name__ == "__main__":
    print("=== Normal case (clean Digital Twin data) ===")
    learner = get_relevant_digital_twin_state()
    result = get_recommendations(learner)
    for record in result["recommendations"]:
        print(f"\nResource: {record['resource']}")
        print(f"Score: {record['score']}")
        print(f"Confidence: {record['personalization_confidence']}")
        print(f"Reasons: {record['reasons']}")

    for scenario_name, raw_learner in SCENARIO_EXAMPLES.items():
        print(f"\n=== Scenario {scenario_name} ===")
        print(f"Raw input: {raw_learner}")

        result = get_recommendations(raw_learner)
        print(f"Message: {result['message']}")

        for record in result["recommendations"]:
            print(f"Resource: {record['resource']} | Score: {record['score']} | Confidence: {record['personalization_confidence']}")