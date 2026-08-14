# Econ Sim

An open-ended, turn-based economic strategy simulator. The player governs a
small agrarian country, develops its institutions and productive capacity, and
tries to keep the regime viable as scarcity, debt, inequality, demographic
change, and foreign pressure accumulate.

The MVP uses a Python/FastAPI backend and a TypeScript/React frontend. Current
development scope is the backend unless frontend work is explicitly requested.

## Project documents

- [MVP.md](MVP.md) defines product scope and delivery milestones.
- [ARCHITECTURE.md](ARCHITECTURE.md) defines system boundaries and structure.
- [SIMULATION_RULES.md](SIMULATION_RULES.md) records the agreed simulation
  behavior and formulas.
- [DECISIONS.md](DECISIONS.md) records binding product and engineering choices.

Source: [Economic Simulator — MVP Product & Engineering Plan](https://app.notion.com/p/3b988d2fa3f381f7a832e2b687d12d15)

## Backend setup

Requirements: Python 3.12 or newer.

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

Run the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

The health check is available at `http://127.0.0.1:8000/health`.

Create a deterministic campaign:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/campaigns `
  -ContentType application/json `
  -Body '{"seed":42,"scenario_id":"agrarian_start"}'
```

Complete a turn by posting the campaign's current turn and a labor allocation
for all five sectors to `/api/campaigns/{campaign_id}/turns`. Interactive API
documentation is available at `http://127.0.0.1:8000/docs`.

Use `ECON_SIM_DATABASE_URL` to override the default
`sqlite:///./econ_sim.db` database URL.

## Backend verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\ruff.exe check backend
.\.venv\Scripts\ruff.exe format --check backend
```
