"""CLI command handlers linking terminal commands to application services."""

import sys
from typing import Any

from sqlalchemy import select

from app.core.exceptions import GameEngineError
from app.db.database import SessionLocal, init_db
from app.models.game_event import GameEvent
from app.scenarios.exceptions import ScenarioError
from app.scenarios.loader import ScenarioLoader
from app.scenarios.registry import ScenarioRegistry
from app.schemas.game_state import ActionType, GameActionDTO, SessionStatus
from app.services.game_engine import GameEngine
from app.services.session_service import SessionService
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

            if cmd == "history":
                events = db.scalars(
                    select(GameEvent)
                    .where(GameEvent.session_id == session_id)
                    .order_by(GameEvent.timestamp)
                ).all()
                print(format_history(list(events)))
                continue

            # Action execution in REPL
            mapping = {
                "inspect": ActionType.INSPECT,
                "move": ActionType.MOVE,
                "interview": ActionType.INTERVIEW,
                "examine": ActionType.EXAMINE_EVIDENCE,
                "advance": ActionType.ADVANCE_STAGE,
                "solve": ActionType.SUBMIT_SOLUTION,
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


def _print_interactive_help() -> None:
    """Display interactive shell help menu."""
    help_text = """
Available Interactive Commands:

  inspect                 Inspect current location for evidence
  move <location_id>      Move to an unlocked location
  interview <suspect_id>  Interview a suspect
  examine <evidence_id>   Examine discovered evidence
  advance                 Advance to the next investigation stage
  solve <suspect_id>      Submit proposed culprit solution
  state                   View current investigation state
  history                 View chronological audit history
  help                    Display this help menu
  quit / exit             Exit interactive investigation mode
"""
    print(help_text)
