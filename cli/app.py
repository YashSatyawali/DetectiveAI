"""Typer application setup for DetectiveAI CLI."""

from typing import Annotated

import typer

from cli.commands import (
    action_cmd,
    ask_cmd,
    history_cmd,
    play_cmd,
    scenarios_cmd,
    start_cmd,
    state_cmd,
)

app = typer.Typer(
    name="detective",
    help="DetectiveAI - Deterministic Interactive Investigation CLI",
    add_completion=False,
)


@app.command("scenarios")
def list_scenarios() -> None:
    """Discover and list all available investigation scenarios."""
    scenarios_cmd()


@app.command("start")
def start_game(
    scenario_id: Annotated[
        str, typer.Argument(help="ID of scenario to start (e.g. test_case)")
    ],
) -> None:
    """Start a new game session for a scenario."""
    start_cmd(scenario_id)


@app.command("state")
def view_state(
    session_id: Annotated[str, typer.Argument(help="Session ID of the investigation")],
) -> None:
    """View current player-facing game state for an active session."""
    state_cmd(session_id)


@app.command("action")
def execute_action(
    session_id: Annotated[str, typer.Argument(help="Session ID of the investigation")],
    action: Annotated[
        str,
        typer.Argument(
            help="Action to execute (move, inspect, interview, examine, advance, solve)"
        ),
    ],
    target_id: Annotated[
        str | None,
        typer.Argument(
            help="Optional target entity ID (location ID, suspect ID, evidence ID)"
        ),
    ] = None,
) -> None:
    """Execute a single investigation action on a game session."""
    action_cmd(session_id, action, target_id)


@app.command("history")
def view_history(
    session_id: Annotated[str, typer.Argument(help="Session ID of the investigation")],
) -> None:
    """View chronological audit history of game events for a session."""
    history_cmd(session_id)


@app.command("play")
def play_interactive(
    session_id: Annotated[str, typer.Argument(help="Session ID of the investigation")],
) -> None:
    """Enter interactive investigation shell mode."""
    play_cmd(session_id)


@app.command("ask")
def ask_agent(
    message: Annotated[
        str, typer.Argument(help="Message or question to send to the Lamatic agent")
    ],
) -> None:
    """Send a question or message to the prototype Lamatic agent."""
    ask_cmd(message)


if __name__ == "__main__":
    app()
