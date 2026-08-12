# Project Instructions

## Product

This repository contains an open-ended, turn-based economic simulator.

Read these files before planning or changing code:

- `docs/MVP.md`
- `docs/ARCHITECTURE.md`
- `docs/SIMULATION_RULES.md`
- `docs/DECISIONS.md`

If the requested work conflicts with those documents, stop and identify
the conflict before editing.

## Current scope

Backend MVP only unless the user explicitly requests frontend work.

Backend stack:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Alembic
- Pytest
- Ruff

Do not add frontend code until explicitly requested.

## Architecture

Keep the simulation engine independent of FastAPI, SQLAlchemy, and the UI.

The primary engine contract is:

`GameState + PlayerActions -> GameState + TurnReport`

Simulation code must be deterministic when given the same:

- Initial state
- Random seed/state
- Player actions

Keep API, domain, engine, and persistence concerns separate.

Do not place economic formulas in route handlers.

## Working method

- Work on only the requested milestone or subsystem.
- Inspect existing code before proposing changes.
- In Plan mode, do not edit files.
- Before implementation, state the files expected to change.
- Do not expand scope without approval.
- Prefer small, reviewable changes.
- Do not refactor unrelated code.
- Preserve user changes in the working tree.
- Do not commit, push, create branches, or open pull requests unless the
  user explicitly requests that exact action.
- After implementation, show the changed files and summarize the diff.

## Testing

Every implemented rule requires tests.

At minimum, run:

- Unit tests for changed behavior
- Full backend test suite
- Ruff
- Relevant type checking, if configured

Important invariants:

- Population cannot be negative.
- Resource inventory cannot be negative.
- Assigned labor cannot exceed available labor.
- A completed turn is atomic.
- Identical seeds and actions produce identical results.
- Crisis countdowns cannot skip states.
- Simulation code must not depend on wall-clock time.

Do not declare work complete if relevant tests fail.

## Simulation design

- Policies must have benefits and costs.
- Major state changes must include causal explanations.
- Avoid arbitrary time-based damage when pressure can emerge from state.
- Clamp or validate formulas that can produce numerical instability.
- Put tunable balance values in configuration or data files.
- Do not silently change an established formula.
- Document new formulas and their units.
