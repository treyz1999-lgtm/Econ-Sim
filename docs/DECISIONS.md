# Decisions

This log records binding product and engineering choices from the MVP plan.
Changes should be explicit; established formulas must not change silently.

## Product decisions

- The game is single-player, turn-based, and technically endless.
- One turn represents one year and resolves player choices simultaneously.
- The player governs aggregate sectors and population groups, not agents.
- The initial MVP contains one fictional agrarian scenario.
- No ideology or institutional combination is a universal endpoint.
- Difficulty is primarily emergent from state. A modest global-pressure factor
  may amplify, but never replace, underlying vulnerabilities.
- Major state changes and losses must identify causal drivers.
- Ordinary policies are tradeoffs and generally limited to one change per turn.
- Crises provide warnings and response windows rather than surprise losses.
- Revolution, insolvency, and other terminal countdowns may not skip states.
- An unresolved revolution ends the regime after a five-turn response window.
- Warfare remains abstract and economic rather than tactical.
- Campaign length is unlimited; balance targets make very long survival rare.

## Engineering decisions

- The backend uses Python 3.12+, FastAPI, Pydantic, SQLAlchemy, SQLite,
  Alembic, Pytest, and Ruff.
- The planned frontend uses TypeScript, React, and Vite, but backend work is the
  current scope unless frontend work is explicitly requested.
- The simulation engine remains independent of FastAPI, SQLAlchemy, and UI.
- The engine contract is `GameState + PlayerActions -> GameState + TurnReport`.
- Seeded inputs must be deterministic; randomness is isolated behind an event
  service and random-generator state is persisted.
- The MVP stores a complete state snapshot after every completed turn.
- Completed turns are atomic.
- Policies, scenarios, events, and tunable balance values live in JSON or other
  configuration data so balancing does not require code changes.
- API, domain, engine, persistence, schemas, and data remain separate.
- Economic formulas do not belong in route handlers or frontend code.

## Scope decisions

- Milestone 0 establishes project/tooling, backend application, health check,
  persistence foundations, tests, and local instructions only.
- Economic simulation begins in Milestone 1.
- Population and government wait until the base economic loop is deterministic.
- Foreign systems, crises, persistence completion, and balancing are delivered
  in their defined later milestones.
- Tactical warfare, multiplayer, individual agents, exact historical data,
  complex financial markets, AI-generated events, mods, multiple scenarios,
  successor regimes, cloud accounts, and online sync are outside the MVP.

## Open implementation details

The plan intentionally leaves numerical balance values, exact policy catalog,
database schema details, API error format, migration naming, and internal module
granularity to milestone-specific planning. New decisions should be appended
with rationale and date once agreed.

## 2026-08-14 — Milestone 1 economic loop

- Use immutable Pydantic domain models and `Decimal` arithmetic so engine
  behavior is portable and deterministic.
- Round quantities to four decimal places and prices to two, half-to-even, only
  at state boundaries.
- Allocate shared production inputs proportionally across all requesting
  sectors. Sector mapping order must not affect output.
- Keep annual resource demand fixed in scenario data until population-driven
  demand is introduced in Milestone 2.
- Treat construction output as reported activity during Milestone 1. It consumes
  labor, energy, and capital goods but does not modify infrastructure or sector
  capacity before Milestone 2.
- Store full JSON state snapshots and causal reports for turn zero and every
  completed turn.
- Require clients to submit `expected_turn`; a stale request returns a conflict
  and creates no snapshot.
- Persist a completed turn and campaign pointer update in one database
  transaction.
- Keep timestamps as audit metadata only. They never enter engine input.
- Use a checked-in golden-seed fixture containing reviewed SHA-256 digests of
  canonical state and report JSON. Fixture changes require explicit formula or
  balance review.

## Source

[Economic Simulator — MVP Product & Engineering Plan](https://app.notion.com/p/3b988d2fa3f381f7a832e2b687d12d15), retrieved 2026-08-13.
