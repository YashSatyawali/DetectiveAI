"""Human-readable formatting utilities for CLI output."""

from typing import Any

from app.models.game_event import GameEvent
from app.schemas.game_state import ActionResultDTO, GameStateDTO


def format_scenarios_list(scenarios: list[dict[str, Any]]) -> str:
    """Format available scenarios list for terminal display."""
    if not scenarios:
        return "No scenarios found."

    lines = [
        "Available Scenarios:",
        "",
        f"{'ID':<20} {'Version':<10} {'Name':<30}",
        "-" * 70,
    ]
    for s in scenarios:
        sid = s.get("id", "")
        ver = s.get("version", "")
        name = s.get("name", "")
        lines.append(f"{sid:<20} {ver:<10} {name:<30}")

    return "\n".join(lines)


def format_game_state(state: GameStateDTO) -> str:
    """Format player-facing GameStateDTO for terminal display."""
    disc_ev = (
        ", ".join(state.discovered_evidence_ids)
        if state.discovered_evidence_ids
        else "None"
    )
    inter_sus = (
        ", ".join(state.interviewed_suspect_ids)
        if state.interviewed_suspect_ids
        else "None"
    )
    visit_loc = (
        ", ".join(state.visited_location_ids) if state.visited_location_ids else "None"
    )
    comp_stg = (
        ", ".join(state.completed_stage_ids) if state.completed_stage_ids else "None"
    )

    stage_str = f"Order {state.current_stage_order} ({state.current_stage_id})"
    lines = [
        "=" * 70,
        "                         INVESTIGATION GAME STATE",
        "=" * 70,
        f"Session ID          : {state.session_id}",
        f"Scenario ID         : {state.scenario_id}",
        f"Case ID             : {state.case_id}",
        f"Status              : {state.status.value.upper()}",
        f"Current Stage       : {stage_str}",
        f"Current Location    : {state.current_location_id or 'None'}",
        f"Score               : {state.score}",
        "-" * 70,
        f"Discovered Evidence : {disc_ev}",
        f"Interviewed Suspects: {inter_sus}",
        f"Visited Locations   : {visit_loc}",
        f"Completed Stages    : {comp_stg}",
        "=" * 70,
    ]
    return "\n".join(lines)


def format_action_result(result: ActionResultDTO) -> str:
    """Format ActionResultDTO after executing an action."""
    status_str = "SUCCESS" if result.success else "FAILED"
    lines = [
        "-" * 70,
        f"Action              : {result.action.value.upper()}",
        f"Status              : {status_str}",
        f"Message             : {result.message}",
        f"Updated Score       : {result.state.score}",
    ]

    if result.newly_discovered_evidence:
        lines.append(
            f"New Evidence        : {', '.join(result.newly_discovered_evidence)}"
        )

    if result.already_known_evidence:
        lines.append(
            f"Already Known       : {', '.join(result.already_known_evidence)}"
        )

    if result.evidence_detail:
        ed = result.evidence_detail
        lines.extend(
            [
                "--- Evidence Details ---",
                f"  Name        : {ed.get('name')}",
                f"  Type        : {ed.get('evidence_type')}",
                f"  Description : {ed.get('description')}",
            ]
        )

    if result.interview_result:
        ir = result.interview_result
        lines.extend(
            [
                "--- Suspect Interview ---",
                f"  Name        : {ir.get('name')}",
                f"  Relationship: {ir.get('relationship_to_victim') or 'N/A'}",
                f"  Alibi       : {ir.get('alibi') or 'N/A'}",
                f"  Description : {ir.get('description')}",
            ]
        )

    if result.stage_unlocked:
        lines.append(f"Unlocked Stage      : {result.stage_unlocked}")

    if result.solution_correct is not None:
        outcome = "CORRECT" if result.solution_correct else "INCORRECT"
        lines.append(f"Solution Result     : {outcome}")

    lines.append("-" * 70)
    return "\n".join(lines)


def format_history(events: list[GameEvent]) -> str:
    """Format chronological GameEvent audit history."""
    if not events:
        return "No history recorded for this session."

    header = (
        f"{'#':<4} {'Timestamp':<20} {'Action':<16} "
        f"{'Target Type':<12} {'Target ID':<12}"
    )
    lines = [
        "=" * 70,
        "                       INVESTIGATION AUDIT HISTORY",
        "=" * 70,
        header,
        "-" * 70,
    ]
    for idx, e in enumerate(events, 1):
        ts = e.timestamp.strftime("%Y-%m-%d %H:%M:%S") if e.timestamp else ""
        act = e.event_type or ""
        ttype = e.target_type or "-"
        tid = e.target_id or "-"
        lines.append(f"{idx:<4} {ts:<20} {act:<16} {ttype:<12} {tid:<12}")

    lines.append("=" * 70)
    return "\n".join(lines)


def format_error(error_message: str) -> str:
    """Format domain errors for friendly terminal presentation."""
    return f"[Error] {error_message}"
