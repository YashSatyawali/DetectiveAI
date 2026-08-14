"""CLI command handlers linking terminal commands to application services."""

import sys
from typing import Any

from sqlalchemy import select

from app.core.exceptions import (
    EvidenceNotDiscoveredError,
    EvidenceNotFoundError,
    GameEngineError,
    InvalidSolutionError,
    SessionAlreadyCompletedError,
    SuspectNotAvailableError,
)
from app.db.database import SessionLocal, init_db
from app.lamatic.agent import DetectiveAgent
from app.lamatic.evidence_agent import EvidenceAgent
from app.lamatic.evidence_knowledge import EvidenceKnowledgeBuilder
from app.lamatic.exceptions import LamaticError
from app.models.game_event import GameEvent
from app.scenarios.exceptions import ScenarioError
from app.scenarios.loader import ScenarioLoader
from app.scenarios.registry import ScenarioRegistry
from app.schemas.game_state import ActionType, GameActionDTO, SessionStatus
from app.schemas.solution_evaluation import SolutionSubmission
from app.services.game_engine import GameEngine
from app.services.investigation_context import InvestigationContextBuilder
from app.services.session_service import SessionService
from app.services.solution_service import SolutionEvaluationService
from app.services.suspect_conversation import SuspectConversationManager
from app.services.suspect_knowledge import SuspectKnowledgeBuilder
from cli.formatting import (
    format_action_result,
    format_error,
    format_game_state,
    format_history,
    format_scenarios_list,
)


def scenarios_cmd() -> None:
    """List all available investigation scenarios."""
    try:
        registry = ScenarioRegistry()
        scenarios = registry.list_scenarios()
        print(format_scenarios_list(scenarios))
    except Exception as err:
        print(format_error(f"Failed to list scenarios: {err}"))
        sys.exit(1)


def start_cmd(scenario_id: str) -> str:
    """Start a new game session for a scenario."""
    init_db()
    db = SessionLocal()
    try:
        service = SessionService()
        state = service.start_game(scenario_id, db=db)
        print("Game Session Started Successfully!\n")
        print(format_game_state(state))
        print(
            "\n[Tip] To enter interactive mode, run: "
            f"python -m cli play {state.session_id}"
        )
        return state.session_id
    except (ScenarioError, GameEngineError) as err:
        print(format_error(str(err)))
        sys.exit(1)
    finally:
        db.close()


def state_cmd(session_id: str) -> None:
    """View player-facing current game state for a session."""
    init_db()
    db = SessionLocal()
    try:
        service = SessionService()
        session_obj = service.get_session(session_id, db=db)
        state = service.to_game_state_dto(session_obj)
        print(format_game_state(state))
    except GameEngineError as err:
        print(format_error(str(err)))
        sys.exit(1)
    finally:
        db.close()


def action_cmd(session_id: str, action: str, target_id: str | None = None) -> None:
    """Execute a game action on an active investigation session."""
    init_db()
    db = SessionLocal()
    try:
        # Normalize action input mapping
        action_clean = action.strip().lower()
        mapping = {
            "inspect": ActionType.INSPECT,
            "move": ActionType.MOVE,
            "interview": ActionType.INTERVIEW,
            "examine": ActionType.EXAMINE_EVIDENCE,
            "examine_evidence": ActionType.EXAMINE_EVIDENCE,
            "advance": ActionType.ADVANCE_STAGE,
            "advance_stage": ActionType.ADVANCE_STAGE,
            "solve": ActionType.SUBMIT_SOLUTION,
            "submit_solution": ActionType.SUBMIT_SOLUTION,
        }

        action_type = mapping.get(action_clean)
        if not action_type:
            print(
                format_error(
                    f"Unknown action '{action}'. Supported actions: move, inspect, "
                    "interview, examine, advance, solve."
                )
            )
            sys.exit(1)

        action_dto = GameActionDTO(action_type=action_type, target_id=target_id)
        engine = GameEngine()
        result = engine.execute_action(session_id, action_dto, db=db)
        print(format_action_result(result))
    except GameEngineError as err:
        print(format_error(str(err)))
        sys.exit(1)
    finally:
        db.close()


def history_cmd(session_id: str) -> None:
    """View chronological audit log of game events for a session."""
    init_db()
    db = SessionLocal()
    try:
        service = SessionService()
        # Verify session exists
        service.get_session(session_id, db=db)

        events = db.scalars(
            select(GameEvent)
            .where(GameEvent.session_id == session_id)
            .order_by(GameEvent.timestamp)
        ).all()
        print(format_history(list(events)))
    except GameEngineError as err:
        print(format_error(str(err)))
        sys.exit(1)
    finally:
        db.close()


def play_cmd(session_id: str, input_fn: Any = input) -> None:
    """Enter interactive REPL investigation mode for a game session."""
    init_db()
    db = SessionLocal()
    try:
        service = SessionService()
        engine = GameEngine()
        loader = ScenarioLoader()

        session_obj = service.get_session(session_id, db=db)
        state = service.to_game_state_dto(session_obj)
        scenario = loader.load(state.scenario_id)

        print("\n" + "=" * 70)
        print("                  DETECTIVE AI INTERACTIVE INVESTIGATION")
        print("=" * 70)
        print(f"Scenario : {scenario.name}")
        print(f"Case     : {scenario.case.title}")
        print(f"Session  : {state.session_id}")
        print(f"Status   : {state.status.value.upper()}")
        print("=" * 70)
        print("Type 'help' for available commands or 'quit' to exit.\n")

        while True:
            try:
                line = input_fn("detective> ")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting interactive investigation.")
                break

            if not line:
                continue

            parts = line.strip().split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None

            if cmd in ("quit", "exit"):
                print("Exiting investigation shell.")
                break

            if cmd == "help":
                _print_interactive_help()
                continue

            if cmd == "state":
                # Refresh session state
                db.refresh(session_obj)
                cur_state = service.to_game_state_dto(session_obj)
                print(format_game_state(cur_state))
                continue

            if cmd == "ask":
                if not arg:
                    print(format_error("Usage: ask <message>"))
                    continue
                try:
                    builder = InvestigationContextBuilder()
                    ctx = builder.build_context(session_id, db=db)
                    agent = DetectiveAgent()
                    res = agent.ask(arg, context=ctx)
                    print("\nDetective AI (Lamatic Agent):")
                    print(res.content)
                except (LamaticError, GameEngineError) as err:
                    print(f"[Lamatic Error]\n{err}")
                continue

            if cmd == "interrogate":
                if not arg:
                    print(format_error("Usage: interrogate <suspect_id>"))
                    continue
                interrogate_cmd(session_id, arg, input_fn=input_fn)
                continue

            if cmd == "examine":
                if not arg:
                    print(format_error("Usage: examine <evidence_id>"))
                    continue
                examine_cmd(session_id, arg, db=db)
                continue

            if cmd == "solve":
                solve_cmd(session_id, target_id=arg, input_fn=input_fn, db=db)
                continue

            # Action execution in REPL
            mapping = {
                "inspect": ActionType.INSPECT,
                "move": ActionType.MOVE,
                "interview": ActionType.INTERVIEW,
                "advance": ActionType.ADVANCE_STAGE,
            }

            action_type = mapping.get(cmd)
            if not action_type:
                print(
                    format_error(
                        f"Unknown command '{cmd}'. Type 'help' for supported commands."
                    )
                )
                continue

            try:
                action_dto = GameActionDTO(action_type=action_type, target_id=arg)
                result = engine.execute_action(session_id, action_dto, db=db)
                print(format_action_result(result))

                if result.state.status != SessionStatus.IN_PROGRESS:
                    status_upper = result.state.status.value.upper()
                    print(
                        "\n[Notice] Investigation complete. Session status: "
                        f"{status_upper}"
                    )
            except (GameEngineError, ScenarioError) as err:
                print(format_error(str(err)))

    finally:
        db.close()


def ask_cmd(message: str, session_id: str | None = None) -> None:
    """Send a question to the Lamatic agent, optionally with session context."""
    init_db()
    db = SessionLocal()
    try:
        context = None
        if session_id:
            builder = InvestigationContextBuilder()
            context = builder.build_context(session_id, db=db)

        agent = DetectiveAgent()
        response = agent.ask(message, context=context)
        print("\nDetective AI (Lamatic Agent):")
        print(response.content)
    except (LamaticError, GameEngineError) as err:
        print(f"[Lamatic Error]\n{err}")
        sys.exit(1)
    finally:
        db.close()


def interrogate_cmd(
    session_id: str,
    suspect_id: str,
    input_fn: Any = input,
    db: Any | None = None,
) -> None:
    """Start interactive AI interrogation with a suspect via GameEngine and Agent."""
    init_db()
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        engine = GameEngine()
        session_service = SessionService()

        # 1. GameEngine validates INTERVIEW action & updates session state
        interview_action = GameActionDTO(
            action_type=ActionType.INTERVIEW, target_id=suspect_id
        )
        engine.execute_action(session_id, interview_action, db=db)

        # 2. Get session & build player-safe SuspectKnowledge
        session_obj = session_service.get_session(session_id, db=db)
        state_dto = session_service.to_game_state_dto(session_obj)
        builder = SuspectKnowledgeBuilder()
        knowledge = builder.build_knowledge(state_dto.scenario_id, suspect_id)

        print("\n" + "=" * 70)
        print("                  SUSPECT INTERROGATION SESSION")
        print("=" * 70)
        print(f"Suspect      : {knowledge.name} ({knowledge.suspect_id})")
        print(f"Alibi        : {knowledge.alibi or 'N/A'}")
        print(f"Relationship : {knowledge.relationship_to_victim or 'N/A'}")
        print("=" * 70)
        print(
            "Type your questions for the suspect. "
            "Type 'quit' or 'exit' to end interrogation.\n"
        )

        conversation_mgr = SuspectConversationManager()

        while True:
            try:
                line = input_fn(f"{suspect_id}> ")
            except (EOFError, KeyboardInterrupt):
                print(f"\nEnding interrogation with {knowledge.name}.\n")
                break

            if not line:
                continue

            clean_line = line.strip()
            if clean_line.lower() in ("quit", "exit"):
                print(f"Ending interrogation with {knowledge.name}.\n")
                break

            try:
                response = conversation_mgr.ask_suspect(
                    session_id=session_id,
                    knowledge=knowledge,
                    user_message=clean_line,
                    db=db,
                )
                print(f"\n{knowledge.name}:")
                print(f"{response.content}\n")
            except LamaticError as err:
                print(f"[Lamatic Error]\n{err}\n")

    except (GameEngineError, ScenarioError, SuspectNotAvailableError) as err:
        print(format_error(str(err)))
        if input_fn == input:
            sys.exit(1)
        raise
    finally:
        if close_db and db is not None:
            db.close()


def examine_cmd(session_id: str, evidence_id: str, db: Any | None = None) -> None:
    """Examine evidence via GameEngine and provide AI forensic analysis."""
    init_db()
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        engine = GameEngine()
        session_service = SessionService()

        # 1. GameEngine validates session & executes EXAMINE_EVIDENCE
        action_dto = GameActionDTO(
            action_type=ActionType.EXAMINE_EVIDENCE, target_id=evidence_id
        )
        result = engine.execute_action(session_id, action_dto, db=db)
        print(format_action_result(result))

        # 2. Build player-safe EvidenceKnowledge & InvestigationContext
        session_obj = session_service.get_session(session_id, db=db)
        state_dto = session_service.to_game_state_dto(session_obj)

        ek_builder = EvidenceKnowledgeBuilder()
        knowledge = ek_builder.build_knowledge(state_dto.scenario_id, evidence_id)

        ctx_builder = InvestigationContextBuilder()
        context = ctx_builder.build_context(session_id, db=db)

        # 3. Perform AI forensic interpretation
        try:
            agent = EvidenceAgent()
            response = agent.ask(knowledge=knowledge, context=context)
            print("\n" + "=" * 70)
            print("                     AI FORENSIC ANALYSIS")
            print("=" * 70)
            print(f"Item Analyzed : {knowledge.name} ({knowledge.evidence_id})")
            print(f"Location      : {knowledge.location_name or 'N/A'}")
            print("-" * 70)
            print(response.content)
            print("=" * 70 + "\n")
        except LamaticError as err:
            print(f"\n[Lamatic Error]\n{err}\n")

    except (
        GameEngineError,
        ScenarioError,
        EvidenceNotDiscoveredError,
        EvidenceNotFoundError,
    ) as err:
        print(format_error(str(err)))
        if close_db:
            sys.exit(1)
        raise
    finally:
        if close_db and db is not None:
            db.close()


def solve_cmd(
    session_id: str,
    target_id: str | None = None,
    input_fn: Any = input,
    db: Any | None = None,
) -> None:
    """Submit case solution theory for evaluation and resolution."""
    init_db()
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        session_service = SessionService()

        # Verify session state before prompt
        session_obj = session_service.get_session(session_id, db=db)
        if session_obj.status in (
            SessionStatus.SOLVED.value,
            SessionStatus.FAILED.value,
        ):
            raise SessionAlreadyCompletedError(
                f"Cannot submit solution: session '{session_id}' is already completed."
            )

        print("\n" + "=" * 70)
        print("                  FINAL CASE SOLUTION SUBMISSION")
        print("=" * 70)
        print("Provide your case theory, supporting evidence, and reasoning below.\n")

        if target_id:
            culprit_id = target_id.strip()
            print(f"Culprit (suspect_id): {culprit_id}")
        else:
            culprit_id = input_fn("Culprit (suspect_id): ").strip()
        motive = input_fn("Motive explanation: ").strip()
        explanation = input_fn("What happened? ").strip()
        raw_evidence = input_fn("Supporting evidence IDs (comma-separated): ").strip()
        reasoning = input_fn("Reasoning explaining evidence: ").strip()
        timeline = input_fn("Timeline reconstruction (optional): ").strip()

        evidence_ids = [e.strip() for e in raw_evidence.split(",") if e.strip()]

        print("\nReview Case Submission:")
        print(f"  Culprit   : {culprit_id}")
        print(f"  Motive    : {motive}")
        print(f"  Evidence  : {evidence_ids}")
        confirm = input_fn("Submit case? [y/N]: ").strip().lower()

        if confirm not in ("y", "yes"):
            print("Submission cancelled.\n")
            return

        submission = SolutionSubmission(
            session_id=session_id,
            culprit_id=culprit_id,
            motive=motive,
            explanation=explanation,
            supporting_evidence_ids=evidence_ids,
            reasoning=reasoning,
            timeline_explanation=timeline if timeline else None,
        )

        service = SolutionEvaluationService()
        action_result, evaluation = service.evaluate_and_submit(submission, db=db)

        # Display Case Evaluation Report
        print("\n" + "=" * 70)
        print("                     CASE RESOLUTION EVALUATION")
        print("=" * 70)
        is_correct = evaluation.culprit_correct
        status_text = "CORRECT (+30 pts)" if is_correct else "INCORRECT (0 pts)"
        print(f"Culprit Identification : {status_text}")
        print(f"Evidence Reasoning     : {evaluation.evidence_score}/20")
        print(f"Motive Reasoning       : {evaluation.motive_score}/15")
        print(f"Reasoning Quality      : {evaluation.reasoning_score}/20")
        print(f"Timeline Reasoning     : {evaluation.timeline_score}/15")
        print("-" * 70)
        print(f"Overall Case Score     : {evaluation.overall_score}/100")
        print("-" * 70)

        if evaluation.strengths:
            print("Strengths:")
            for s in evaluation.strengths:
                print(f"  • {s}")
            print()

        if evaluation.weaknesses:
            print("Weaknesses:")
            for w in evaluation.weaknesses:
                print(f"  • {w}")
            print()

        if evaluation.contradictions:
            print("Contradictions:")
            for c in evaluation.contradictions:
                print(f"  • {c}")
            print()

        print("Feedback:")
        print(evaluation.feedback)
        print("=" * 70 + "\n")

    except (
        GameEngineError,
        ScenarioError,
        InvalidSolutionError,
        SessionAlreadyCompletedError,
    ) as err:
        print(format_error(str(err)))
        if input_fn == input:
            sys.exit(1)
        raise
    finally:
        if close_db and db is not None:
            db.close()


def _print_interactive_help() -> None:
    """Display interactive shell help menu."""
    help_text = """
Available Interactive Commands:

  ask <message>           Ask the prototype Lamatic AI agent a question
  interrogate <suspect_id> Start conversational AI interrogation with a suspect
  examine <evidence_id>   Examine evidence and view AI forensic analysis
  inspect                 Inspect current location for evidence
  move <location_id>      Move to an unlocked location
  interview <suspect_id>  Interview a suspect
  advance                 Advance to the next investigation stage
  solve                   Submit final case solution theory and receive evaluation
  state                   View current investigation state
  history                 View chronological audit history
  help                    Display this help menu
  quit / exit             Exit interactive investigation mode
"""
    print(help_text)
