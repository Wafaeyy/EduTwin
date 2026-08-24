"""
test_orchestrator.py

Tests for the Agent Orchestrator, Intent Classifier, and Parser pipeline.
"""

from src.agents.schemas import AgentType, IntentDecision, CoachSignal, MentorProposal
from src.agents.parsers import parse_coach_output, parse_mentor_output
from src.agents.orchestrator import AgentOrchestrator, route_and_execute_agent


def test_parsers():
    print("Testing parsers...")
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


if __name__ == "__main__":
    test_parsers()
    test_routing_mock()
    print("\nAll unit tests passed successfully!")
