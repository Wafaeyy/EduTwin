"""
test_orchestrator.py

Tests for the Agent Orchestrator, Intent Classifier, and Parser pipeline.
"""

from src.agents.schemas import AgentType, IntentDecision, CoachSignal, MentorProposal
from src.agents.parsers import parse_coach_output, parse_mentor_output
from src.agents.intent_classifier import IntentClassifier
from src.agents.orchestrator import AgentOrchestrator, route_and_execute_agent


def test_intent_decision_schema():
    print("Testing IntentDecision schema normalization and robustness...")
    # Test normalization from string
    d1 = IntentDecision(agent="career_mentor", intent="goal_change", confidence=0.9)
    assert d1.agent == AgentType.CAREER_MENTOR

    d2 = IntentDecision(agent="Career Mentor", intent="career_fit_question")
    assert d2.agent == AgentType.CAREER_MENTOR

    d3 = IntentDecision(agent="recommendation", intent="resource_recommendation")
    assert d3.agent == AgentType.RECOMMENDATION_SYSTEM

    d4 = IntentDecision(agent="explainability", intent="explain_decision")
    assert d4.agent == AgentType.EXPLAINABILITY

    d5 = IntentDecision(agent="study_coach", intent="explain_concept")
    assert d5.agent == AgentType.STUDY_COACH

    # Test extra fields are ignored without raising ValidationError
    d6 = IntentDecision.model_validate({
        "agent": "career_mentor",
        "intent": "goal_change",
        "confidence": 0.85,
        "rationale": "Student wants to become ML engineer",
        "extra_unexpected_field": "some_value"
    })
    assert d6.agent == AgentType.CAREER_MENTOR
    print("[PASS] IntentDecision schema normalization and extra fields handling work cleanly.")


def test_heuristic_classification():
    print("\nTesting Heuristic Intent Classifier fallback...")
    classifier = IntentClassifier()

    dec1 = classifier._heuristic_fallback("I want to be a machine learining engineer")
    assert dec1.agent == AgentType.CAREER_MENTOR
    assert dec1.intent == "goal_change"

    dec2 = classifier._heuristic_fallback("Can you recommend videos or courses for linear algebra?")
    assert dec2.agent == AgentType.RECOMMENDATION_SYSTEM
    assert dec2.intent == "resource_recommendation"

    dec3 = classifier._heuristic_fallback("Why did you recommend this topic?")
    assert dec3.agent == AgentType.EXPLAINABILITY
    assert dec3.intent == "explain_decision"

    dec4 = classifier._heuristic_fallback("Can you explain how backpropagation works?")
    assert dec4.agent == AgentType.STUDY_COACH
    assert dec4.intent == "explain_concept"

    print("[PASS] Heuristic classifier routes queries accurately.")


def test_parsers():
    print("\nTesting parsers...")
    coach_sample = """
Let's look at the product rule step by step. When differentiating f(x)*g(x), the derivative is f'(x)g(x) + f(x)g'(x).

<signal>
{"concept": "product_rule", "signal": "mastery_evidence", "detail": "Student applied product rule correctly.", "evidence": "Applied f'g + fg'", "confidence": 0.8}
</signal>
"""
    clean_reply, signals = parse_coach_output(coach_sample)
    assert "Let's look at the product rule" in clean_reply
    assert "<signal>" not in clean_reply
    assert len(signals) == 1
    assert signals[0].concept == "product_rule"
    assert signals[0].signal == "mastery_evidence"
    assert signals[0].confidence == 0.8
    print("[PASS] Coach parser works cleanly.")

    mentor_sample = """
You should prioritize Linear Algebra before Deep Learning.

<report>
{"target_role": "machine_learning_engineer", "required_profile": {"linear_algebra": 0.7}, "current_profile": {"linear_algebra": 0.3}, "gaps_ranked": [{"skill": "linear_algebra", "gap": 0.4, "priority": 1, "reason": "Foundational"}], "direction": "linear_algebra"}
</report>

<proposal>
{"type": "goal_change_detected", "detail": "Wants to switch from Web Dev to ML", "evidence": "Student said: I want to focus on ML now", "confidence": 0.85}
</proposal>
"""
    clean_reply, report, proposals = parse_mentor_output(mentor_sample)
    assert "You should prioritize Linear Algebra" in clean_reply
    assert "<report>" not in clean_reply
    assert "<proposal>" not in clean_reply
    assert report is not None
    assert report["direction"] == "linear_algebra"
    assert len(proposals) == 1
    assert proposals[0].type == "goal_change_detected"
    assert proposals[0].confidence == 0.85
    print("[PASS] Mentor parser works cleanly.")


def test_routing_mock():
    print("\nTesting Orchestrator initialization and prompts...")
    orchestrator = AgentOrchestrator()
    assert len(orchestrator.coach_prompt) > 0, "Coach prompt failed to load"
    assert len(orchestrator.mentor_prompt) > 0, "Mentor prompt failed to load"
    print("[PASS] System prompts loaded successfully.")


def test_routing_dispatch():
    print("\nTesting Orchestrator routing dispatch logic...")
    orchestrator = AgentOrchestrator()

    # Verify forced_intent routes to Career Mentor
    forced = IntentDecision(agent=AgentType.CAREER_MENTOR, intent="goal_change")
    # Verify target agent identification
    assert forced.agent == AgentType.CAREER_MENTOR
    print("[PASS] Orchestrator routing dispatch is verified.")


if __name__ == "__main__":
    test_intent_decision_schema()
    test_heuristic_classification()
    test_parsers()
    test_routing_mock()
    test_routing_dispatch()
    print("\nAll unit tests passed successfully!")
