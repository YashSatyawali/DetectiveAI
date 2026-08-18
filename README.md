# DetectiveAI

An interactive AI-powered detective investigation engine backend and CLI game.

## Overview

DetectiveAI allows players to investigate fictional mystery cases by listing suspects, searching locations, interviewing suspects, discovering evidence, tracking timelines, and submitting final case solutions.

The core architecture strictly separates **authoritative game state and deterministic logic** (handled by the Game Engine and Session Service) from **AI reasoning & agent behavior** (powered by Lamatic AgentKit workflows).

## Features & Architecture

* **Authoritative Game Engine**: Deterministic state transitions, action validations, stage requirements, and audit event logs.
* **REST API Layer (FastAPI)**: Versioned `/api/v1` endpoints for sessions, actions, suspect interrogation, forensic evidence examination, and solution grading.
* **AI Interrogation & Examination**: Multi-turn dialogue with suspects and forensic evidence analysis via Lamatic AgentKit workflows with offline fallback support.
* **Rich CLI Interface**: Typer and Rich console presentation adapter with interactive subshells, colored evidence tags, and AI markdown rendering.
* **Zero Ground-Truth Leaks**: Strict isolation ensuring players and AI agents never receive confidential case solutions or hidden events.

## Quick Start

### 1. Environment Setup

Create and activate a virtual environment (Python 3.12+ required):

```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate
```

Install project dependencies in editable mode:

```bash
pip install -e ".[dev]"
```

### 2. Running the FastAPI Server

Start the FastAPI application with Uvicorn:

```bash
python -m uvicorn app.main:app --reload
```

The server will be available at:
* Health Endpoint: `http://127.0.0.1:8000/health`
* Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
* Versioned API Base: `http://127.0.0.1:8000/api/v1`

### 3. REST API Quick Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Application health check |
| `GET` | `/api/v1/scenarios` | List player-safe scenario summaries |
| `GET` | `/api/v1/scenarios/{id}` | Inspect player-safe scenario details |
| `POST` | `/api/v1/sessions` | Start new session (`{"scenario": "the_midnight_archive"}`) |
| `GET` | `/api/v1/sessions/{id}` | Retrieve session state |
| `GET` | `/api/v1/sessions/{id}/context` | Retrieve player-safe investigation context |
| `GET` | `/api/v1/sessions/{id}/available-actions` | Retrieve permitted player actions |
| `GET` | `/api/v1/sessions/{id}/history` | Retrieve chronological audit event log |
| `POST` | `/api/v1/sessions/{id}/actions` | Execute deterministic action (`move`, `inspect`, `interview`, `examine_evidence`, `advance`) |
| `POST` | `/api/v1/sessions/{id}/suspects/{suspect_id}/interrogate` | Interrogate suspect via AI dialog (`{"message": "..."}`) |
| `POST` | `/api/v1/sessions/{id}/evidence/{evidence_id}/examine` | Examine evidence with AI forensic interpretation |
| `POST` | `/api/v1/sessions/{id}/solve` | Submit case hypothesis for scoring and feedback |

### 4. CLI Usage

Discover scenarios, start investigations, execute actions, and enter interactive play mode via Typer CLI:

```bash
# List all available scenarios
python -m cli scenarios

# Start a new investigation session for a scenario
python -m cli start the_midnight_archive

# View player-facing game state for a session
python -m cli state <session_id>

# Execute a single investigation action (inspect, move, interview, examine, advance, solve)
python -m cli action <session_id> inspect
python -m cli action <session_id> move location_02
python -m cli action <session_id> examine evidence_02
python -m cli action <session_id> interview suspect_02
python -m cli action <session_id> advance
python -m cli action <session_id> solve "Sofia Bennett"

# View chronological audit event history for a session
python -m cli history <session_id>

# Enter interactive investigation shell
python -m cli play <session_id>
```

### 5. Running Quality & Verification Tools

Run tests with `pytest`:

```bash
pytest
```

Run linter and formatting checks with `ruff`:

```bash
ruff check .
ruff format --check .
```

# Lamatic AgentKit

DetectiveAI integrates with the official **Lamatic AgentKit** Python SDK (`lamatic`) to enable AI-powered reasoning and conversational agents.

### Configuration

Set the following environment variables (or define them in `.env`):

```env
LAMATIC_ENDPOINT=https://your-project.lamatic.ai/api/graphql
LAMATIC_PROJECT_ID=your-project-id
LAMATIC_API_KEY=your-api-key
LAMATIC_FLOW_ID=your-flow-id
```

### Running the Test Command

Test the context-aware Lamatic agent directly from the CLI:

```bash
# Standalone prompt
python -m cli ask "What makes a good detective?"

# Context-aware prompt using active investigation session context
python -m cli ask "What should I investigate next?" --session-id <session_id>

# AI-Powered Suspect Interrogation subshell
python -m cli interrogate <session_id> <suspect_id>

# AI-Powered Evidence Forensic Analysis
python -m cli examine <session_id> <evidence_id>

# AI Case Resolution & Reasoning Evaluation
python -m cli solve <session_id>
```

> **Note**: Case resolution evaluates objective culprit correctness (30%) via `GameEngine` and subjective reasoning quality (70%) via `SolutionEvaluator`. Scenario ground truth is strictly protected and never exposed to the player or LLM.

## Repository Structure

```
detective-ai/
├── app/
│   ├── api/          # FastAPI routers and endpoints
│   ├── core/         # Configuration, constants, security
│   ├── db/           # Database sessions, engine, migrations
│   ├── models/       # SQLAlchemy ORM models and Pydantic schemas
│   ├── services/     # Business logic & game engine deterministic rules
│   └── lamatic/      # Future Lamatic AI integration layer
├── cli/              # Command Line Interface (Typer)
├── scenarios/        # Case ground-truth scenarios and static data
├── tests/            # Automated test suite
│   ├── unit/         # Unit tests for deterministic rules
│   └── integration/  # API and flow integration tests
├── docs/             # Architecture and design documentation
│   └── architecture.md
├── .env.example      # Example environment variables
├── .gitignore        # Git ignore specifications
├── pyproject.toml    # Project dependencies and tool settings
└── README.md         # Project documentation
```

## Application Logging

DetectiveAI features a centralized application logging system using Python's standard `logging` library.

### Key Highlights
- **Centralized Configuration (`app/core/logging.py`)**: Initialized automatically on FastAPI and CLI startup (`configure_logging()`).
- **Rotating File Handler**: Writes to `logs/detective_ai.log` with automatic rotation at 10 MB (`maxBytes=10*1024*1024`) and 5 backup files (`backupCount=5`) encoded in UTF-8. The `logs/` directory is created automatically if not present.
- **Structured Metadata Format**:
  ```text
  %(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s
  ```
- **Operational Coverage**:
  - `GameEngine`: Action validation, stage requirements checking, and state progression.
  - `SessionService` & `ScenarioLoader`/`ScenarioRegistry`: Session lifecycle and scenario catalog discovery.
  - `InvestigationTools`: Tool invocations and authoritative rule enforcement.
  - `LamaticClient`: Flow invocation start, duration tracking (`duration_ms`), status codes, and network error handling.
  - `SuspectAgent`, `EvidenceAgent`, `SolutionEvaluator`: Agent requests and execution lifecycle.
  - `CLI Commands`: User command invocations, parameter inputs, and warnings/errors.
- **Security & Confidentiality**:
  - Raw API keys, authorization headers, and bearer tokens are strictly omitted.
  - Scenario ground truth (`solution.json`, secret events, ground-truth culprit) is never written to log sinks.

## Architecture

For details on component responsibilities, state authority principles, AI agent architecture, and development phases, see [`docs/architecture.md`](docs/architecture.md).

