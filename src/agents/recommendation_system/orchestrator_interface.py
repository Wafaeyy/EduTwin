

from main import get_recommendations

SUPPORTED_INTENTS = ["resource_recommendation"]


def handle_orchestrator_request(request):
    """
    Args:
        request (dict): expected shape:
            {
                "intent": "resource_recommendation",
                "learner_state": {...},
                "user_request": "..." (not currently used by this engine,
                                        but accepted so the Orchestrator
                                        doesn't need a special case for us)
            }

    Returns:
        dict: {
            "status": "ok" or "error",
            "intent": the intent that was processed,
            "recommendations": [...] (decision records, empty on error),
            "message": a human-readable status message
        }
    """
    if request is None:
        return {
            "status": "error",
            "intent": None,
            "recommendations": [],
            "message": "No request was provided.",
        }

    intent = request.get("intent")

    if intent not in SUPPORTED_INTENTS:
        return {
            "status": "error",
            "intent": intent,
            "recommendations": [],
            "message": f"Unsupported intent: {intent!r}. This engine only handles: {SUPPORTED_INTENTS}",
        }

    learner_state = request.get("learner_state")
    result = get_recommendations(learner_state)

    return {
        "status": "ok",
        "intent": intent,
        "recommendations": result["recommendations"],
        "message": result["message"],
    }


if __name__ == "__main__":
    print("=== Valid Orchestrator request ===")
    valid_request = {
        "intent": "resource_recommendation",
        "learner_state": {
            "level": "beginner",
            "goal": "machine learning",
            "preferred_format": "video",
            "preferred_duration": "short",
        },
        "user_request": "Can you recommend a video for me to learn machine learning?",
    }
    response = handle_orchestrator_request(valid_request)
    print(f"Status: {response['status']}")
    print(f"Message: {response['message']}")
    for record in response["recommendations"]:
        print(f"  - {record['resource']} | Score: {record['score']}")

    print("\n=== Unsupported intent ===")
    bad_intent_request = {
        "intent": "study_schedule_planning",
        "learner_state": {},
    }
    response = handle_orchestrator_request(bad_intent_request)
    print(f"Status: {response['status']}")
    print(f"Message: {response['message']}")

    print("\n=== Completely empty request ===")
    response = handle_orchestrator_request(None)
    print(f"Status: {response['status']}")
    print(f"Message: {response['message']}")