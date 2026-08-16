# Architecture

## System boundaries

The simulation engine is a pure domain component. Its primary contract is:

```text
GameState + PlayerActions -> GameState + TurnReport
```

It must not depend on FastAPI, SQLAlchemy, UI code, wall-clock time, or global
random state. Given the same initial state, random seed/state, and player
actions, it must return the same state and report.

API, schemas, domain models, engine behavior, persistence, and configuration
data remain separate. Route handlers validate and coordinate requests; they do
not contain economic formulas. The frontend displays explanations returned by
the API and does not reimplement simulation formulas.

## Technology

### Backend

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for the MVP
- Alembic migrations
- Pytest
- Ruff
- A seeded Python random generator behind an event service

### Frontend

The planned client uses React, TypeScript, Vite, TanStack Query, React Router,
Recharts, Zod, and a small CSS Modules or design-token layer. Frontend work is
outside the current backend-only scope unless explicitly requested.

## Backend package structure

```text
backend/
  app/
    api/
      campaigns.py
      turns.py
      policies.py
      saves.py
    domain/
      state.py
      resources.py
      production.py
      population.py
      government.py
      politics.py
      foreign.py
      crises.py
    engine/
      turn_engine.py
      pricing.py
      events.py
      explanations.py
    persistence/
      models.py
      repositories.py
    schemas/
      requests.py
      responses.py
    data/
      policies.json
      events.json
      scenarios.json
```

Milestones should add only the modules needed for their scope. Empty speculative
modules are not required. Balance values and content belong in data or
configuration so tuning does not require engine changes.

## Domain model

The planned core entities are `Campaign`, `GameState`, `ResourceState`,
`SectorState`, `PopulationState`, `PopulationGroupState`, `GovernmentState`,
`PolicyState`, `ForeignNationState`, `CrisisState`, `TurnAction`, `TurnReport`,
and `MetricExplanation`.

For MVP simplicity, persistence stores a full state snapshot after every
completed turn. The campaign also stores the seed and random-generator state so
saves preserve deterministic futures. A completed turn is atomic: validation,
resolution, snapshot persistence, and report persistence either all succeed or
leave the prior state unchanged.

## Initial API direction

```text
POST   /api/campaigns
GET    /api/campaigns/{campaign_id}
DELETE /api/campaigns/{campaign_id}
GET    /api/campaigns/{campaign_id}/state
POST   /api/campaigns/{campaign_id}/turns
GET    /api/campaigns/{campaign_id}/turns/{turn_number}
GET    /api/campaigns/{campaign_id}/history
GET    /api/campaigns/{campaign_id}/policies
POST   /api/campaigns/{campaign_id}/policies/{policy_id}/adopt
GET    /api/campaigns/{campaign_id}/crises
POST   /api/campaigns/{campaign_id}/crises/{crisis_id}/responses
POST   /api/campaigns/{campaign_id}/save
POST   /api/saves/{save_id}/load
```

These endpoints describe the target MVP, not Milestone 0 requirements. The
end-turn request eventually contains labor allocation, budget, trade orders,
investment, and a crisis response. Its response includes new state, a turn
report, explanations, warnings, and game-over status.

## Milestone 3 policy boundary

Policy adoption is part of `PlayerActions` submitted to the end-turn endpoint,
so costs, reactions, simulation resolution, reports, and persistence share one
atomic transaction. `GET /api/campaigns/{campaign_id}/policies` is a read-only
catalog projection reporting active policies, transitions, and blockers. A
separate mutating adoption endpoint is deferred to avoid a second non-atomic
simulation path.

`PolicyState` and `PoliticsState` are pure domain snapshots. Eligibility and
political formulas live in engine modules; routes coordinate validated inputs
and persistence. Definitions and tunable values are loaded from checked-in JSON.

## Milestone 4 trade and foreign boundary

Trade orders are part of `PlayerActions` and settle inside the existing atomic
end-turn transaction. The engine resolves production, trade, consumption,
prices, government finance, foreign relations, and politics in that order.
`GET /api/campaigns/{campaign_id}/foreign` is a read-only projection of the
three persisted foreign actors.

`ForeignState` is a pure domain snapshot. `engine/trade.py` owns inventory and
reserve settlement; `engine/foreign.py` owns trust, relations, debt claims,
dependence, pressure, and ordered escalation. Actor baselines and market
capacity live in `data/foreign_nations.json`; routes contain no trade formulas.

## Testing architecture

- Unit tests for formulas and state transitions.
- Golden-seed tests for determinism.
- Invariant/property tests for legal state.
- Scenario tests for cross-system causal behavior.
- Soak tests of 500–2,000 automated turns for stability and balance.

Source: [Economic Simulator — MVP Product & Engineering Plan](https://app.notion.com/p/3b988d2fa3f381f7a832e2b687d12d15)
