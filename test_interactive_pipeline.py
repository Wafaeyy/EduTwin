"""
test_interactive_pipeline.py

Interactive tester for the full EduTwin pipeline end-to-end with multi-turn history.
Displays detailed output from every pipeline component on each turn.
"""

import json
from dotenv import load_dotenv

load_dotenv()

from src.services.edutwin_service import EduTwinService


def print_banner():
    print("=" * 80)
    print("           🎓 EduTwin Full Pipeline - Interactive History Tester           ")
    print("=" * 80)
    print("Commands:")
    print("  'exit' or 'quit' : Stop the session")
    print("  'history'        : Print full conversation history currently in orchestrator")
    print("  'clear'          : Reset conversation history")
    print("  'twin'           : Show current student digital twin state")
    print("  'brief'          : Toggle showing full briefing vs summary on each turn")
    print("=" * 80)


def print_twin_summary(twin):
    print("\n" + "─" * 30 + " CURRENT DIGITAL TWIN " + "─" * 30)
    stage = twin.profile.education_stage.value if hasattr(twin.profile.education_stage, "value") else twin.profile.education_stage
    print(f"Learner   : {twin.profile.full_name} ({stage})")
    print(f"Field     : {twin.profile.fied_of_study} @ {twin.profile.university}")
    
    print("\n[Skills]")
    for s in twin.skills.values():
        print(f"  • {s.name:<25} level={s.skill_level:.2f}, conf={s.confidence:.2f}")
        
    print("\n[Knowledge]")
    for k in twin.knowledge.values():
        print(f"  • {k.title:<25} mastery={k.mastery:.2f}, conf={k.confidence:.2f}")
        
    print("\n[Interests]")
    for i in twin.interests.values():
        print(f"  • {i.topic:<25} affinity={i.affinity:.2f}, conf={i.confidence:.2f}")
        
    print("\n[Preferences]")
    for p in twin.preferences.values():
        dim = p.dimension.value if hasattr(p.dimension, "value") else p.dimension
        print(f"  • {dim:<25} affinities={p.affinities}")
        
    print("\n[Goals]")
    for g in twin.goals.values():
        print(f"  • {g.title:<25} progress={g.progress}%, status={g.status}")
        
    print("─" * 82 + "\n")


def format_evidence_preview(evidence_list):
    if not evidence_list:
        return "None"
    lines = []
    for ev in evidence_list:
        src = ev.source.value if hasattr(ev.source, "value") else str(ev.source)
        content_preview = ev.content if len(ev.content) < 80 else ev.content[:77] + "..."
        lines.append(f"  [{src}] {content_preview}")
    return "\n".join(lines)


def run_pipeline_turn(service: EduTwinService, query: str, show_full_brief: bool = False):
    print("\n" + "═" * 80)
    print(f"🚀 PROCESSING QUERY: \"{query}\"")
    print("═" * 80)

    # -------------------------------------------------------------
    # 1. Retrieval
    # -------------------------------------------------------------
    retrieval_evidence = service.retrieval_orchestrator.retrieve(
        student=service.twin,
        query=query
    )
    print(f"\n📥 [1. RETRIEVAL]")
    print(f"  Total Evidence Items: {len(retrieval_evidence)}")
    if retrieval_evidence:
        print(format_evidence_preview(retrieval_evidence))

    # -------------------------------------------------------------
    # 2. Context Builder
    # -------------------------------------------------------------
    brief = service.context_builder.build(retrieval_evidence)
    print(f"\n📋 [2. CONTEXT BRIEFING]")
    if show_full_brief:
        print(brief)
    else:
        brief_preview = brief.replace("\n", " ")
        if len(brief_preview) > 160:
            brief_preview = brief_preview[:157] + "..."
        print(f"  Briefing ({len(brief)} chars): {brief_preview}")

    # -------------------------------------------------------------
    # 3. Agent Routing & Execution
    # -------------------------------------------------------------
    history_before_len = len(service.agent_orchestrator.history)
    agent_result = service.agent_orchestrator.process(
        query=query,
        brief=brief,
        twin=service.twin
    )
    agent_name_val = agent_result.agent_name.value if hasattr(agent_result.agent_name, "value") else str(agent_result.agent_name)

    print(f"\n🤖 [3. AGENT ROUTING & EXECUTION]")
    print(f"  • Selected Agent : {agent_name_val.upper()}")
    print(f"  • Detected Intent: {agent_result.intent}")
    print(f"  • History Count  : {history_before_len} msgs passed to agent/router")

    # Diagnostic Signals (Study Coach)
    if agent_result.signals:
        print(f"\n  📡 Diagnostic Signals ({len(agent_result.signals)}):")
        for sig in agent_result.signals:
            sig_type = sig.signal.value if hasattr(sig.signal, "value") else str(sig.signal)
            print(f"    - Concept: {sig.concept} | Signal: {sig_type} | Conf: {sig.confidence:.2f}")
            print(f"      Detail: {sig.detail}")
            if sig.evidence:
                print(f"      Evidence: \"{sig.evidence}\"")

    # Proposals (Career Mentor)
    if agent_result.proposals:
        print(f"\n  💼 Career Proposals ({len(agent_result.proposals)}):")
        for prop in agent_result.proposals:
            p_type = prop.type.value if hasattr(prop.type, "value") else str(prop.type)
            print(f"    - Proposal: {p_type} | Conf: {prop.confidence:.2f}")
            print(f"      Detail: {prop.detail}")
            if prop.evidence:
                print(f"      Evidence: \"{prop.evidence}\"")

    # Career Mentor Report
    if agent_result.report:
        print(f"\n  📊 Mentor Report:")
        print(f"    - Target Role: {agent_result.report.target_role}")
        if agent_result.report.gaps_ranked:
            print(f"    - Skill Gaps Ranked:")
            for g in agent_result.report.gaps_ranked:
                print(f"      • {g.skill} (gap: {g.gap:.2f}, priority: {g.priority}): {g.reason}")

    # Recommendations
    if agent_result.recommendations:
        print(f"\n  📚 Recommendations ({len(agent_result.recommendations)}):")
        for r in agent_result.recommendations:
            print(f"    • {r}")

    # Student-facing reply
    print("\n" + "─" * 32 + " AGENT ANSWER " + "─" * 32)
    print(agent_result.reply)
    print("─" * 78)

    # -------------------------------------------------------------
    # 4. Memory Decision
    # -------------------------------------------------------------
    memory = service.memory_decision.process_interaction(
        user_message=query,
        assistant_message=agent_result.reply
    )
    print(f"\n🧠 [4. MEMORY DECISION]")
    if memory:
        comps = [c.value if hasattr(c, "value") else str(c) for c in memory.affected_components]
        print(f"  • Memory Stored     : YES ✅")
        print(f"  • Content           : {memory.content}")
        print(f"  • Importance        : {memory.importance:.2f}")
        print(f"  • Affected Comps    : {comps}")
    else:
        print(f"  • Memory Stored     : NO ❌ (filtered out or not durable learner info)")

    # -------------------------------------------------------------
    # 5. Twin Entity Resolution & 6. Twin Update
    # -------------------------------------------------------------
    if memory:
        resolved_evidence = service.resolver.resolve(
            student=service.twin,
            memory=memory
        )
        print(f"\n🎯 [5. TWIN ENTITY RESOLUTION]")
        for item in resolved_evidence:
            comp = item.component.value if hasattr(item.component, "value") else str(item.component)
            status = item.status.value if hasattr(item.status, "value") else str(item.status)
            dir_str = item.direction.value if item.direction and hasattr(item.direction, "value") else str(item.direction)
            print(f"  • Component : {comp}")
            print(f"    Status    : {status}")
            print(f"    Entity    : {item.entity_name or item.entity_id or 'None'}")
            print(f"    Direction : {dir_str} | Strength: {item.strength} | Conf: {item.resolution_confidence:.2f}")
            print(f"    Reason    : {item.reason}")

        print(f"\n🔄 [6. TWIN UPDATER]")
        update_report = service.twin_updater.update(
            student=service.twin,
            evidence=resolved_evidence
        )
        print(f"  Update Report:\n  {update_report}")
    else:
        print(f"\n🎯 [5. TWIN ENTITY RESOLUTION & 6. TWIN UPDATER]")
        print("  Skipped (no new memory generated this turn)")

    print("\n" + "═" * 80 + "\n")


def main():
    print_banner()
    print("Initializing full EduTwin pipeline...")
    service = EduTwinService()
    print("EduTwin service initialized successfully.\n")

    show_full_brief = False
    turn = 1

    while True:
        try:
            user_input = input(f"[Turn {turn}] You > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("exit", "quit", "q"):
            print("Session ended.")
            break
        elif cmd == "history":
            history = service.agent_orchestrator.history
            print("\n" + "=" * 30 + " ORCHESTRATOR HISTORY " + "=" * 30)
            if not history:
                print("(History is currently empty)")
            else:
                for idx, entry in enumerate(history, 1):
                    print(f"[{idx}] {entry}")
            print("=" * 82 + "\n")
            continue
        elif cmd == "clear":
            service.agent_orchestrator.history.clear()
            print("\n🧹 [Conversation History Cleared]\n")
            continue
        elif cmd == "twin":
            print_twin_summary(service.twin)
            continue
        elif cmd == "brief":
            show_full_brief = not show_full_brief
            print(f"\n[Full Briefing Display: {'ON' if show_full_brief else 'OFF'}]\n")
            continue

        try:
            run_pipeline_turn(service, user_input, show_full_brief=show_full_brief)
            turn += 1
        except Exception as e:
            print(f"\n❌ Error during pipeline execution: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
