# DetectiveAI Architecture Specification

## 1. Project Purpose

**DetectiveAI** is an interactive, AI-powered detective investigation engine and game. Players take on the role of a lead detective investigating fictional mystery cases by performing investigative actions such as:

* Listing suspects and reviewing their alibis
* Searching locations for physical and digital evidence
* Interrogating suspects and witnesses
* Reviewing chronological timelines of events
* Forming hypotheses and connecting pieces of evidence
* Submitting a final case solution (identifying culprit, motive, and supporting evidence)

The primary vision of DetectiveAI is to combine the procedural rigour of a classic detective mystery with the dynamic adaptability of modern generative AI reasoning, while maintaining strict state consistency and deterministic rules.

---

## 2. Problem Statement

Traditional detective video games rely on rigid, hardcoded branching dialog trees and fixed trigger points. Conversely, fully unconstrained LLM-driven roleplay games suffer from critical flaws:
* **Hallucination & Inconsistency**: The LLM may invent non-existent suspects, misremember established facts, or change the culprit mid-investigation.
* **Lack of Rule Enforcement**: An LLM cannot reliably enforce complex game mechanics (e.g., action point budgets, locked locations, legal evidence requirements).
* **Solvability Loss**: The mystery loses structural integrity if ground truth is fluid or non-authoritative.

DetectiveAI solves this by enforcing a strict separation between **Authoritative Game Engine Logic** (which owns ground truth, state transitions, and rules) and **AI Reasoning Workflows** (which handle natural language dialogue, contextual interpretation, and structured evaluation).

---

## 3. Goals

* **Authoritative Ground Truth**: Establish a deterministic game engine that manages mystery cases, culprit identities, motive graphs, timelines, and evidence availability.
* **AI-Augmented Gameplay**: Integrate Lamatic agent workflows to render dynamic suspect interrogations, detect statement contradictions, and evaluate complex detective hypotheses.
* **Modular Python Architecture**: Build a clean, decoupled backend using FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, and Ruff.
* **Multi-Interface Architecture**: Provide a CLI-first player interface (built with Typer) while ensuring the backend REST API is ready for future Web UI integration.
* **Deterministic Testability**: Ensure game state transitions, rule evaluations, and scoring logic are 100% testable without reliance on external LLM calls.

---

## 4. Non-Goals

* **LLM-Driven Ground Truth**: The AI layer will *never* create, alter, or decide the authoritative case ground truth or culprit identity at runtime.
* **Complex Enterprise Infrastructure**: No Redis, Kafka, Celery, PostgreSQL, Docker orchestration, or microservices during initial development phases.
* **Real-time Multiplayer**: DetectiveAI is designed as a single-player interactive investigation experience.
* **Unvalidated LLM Output**: Raw LLM output will never directly mutate internal game state without backend validation.

---

## 5. High-Level Architecture

DetectiveAI follows a clean tiered architecture:

```
+-------------------------------------------------------------+
|                     Presentation Layer                      |
|          +-------------------+       +-------------------+  |
|          |    CLI (Typer)    |       |  Future Web UI    |  |
|          +---------+---------+       +---------+---------+  |
+--------------------|---------------------------|------------+
                     |                           |
                     +-------------+-------------+
                                   | (HTTP / REST)
+----------------------------------v--------------------------+
|                        API Layer                            |
|                    FastAPI Endpoints                        |
+----------------------------------+--------------------------+
                                   |
+----------------------------------v--------------------------+
|                       Game Engine                           |
|      - State Machine           - Deterministic Rules        |
|      - Action Validator        - Scoring & Timeline          |
+-------------------+----------------------+------------------+
                    |                      |
      (Persistence) |                      | (Structured Tasks)
+-------------------v---+          +-------v------------------+
|    Database Layer     |          |   Future Lamatic Layer   |
| (SQLAlchemy / SQLite) |          | (AI Reasoning & Agents)  |
+-----------------------+          +--------------------------+
```

---

## 6. Component Responsibilities

| Component | Tech Stack | Key Responsibilities |
| :--- | :--- | :--- |
| **FastAPI** | Python 3.12, FastAPI | HTTP routing, request/response validation, API docs, session entrypoints. |
| **Scenario Layer** | Python 3.12, Pydantic | Version-controlled scenario JSON definitions, registry discovery, loader service, integrity & cross-reference validation. |
| **Game Engine** | Python 3.12, Pydantic | State transitions, action validation, rule execution, scoring, timeline progression. |
| **Database** | SQLAlchemy, SQLite | Persisting active player sessions, case ground-truth static data, action logs. |
| **Lamatic Layer** | Lamatic Agent Workflows | Dialogue generation, evidence interpretation, contradiction analysis, solution grading. |
| **CLI** | Typer, Rich | Console user interface, command parser, rich text formatting for terminal play. |
| **Web UI** | HTML/JS / React (Future) | Graphical interface, visual evidence board, interactive interrogation screen. |

---

## 7. FastAPI Responsibility

The FastAPI application serves as the API gateway and orchestrator:
* Exposes clean RESTful API endpoints for CLI and future Web UI clients.
* Enforces request input validation and response serialization using Pydantic schemas.
* Manages session lifecycle and coordinates request execution with the core Game Engine.
* Provides health check (`GET /health`) and OpenAPI documentation (`/docs`, `/redoc`).

---

## 8. Game Engine Responsibility

The Game Engine is the deterministic heart of DetectiveAI:
* **Authoritative Ground Truth**: Holds the immutable facts of a case (the real culprit, true motive, secret timeline, and physical evidence graph).
* **State Machine**: Tracks player progress, uncovered evidence, discovered locations, interviewed suspects, and remaining action points/time.
* **Action Validation**: Checks whether an intended player action (e.g. searching a room, asking a specific question) is legally permitted given the current state.
* **State Transitions**: Mutates player state only when actions succeed, recording event logs and updating scores.
* **Scoring & Penalties**: Computes investigation efficiency, tracks wrong accusations, and calculates final detective rank.

---

## 9. Database Responsibility

The database layer provides persistent storage for cases and active games:
* **Case Definitions**: Stores case static ground-truth metadata, locations, initial suspect profiles, and evidence items.
* **Player Sessions**: Stores active game states, player inventories, unlocked locations, and notebook/hypothesis logs.
* **Audit Trail**: Logs all player actions chronologically for timeline views and scoring reviews.
* **SQLite Storage**: Uses SQLite for lightweight, zero-dependency, zero-configuration local development.

---

## 10. Scenario Management Layer

The Scenario Management Layer provides a scenario-agnostic system for defining, loading, validating, and discovering mystery cases:

```
Scenario Files
      ↓
Scenario Registry
      ↓
Scenario Loader
      ↓
Pydantic Validation
      ↓
Validated Scenario
      ↓
Game Engine
```

Key principles of the Scenario Layer:
* **Version-Controlled & Deterministic**: Scenarios are stored as structured, human-readable JSON definition files under `scenarios/<scenario_id>/`.
* **Database Independent**: Scenario loading and validation are completely decoupled from database mutations. Scenarios remain input/configuration models (`ScenarioDefinition`).
* **Rigorous Integrity Validation**: Cross-entity references (e.g. evidence locations, timeline suspects, solution culprit, stage requirements) and semver format are validated deterministically before a scenario is accepted.
* **Ground Truth Separation**: Authoritative ground-truth data (culprit identity, motives, secret timeline events, solution details) is loaded for backend validation but strictly isolated from player-facing schemas (`PublicScenarioDefinition`).

---

## 11. Deterministic Game Engine & Investigation Lifecycle

The Game Engine serves as the central, authoritative state machine governing investigation sessions:

```
Scenario Layer (Immutable World)
      ↓
Game Session (Player-Specific Mutable State)
      ↓
Game Engine (Authoritative Action Validation & Rule Engine)
      ↓
State Transition (Progress, Stage, Score, Discoveries)
      ↓
GameEvent Audit Log (Append-Only Event Stream)
```

Key principles of the Game Engine architecture:
* **Scenario Immutability**: The scenario definition remains immutable throughout gameplay.
* **Player Session Isolation**: `GameSession` encapsulates player-specific mutable state (current location, stage, discovered evidence, interviewed suspects, visited locations, score).
* **Central Action Validation**: All investigation actions (`MOVE`, `INSPECT`, `INTERVIEW`, `EXAMINE_EVIDENCE`, `ADVANCE_STAGE`, `SUBMIT_SOLUTION`) pass through `GameEngine.execute_action()`.
* **Append-Only Audit Log**: Every executed action creates a persistent `GameEvent` record documenting the session ID, action type, target type, target ID, timestamp, and structured output.
* **Non-Mutating AI Boundary**: AI/Lamatic agents operate strictly on top of this engine and cannot directly mutate authoritative game state.

---

## 12. Future Lamatic Responsibility

Lamatic will provide AI reasoning, agent orchestration, and natural language generation without owning game truth:
* **Suspect Dialogue**: Generates dynamic, in-character suspect responses constrained by the suspect's current emotional state and known facts.
* **Contextual Interpretation**: Formulates clues and observations from physical evidence based on player skill and approach.
* **Contradiction Detection**: Analyzes player hypotheses and suspect statements to flag logical inconsistencies.
* **Investigation Assistance**: Generates subtle hints or detective reasoning summaries when requested.
* **Solution Reasoning Evaluation**: Evaluates the subjective quality of the player's final written solution against the true case solution.

---

## 11. CLI Responsibility

The Command Line Interface (CLI) is the initial primary interface for players:
* Built with `Typer` and formatted using rich terminal components.
* Translates player terminal input (commands like `inspect`, `talk`, `accuse`) into API requests to the FastAPI engine.
* Displays game responses, suspect dialogue, maps, and case notebooks cleanly in the terminal.

---

## 12. Future Web UI Responsibility

The future Web UI will provide a graphical experience for non-terminal players:
* Interacts with the backend via the exact same FastAPI REST endpoints used by the CLI.
* Renders visual location maps, interactive evidence pinboards, audio/text suspect interrogations, and timeline graphs.

---

## 13. CLI Presentation Adapter Layer

The Command Line Interface (CLI) serves as a presentation adapter over application services:

```
CLI Presentation Layer (Typer / Rich)
  │
  ├──────> GameEngine (Authoritative State Machine) ──> Database Layer
  │
  └──────> Lamatic Adapter (LamaticClient / DetectiveAgent) ──> Lamatic AgentKit Agent
```

Key principles of the CLI Layer:
* **Zero Gameplay Rules**: The CLI contains no game rules, evidence discovery logic, or stage progression logic.
* **Strict Adapter Pattern**: Translates terminal commands into `GameActionDTO` objects and delegates execution to `GameEngine.execute_action()`.
* **Isolated AI Adapter**: CLI requests to the Lamatic agent route through `LamaticClient` / `DetectiveAgent`. The Lamatic adapter is intentionally isolated from the deterministic `GameEngine`.
* **Confidentiality Preservation**: Consumes player-facing DTOs (`GameStateDTO`, `ActionResultDTO`) to format terminal output without revealing ground truth (`culprit_id`, `motive`, secret timeline).
* **Persistent Sessions**: Uses local database sessions (`SessionLocal()`) allowing players to start an investigation, exit the terminal, and resume the session later (`python -m cli play <session_id>`).

---

## 14. Authoritative Game State Principle

The fundamental architectural constraint of DetectiveAI is:

> **The backend game engine is the sole authoritative source of truth. The LLM/Lamatic layer is an untrusted reasoning worker.**

Key rules enforcing this principle:
1. **No State Mutation by LLM**: Lamatic agent outputs cannot directly modify database tables or game state flags.
2. **Structured AI Validation**: All responses from Lamatic must be parsed into strictly typed Pydantic models and validated by the Game Engine before state updates occur.
3. **Ground Truth Confidentiality**: Lamatic agents only receive the subset of facts that the suspect or evidence is allowed to know at that moment, preventing accidental spoilers or hallucinations.

---

## 15. AI Tool Boundary & Investigation Context Architecture

The AI layer interacts with DetectiveAI through an explicit, player-safe boundary:

```
Lamatic Agent (DetectiveAgent)
      ↓
InvestigationContext (Player-Safe Whitelisted State)
      ↓
InvestigationTools (Application Tool Boundary)
      ↓
GameEngine (Authoritative Validation & Rule Engine)
      ↓
Database Layer (SQLAlchemy / SQLite)
```

Core Principles:
* **The AI is an investigator, not the game engine**: The AI reasons over permitted information (`InvestigationContext`) and requests actions through tools (`InvestigationTools`). The deterministic `GameEngine` validates and executes all state changes.
* **No Direct DB or Ground Truth Access**: `DetectiveAgent` never receives ORM models (`GameSession`, `Case`, `Suspect`), `ScenarioDefinition` ground truth, `culprit_id`, `motive`, or `solution.json`.
* **Action Tools Delegate to Engine**: All action tools (`move_to_location`, `inspect_location`, `interview_suspect`, `examine_evidence`, `advance_stage`) delegate directly to `GameEngine.execute_action()`.

---

## 16. High-Level Investigation Flow

When a player performs an action during investigation, the control flow proceeds as follows:

```
Player
  ↓
CLI / Web UI
  ↓
FastAPI
  ↓
Game Engine
  ↓
Validate Action
  ↓
Execute deterministic rules
  ↓
Invoke Lamatic only when AI reasoning is required
  ↓
Validate structured AI result
  ↓
Update game state
  ↓
Record event
  ↓
Return result to player
```

---

## 15. Planned AI Agent Architecture

Future milestones will introduce specialized Lamatic agents, each with a tightly bounded responsibility:

* **Suspect Agent**: Simulates individual suspects during interviews. Prompts are injected only with facts the suspect actually knows or wants to lie about.
* **Evidence Agent**: Generates detailed physical or forensic descriptions of evidence items discovered by the player.
* **Contradiction Agent**: Compares suspect statements against physical evidence and timeline events to flag discrepancies.
* **Detective Reasoning Agent**: Assists the player by summarizing known facts, linking clues, or offering structural hints.
* **Game Director**: Monitors player pacing, frustration, and action count to dynamically adjust narrative tension.
* **Solution Evaluator**: Graded evaluation agent that reviews the player's final case submission (culprit, motive, evidence chain) against ground truth.

*(Note: None of these agents are implemented in Milestone 0.)*

---

## 17. AI-Powered Suspect Interrogation Architecture

The conversational suspect interrogation flow proceeds as follows:

```
                  Player
                    │
                    ▼
                GameEngine
                    │
            interview valid?
                    │
                    ▼
            SuspectKnowledge
                    │
                    ▼
              SuspectAgent
                    │
                    ▼
               Lamatic Flow
                    │
                    ▼
             Suspect Response
                    │
                    ▼
                  Player
```

Core Principles:
* **Separation of Reality vs Conversation**: "The GameEngine determines whether an interrogation is valid. The SuspectAgent determines how the suspect responds."
* **Ground-Truth Confidentiality**: `SuspectKnowledge` is built from public scenario definitions by `SuspectKnowledgeBuilder`. Ground-truth fields (`is_culprit`, `culprit_id`, `motive`, secret timeline events) are strictly stripped.
* **Persistent Dialogue History**: Multi-turn dialogue exchanges are saved into `GameEvent` (`event_type="INTERVIEW_DIALOGUE"`, `target_type="suspect"`) preserving turn history per suspect without modifying database schemas.

---

## 18. AI-Powered Evidence Examination Architecture

The AI forensic evidence examination flow proceeds as follows:

```
                  Player
                    │
                    ▼
                GameEngine
                    │
            evidence discovered?
                    │
                    ▼
            EvidenceKnowledge
                    │
                    ▼
              EvidenceAgent
                    │
                    ▼
          Lamatic Evidence Flow
                    │
                    ▼
          AI Forensic Analysis
                    │
                    ▼
                  Player
```

Core Principles:
* **Untrusted Reasoning Worker**: The `EvidenceAgent` generates physical observations, forensic interpretations, and follow-up avenues. The deterministic `GameEngine` remains the sole authority over evidence existence, discovery, and state transitions.
* **Ground-Truth Confidentiality**: `EvidenceKnowledge` is built by `EvidenceKnowledgeBuilder` from `PublicScenarioDefinition`, excluding ground-truth solutions (`solution_summary`, `culprit_id`, `is_culprit`, `motive`) and secret discovery metadata.
* **Offline Game Engine Fallback**: If Lamatic credentials are unset or unreachable, `GameEngine` completes deterministic evidence examination gracefully without breaking gameplay.

---

## 19. AI Case Resolution & Reasoning Evaluation Architecture

The final case solution submission and evaluation flow proceeds as follows:

```
                  Player
                    │
                    ▼
        SolutionSubmission DTO
                    │
                    ▼
        SolutionEvaluationService
         ┌──────────┴──────────┐
         ▼                     ▼
    GameEngine         SolutionEvaluator
    (Objective)           (Subjective)
   • Culprit ID?        • Evidence score (20%)
   • Evidence IDs?      • Motive score (15%)
   • Culprit correct?   • Reasoning score (20%)
     (+30 pts)          • Timeline score (15%)
         │                     │
         └──────────┬──────────┘
                    ▼
           SolutionEvaluation
             (Total 100 pts)
                    │
                    ▼
           Session Status Update
             (SOLVED / FAILED)
```

Scoring Mechanism:
* **Culprit Correctness (30%)**: Authoritative objective check performed by `GameEngine` / `SolutionEvaluationService` comparing accused culprit ID against ground-truth culprit ID.
* **Evidence Relevance & Support (20%)**: Subjective AI evaluation of supporting evidence items cited by player.
* **Motive Reasoning (15%)**: Subjective AI evaluation of player's motive explanation.
* **Reasoning Quality & Logic (20%)**: Subjective AI evaluation of logical connection between evidence and culprit.
* **Timeline Reconstruction (15%)**: Subjective AI evaluation of crime timeline sequence explanation.

Core Principles:
* **Hybrid Objective + Subjective Model**: `GameEngine` determines objective culprit correctness, session completion, and state transitions. `SolutionEvaluator` provides subjective reasoning quality evaluation.
* **Ground-Truth Protection**: Neither the player nor `SolutionEvaluator` receives secret scenario ground truth (`solution_summary`, `culprit_id`, `motive`, secret timeline events). The evaluator reviews player reasoning solely against established public facts.
* **Deterministic Fallback**: If Lamatic credentials are unavailable, `SolutionEvaluationService` applies deterministic scoring rules without crashing.

---

## 20. Development Phases

* **Milestone 0**: Project foundation, modern `pyproject.toml` setup, FastAPI app skeleton, `/health` endpoint, pytest harness, Ruff configuration, architecture documentation.
* **Milestone 1**: Core Domain Models & Database Schema (Case, Suspect, Location, Evidence, GameState) using SQLAlchemy & Pydantic.
* **Milestone 2**: Scenario Definition, Loader, Integrity Validator, Discovery Registry, and Ground-Truth Isolation.
* **Milestone 3**: Game State and Investigation Lifecycle (Deterministic Game Engine, Session Service, Action Validation, Audit Log).
* **Milestone 4**: CLI Investigation Interface (Typer CLI, Interactive REPL, Command Mapping, Confidentiality Formatting).
* **Milestone 5A**: Lamatic AgentKit Integration Spike (Official SDK Adapter, Connectivity Prototype, Configuration, Testing Harness).
* **Milestone 5B**: Investigation Context & AI Tool Boundary (`InvestigationContext`, `InvestigationTools`, explicit player-safe whitelisting, `GameEngine` delegation).
* **Milestone 5C**: AI-Powered Suspect Interrogation (`SuspectKnowledge`, `SuspectKnowledgeBuilder`, `SuspectAgent`, `SuspectConversationManager`, CLI `interrogate` subshell).
* **Milestone 5D**: AI-Powered Evidence Examination (`EvidenceKnowledge`, `EvidenceKnowledgeBuilder`, `EvidenceAgent`, `LAMATIC_EVIDENCE_FLOW_ID`, CLI `examine` AI analysis).
* **Milestone 6**: AI Case Resolution & Reasoning Evaluation (`SolutionSubmission`, `SolutionEvaluation`, `SolutionEvaluator`, `SolutionEvaluationService`, `LAMATIC_SOLUTION_FLOW_ID`, CLI `solve` interactive command).
* **Milestone 7**: FastAPI Application & REST API Layer (API router `/api/v1`, scenario endpoints, session lifecycle, deterministic action execution, AI interrogation & examination endpoints, solution evaluation, standardized error envelopes, zero ground-truth leakage guarantee).

---

## 21. Application Logging Architecture

DetectiveAI implements a standardized, production-quality logging framework built on Python's built-in `logging` module:

```
FastAPI Server Startup / Typer CLI Execution
                  │
                  ▼
       configure_logging() (app/core/logging.py)
       ┌──────────┴──────────┐
       ▼                     ▼
  StreamHandler      RotatingFileHandler
 (sys.stdout console) (logs/detective_ai.log)
                      • 10 MB maxBytes
                      • 5 backupCount
                      • UTF-8 encoding
                      • Format: %(asctime)s | %(levelname)s | %(name)s |
                                %(filename)s:%(lineno)d | %(funcName)s | %(message)s
```

### Logging Principles & Design Constraints
1. **Centralized Configuration**: `configure_logging()` in `app/core/logging.py` serves as the single source of truth for logging configuration. It is idempotent and prevents duplicate log emission.
2. **Metadata-Rich Formatter**: Uses standard log record attributes `%(asctime)s`, `%(levelname)s`, `%(name)s`, `%(filename)s:%(lineno)d`, `%(funcName)s`, and `%(message)s` for traceability.
3. **Log Rotation**: Implemented via `RotatingFileHandler` with 10 MB maximum file size and 5 rotating backups to avoid unbounded disk growth.
4. **Latency & Observability**:
   - `LamaticClient` records execution duration (`duration_ms = (time.perf_counter() - start_time) * 1000`) for all AI workflow invocations.
   - `GameEngine` records all player action transitions, stage advancement criteria checks, and validation failures.
5. **Confidentiality & Secret Isolation**:
   - Secrets, API keys (`LAMATIC_API_KEY`), and Bearer tokens are never logged.
   - Ground truth fields (`solution.culprit_id`, `is_culprit`, secret events) are excluded from logs.

---

## 22. FastAPI REST API Layer (Milestone 7)

DetectiveAI provides a complete RESTful API layer under `/api/v1`, serving as a thin presentation adapter over the authoritative `GameEngine`, `SessionService`, `ScenarioRegistry`, and Lamatic agent services.

### API Architecture & Design Rules
1. **Presentation Adapter Only**: The FastAPI layer contains zero business or game rules. All state transitions, validations, stage requirements, and scoring are delegated directly to backend services.
2. **Standardized Error Envelope**: All domain, scenario, Lamatic, and validation errors are mapped to consistent JSON responses:
   ```json
   {
     "error": {
       "code": "SESSION_NOT_FOUND",
       "message": "Session '...' does not exist."
     }
   }
   ```
3. **Zero Ground-Truth Leaks**: Player-facing endpoints strictly omit confidential fields (`culprit_id`, `is_culprit`, `motive`, `solution_summary`, secret timeline events, undiscovered evidence).

### Endpoint Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Application health check returning `{"status": "ok", "version": "0.1.0"}` |
| `GET` | `/api/v1/scenarios` | List player-safe summaries of registered scenarios |
| `GET` | `/api/v1/scenarios/{id}` | Inspect player-safe details of a scenario |
| `POST` | `/api/v1/sessions` | Create and start a new game session (`{"scenario": "the_midnight_archive"}`) |
| `GET` | `/api/v1/sessions/{id}` | Get player-facing `GameStateDTO` |
| `GET` | `/api/v1/sessions/{id}/context` | Get player-safe `InvestigationContext` |
| `GET` | `/api/v1/sessions/{id}/available-actions` | Get dynamically permitted actions for current state |
| `GET` | `/api/v1/sessions/{id}/history` | Get chronological player-visible audit event history |
| `POST` | `/api/v1/sessions/{id}/actions` | Execute deterministic action (`move`, `inspect`, `interview`, `examine_evidence`, `advance`) |
| `POST` | `/api/v1/sessions/{id}/suspects/{suspect_id}/interrogate` | Perform AI dialogue interrogation turn with a suspect |
| `POST` | `/api/v1/sessions/{id}/evidence/{evidence_id}/examine` | Examine evidence with deterministic update and AI forensic analysis |
| `POST` | `/api/v1/sessions/{id}/solve` | Submit case solution hypothesis for rubric scoring and evaluation |


