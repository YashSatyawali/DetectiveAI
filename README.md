# DetectiveAI

An interactive AI-powered detective investigation engine backend and CLI game.

## Overview

DetectiveAI allows players to investigate fictional mystery cases by listing suspects, searching locations, interviewing suspects, discovering evidence, tracking timelines, and submitting final case solutions.

The core architecture strictly separates **authoritative game state and deterministic logic** (handled by FastAPI / Python backend engine) from **AI reasoning & agent behavior** (to be powered by Lamatic in future milestones).

## Milestone 0 Status

Milestone 0 establishes the foundation and architecture:
* Clean Python project structure using `pyproject.toml`
* FastAPI application base with `/health` endpoint
* Pytest test harness and Ruff linting configuration
* Comprehensive architecture specification in [`docs/architecture.md`](docs/architecture.md)

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
uvicorn app.main:app --reload
```

The server will be available at:
* Health Endpoint: `http://127.0.0.1:8000/health`
* Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
* OpenAPI Schema: `http://127.0.0.1:8000/openapi.json`

### 3. CLI Usage

Discover scenarios, start investigations, execute actions, and enter interactive play mode via Typer CLI:

```bash
# List all available scenarios
python -m cli scenarios

# Start a new investigation session for a scenario
python -m cli start test_case

# View player-facing game state for a session
python -m cli state <session_id>

# Execute a single investigation action (inspect, move, interview, examine, advance, solve)
python -m cli action <session_id> inspect
python -m cli action <session_id> move location_01
python -m cli action <session_id> examine evidence_01
python -m cli action <session_id> interview suspect_01
python -m cli action <session_id> advance
python -m cli action <session_id> solve suspect_01

# View chronological audit event history for a session
python -m cli history <session_id>

# Enter interactive investigation shell
python -m cli play <session_id>
```

### 4. Running Quality & Verification Tools

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

## Architecture

For details on component responsibilities, state authority principles, AI agent architecture, and development phases, see [`docs/architecture.md`](docs/architecture.md).
