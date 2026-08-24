"""
parsers.py

Parses raw LLM outputs from agents into clean student-facing replies
and structured diagnostic signals/reports for the Digital Twin.
"""

import json
import re
from typing import Any

from src.agents.schemas import CoachSignal, MentorProposal


def parse_coach_output(raw_text: str) -> tuple[str, list[CoachSignal]]:
    """
    Extracts clean student-facing text and all <signal> blocks from Study Coach output.
    """
    signals: list[CoachSignal] = []

    # Find all <signal>...</signal> blocks
    raw_signals = re.findall(r"<signal>(.*?)</signal>", raw_text, re.DOTALL)
    for raw_sig in raw_signals:
        try:
            data = json.loads(raw_sig.strip())
            signals.append(CoachSignal(**data))
        except Exception:
            # Continue even if an individual signal fails to parse
            continue

    # Strip signal blocks to get the clean student-facing message
    clean_reply = re.sub(r"<signal>.*?</signal>", "", raw_text, flags=re.DOTALL).strip()
    return clean_reply, signals


def parse_mentor_output(raw_text: str) -> tuple[str, dict[str, Any] | None, list[MentorProposal]]:
    """
    Extracts clean student-facing text, <report> block, and <proposal> blocks from Career Mentor output.
    """
    report: dict[str, Any] | None = None
    proposals: list[MentorProposal] = []

    # Find <report>...</report>
    report_match = re.search(r"<report>(.*?)</report>", raw_text, re.DOTALL)
    if report_match:
        try:
            report = json.loads(report_match.group(1).strip())
        except Exception:
            pass

    # Find all <proposal>...</proposal>
    raw_proposals = re.findall(r"<proposal>(.*?)</proposal>", raw_text, re.DOTALL)
    for raw_prop in raw_proposals:
        try:
            data = json.loads(raw_prop.strip())
            proposals.append(MentorProposal(**data))
        except Exception:
            continue

    # Strip report and proposal blocks
    clean_reply = re.sub(r"<report>.*?</report>", "", raw_text, flags=re.DOTALL)
    clean_reply = re.sub(r"<proposal>.*?</proposal>", "", clean_reply, flags=re.DOTALL).strip()

    return clean_reply, report, proposals
