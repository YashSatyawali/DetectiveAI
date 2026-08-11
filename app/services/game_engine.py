"""Authoritative deterministic Game Engine for DetectiveAI."""

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.exceptions import (
    EvidenceNotDiscoveredError,
    InvalidActionError,
    InvalidLocationError,
    InvalidSolutionError,
    LocationLockedError,
    SessionAlreadyCompletedError,
    StageRequirementsNotMetError,
    SuspectNotAvailableError,
)
from app.models.game_event import GameEvent
from app.models.game_session import GameSession
from app.scenarios.loader import ScenarioLoader
from app.scenarios.schemas import ScenarioDefinition
from app.schemas.game_state import (
    ActionResultDTO,
    ActionType,
    GameActionDTO,
    SessionStatus,
)
from app.services.session_service import SessionService


class GameEngine:
    """Authoritative state machine and rule execution engine for investigations."""

    def __init__(
        self,
        loader: ScenarioLoader | None = None,
        session_service: SessionService | None = None,
    ) -> None:
        self.loader = loader or ScenarioLoader()
        self.session_service = session_service or SessionService(loader=self.loader)

    def execute_action(
        self,
        session_id: str,
        action: GameActionDTO,
        db: Session,
    ) -> ActionResultDTO:
        """Central execution entrypoint for all investigation game actions.

        1. Loads session and verifies status.
        2. Loads relevant scenario definition.
        3. Validates and executes action rules deterministically.
        4. Mutates state and records append-only GameEvent audit log.
        5. Returns structured ActionResultDTO.
        """
        session = self.session_service.get_session(session_id, db)

        # Enforce state transition rule: completed sessions reject actions
        if session.status in (
            SessionStatus.SOLVED.value,
            SessionStatus.FAILED.value,
        ):
            raise SessionAlreadyCompletedError(
                f"Session '{session_id}' is already {session.status.upper()} "
                "and cannot accept further investigation actions."
            )

        meta = session.state_metadata or {}
        scenario_id = meta.get("scenario_id")
        if not scenario_id:
            raise InvalidActionError("Session metadata missing scenario_id.")

        scenario = self.loader.load(scenario_id)

        # Dispatch action handlers
        if action.action_type == ActionType.MOVE:
            result = self._handle_move(session, scenario, action)
        elif action.action_type == ActionType.INSPECT:
            result = self._handle_inspect(session, scenario, action)
        elif action.action_type == ActionType.INTERVIEW:
            result = self._handle_interview(session, scenario, action)
        elif action.action_type == ActionType.EXAMINE_EVIDENCE:
            result = self._handle_examine_evidence(session, scenario, action)
        elif action.action_type == ActionType.ADVANCE_STAGE:
            result = self._handle_advance_stage(session, scenario, action)
        elif action.action_type == ActionType.SUBMIT_SOLUTION:
            result = self._handle_submit_solution(session, scenario, action)
        else:
            raise InvalidActionError(f"Unsupported action type '{action.action_type}'")

        # Record append-only GameEvent audit log
        event = GameEvent(
            session_id=session.id,
            event_type=action.action_type.value.upper(),
            target_type=self._get_target_type(action.action_type),
            target_id=action.target_id,
            result_data={
                "success": result.success,
                "message": result.message,
                "score": session.score,
            },
        )
        db.add(event)

        # Save session changes and commit transaction
        session.state_metadata = dict(meta)
        flag_modified(session, "state_metadata")
        db.add(session)
        db.commit()
        db.refresh(session)

        # Update state DTO in result
        result.state = self.session_service.to_game_state_dto(session)
        return result

    def _handle_move(
        self,
        session: GameSession,
        scenario: ScenarioDefinition,
        action: GameActionDTO,
    ) -> ActionResultDTO:
        target_id = action.target_id
        if not target_id:
            raise InvalidLocationError("MOVE action requires target_id (location ID).")

        location = next(
            (loc for loc in scenario.locations if loc.id == target_id), None
        )
        if not location:
            raise InvalidLocationError(
                f"Location '{target_id}' does not exist in scenario "
                f"'{scenario.scenario_id}'."
            )

        meta = session.state_metadata or {}
        visited = set(meta.get("visited_location_ids", []))

        # Check accessibility rule
        if not location.is_initial_unlocked and target_id not in visited:
            raise LocationLockedError(
                f"Location '{location.name}' ({target_id}) is locked."
            )

        session.current_location_id = target_id
        if target_id not in visited:
            visited.add(target_id)
            meta["visited_location_ids"] = sorted(visited)

        state_dto = self.session_service.to_game_state_dto(session)
        return ActionResultDTO(
            success=True,
            action=ActionType.MOVE,
            message=f"Moved to location '{location.name}'.",
            state=state_dto,
        )

    def _handle_inspect(
        self,
        session: GameSession,
        scenario: ScenarioDefinition,
        action: GameActionDTO,
    ) -> ActionResultDTO:
        current_loc_id = session.current_location_id
        if action.target_id and action.target_id != current_loc_id:
            raise InvalidLocationError(
                f"Cannot inspect location '{action.target_id}' while at "
                f"location '{current_loc_id}'."
            )

        meta = session.state_metadata or {}
        discovered_set = set(meta.get("discovered_evidence_ids", []))

        # Find evidence items located at the current location
        location_evidence = [
            ev for ev in scenario.evidence if ev.location_id == current_loc_id
        ]

        newly_discovered: list[str] = []
        already_known: list[str] = []

        for ev in location_evidence:
            if ev.id not in discovered_set:
                newly_discovered.append(ev.id)
                discovered_set.add(ev.id)
                session.score += 10  # Score reward for new evidence discovery
            else:
                already_known.append(ev.id)

        meta["discovered_evidence_ids"] = sorted(discovered_set)

        state_dto = self.session_service.to_game_state_dto(session)
        return ActionResultDTO(
            success=True,
            action=ActionType.INSPECT,
            message=(
                f"Inspected current location. Discovered {len(newly_discovered)} "
                f"new evidence item(s)."
            ),
            state=state_dto,
            newly_discovered_evidence=newly_discovered,
            already_known_evidence=already_known,
        )

    def _handle_interview(
        self,
        session: GameSession,
        scenario: ScenarioDefinition,
        action: GameActionDTO,
    ) -> ActionResultDTO:
        target_id = action.target_id
        if not target_id:
            raise SuspectNotAvailableError(
                "INTERVIEW action requires target_id (suspect ID)."
            )

        suspect = next((s for s in scenario.suspects if s.id == target_id), None)
        if not suspect:
            raise SuspectNotAvailableError(
                f"Suspect '{target_id}' is not available in scenario "
                f"'{scenario.scenario_id}'."
            )

        meta = session.state_metadata or {}
        interviewed_set = set(meta.get("interviewed_suspect_ids", []))

        if target_id not in interviewed_set:
            interviewed_set.add(target_id)
            meta["interviewed_suspect_ids"] = sorted(interviewed_set)
            session.score += 10  # Score reward for interviewing suspect

        # Public interview summary (strictly omits is_culprit / motive)
        public_interview = {
            "suspect_id": suspect.id,
            "name": suspect.name,
            "description": suspect.description,
            "alibi": suspect.alibi,
            "relationship_to_victim": suspect.relationship_to_victim,
            "profile_metadata": suspect.profile_metadata,
        }

        state_dto = self.session_service.to_game_state_dto(session)
        return ActionResultDTO(
            success=True,
            action=ActionType.INTERVIEW,
            message=f"Interviewed suspect '{suspect.name}'.",
            state=state_dto,
            interview_result=public_interview,
        )

    def _handle_examine_evidence(
        self,
        session: GameSession,
        scenario: ScenarioDefinition,
        action: GameActionDTO,
    ) -> ActionResultDTO:
        target_id = action.target_id
        if not target_id:
            raise EvidenceNotDiscoveredError(
                "EXAMINE_EVIDENCE action requires target_id (evidence ID)."
            )

        meta = session.state_metadata or {}
        discovered_set = set(meta.get("discovered_evidence_ids", []))

        if target_id not in discovered_set:
            raise EvidenceNotDiscoveredError(
                f"Cannot examine evidence '{target_id}': "
                "it has not been discovered yet."
            )

        evidence = next((ev for ev in scenario.evidence if ev.id == target_id), None)
        if not evidence:
            raise EvidenceNotDiscoveredError(
                f"Evidence '{target_id}' does not exist in scenario."
            )

        public_evidence = {
            "evidence_id": evidence.id,
            "name": evidence.name,
            "description": evidence.description,
            "evidence_type": evidence.evidence_type,
            "location_id": evidence.location_id,
            "discovery_metadata": evidence.discovery_metadata,
        }

        state_dto = self.session_service.to_game_state_dto(session)
        return ActionResultDTO(
            success=True,
            action=ActionType.EXAMINE_EVIDENCE,
            message=f"Examined evidence '{evidence.name}'.",
            state=state_dto,
            evidence_detail=public_evidence,
        )

    def _handle_advance_stage(
        self,
        session: GameSession,
        scenario: ScenarioDefinition,
        action: GameActionDTO,
    ) -> ActionResultDTO:
        meta = session.state_metadata or {}
        curr_stage_id = meta.get("current_stage_id")

        curr_stage = next(
            (st for st in scenario.stages if st.id == curr_stage_id), None
        )
        if not curr_stage:
            curr_stage = sorted(scenario.stages, key=lambda s: s.order)[0]

        # Evaluate current stage requirements against session discovery state
        reqs = curr_stage.requirements or {}
        req_evs = reqs.get("required_evidence_ids") or reqs.get("evidence_ids", [])
        req_locs = reqs.get("required_location_ids") or reqs.get("location_ids", [])
        req_suss = reqs.get("required_suspect_ids") or reqs.get("suspect_ids", [])

        discovered_evs = set(meta.get("discovered_evidence_ids", []))
        visited_locs = set(meta.get("visited_location_ids", []))
        interviewed_suss = set(meta.get("interviewed_suspect_ids", []))

        missing_evs = [ev for ev in req_evs if ev not in discovered_evs]
        missing_locs = [loc for loc in req_locs if loc not in visited_locs]
        missing_suss = [sus for sus in req_suss if sus not in interviewed_suss]

        if missing_evs or missing_locs or missing_suss:
            raise StageRequirementsNotMetError(
                f"Cannot advance from stage '{curr_stage.name}': requirements "
                f"not satisfied. Missing evidence: {missing_evs}, missing "
                f"locations: {missing_locs}, missing suspects: {missing_suss}"
            )

        # Find next stage
        sorted_stages = sorted(scenario.stages, key=lambda s: s.order)
        next_stage = next(
            (st for st in sorted_stages if st.order > curr_stage.order), None
        )

        completed = set(meta.get("completed_stage_ids", []))
        completed.add(curr_stage.id)
        meta["completed_stage_ids"] = sorted(completed)

        if not next_stage:
            state_dto = self.session_service.to_game_state_dto(session)
            return ActionResultDTO(
                success=True,
                action=ActionType.ADVANCE_STAGE,
                message="Completed current stage. Already at final stage.",
                state=state_dto,
            )

        meta["current_stage_id"] = next_stage.id
        meta["current_stage_order"] = next_stage.order

        state_dto = self.session_service.to_game_state_dto(session)
        return ActionResultDTO(
            success=True,
            action=ActionType.ADVANCE_STAGE,
            message=(
                f"Advanced investigation to stage {next_stage.order}: "
                f"'{next_stage.name}'."
            ),
            state=state_dto,
            stage_unlocked=next_stage.id,
        )

    def _handle_submit_solution(
        self,
        session: GameSession,
        scenario: ScenarioDefinition,
        action: GameActionDTO,
    ) -> ActionResultDTO:
        proposed_culprit_id = action.target_id
        if not proposed_culprit_id:
            raise InvalidSolutionError(
                "SUBMIT_SOLUTION action requires target_id "
                "(proposed culprit suspect ID)."
            )

        suspect = next(
            (s for s in scenario.suspects if s.id == proposed_culprit_id), None
        )
        if not suspect:
            raise InvalidSolutionError(
                f"Suspect '{proposed_culprit_id}' does not exist in scenario."
            )

        # Authoritative ground-truth evaluation ONLY inside backend
        is_correct = proposed_culprit_id == scenario.solution.culprit_id

        if is_correct:
            session.status = SessionStatus.SOLVED.value
            session.score += 50  # Score reward for solving case
            message = "Solution accepted! Case solved successfully."
        else:
            # Remains IN_PROGRESS on incorrect submission
            message = "Solution incorrect. Investigation remains in progress."

        state_dto = self.session_service.to_game_state_dto(session)
        return ActionResultDTO(
            success=is_correct,
            action=ActionType.SUBMIT_SOLUTION,
            message=message,
            state=state_dto,
            solution_correct=is_correct,
        )

    @staticmethod
    def _get_target_type(action_type: ActionType) -> str:
        mapping = {
            ActionType.MOVE: "location",
            ActionType.INSPECT: "location",
            ActionType.INTERVIEW: "suspect",
            ActionType.EXAMINE_EVIDENCE: "evidence",
            ActionType.ADVANCE_STAGE: "stage",
            ActionType.SUBMIT_SOLUTION: "solution",
        }
        return mapping.get(action_type, "unknown")
