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

### 3. Running Quality & Verification Tools

Run tests with `pytest`:

```bash
pytest
```

Run linter and formatting checks with `ruff`:

```bash
ruff check .
ruff format --check .
```

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
