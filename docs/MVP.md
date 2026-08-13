# Economic Simulator MVP

## Product vision

Build a single-player economic strategy simulator in which the player governs
a regime beginning as a low-complexity agrarian and barter economy. Across
annual turns, the player allocates labor, manages resources, adopts
institutions, trades, finances the state, and responds to demographic and
political pressure.

There is no universally correct economic system and no fixed final turn.
Campaigns become harder because growth creates complexity, commitments,
scarcity, inequality, environmental damage, and foreign exposure. Long runs
usually end through revolution, sovereign insolvency, conquest, or sustained
essential-resource collapse.

## MVP success criteria

A player can:

- Start a seeded campaign and play an unlimited number of turns.
- Allocate labor and understand resulting production.
- Accumulate, consume, trade, and deplete resources.
- Observe population cohorts, births, deaths, migration, and workforce change.
- Adopt policies with visible benefits, costs, and delayed effects.
- Manage prices, employment, taxes, spending, debt, and foreign reserves.
- Trade and interact diplomatically with three simplified foreign nations.
- Receive causal warnings about emerging crises.
- Enter five-turn terminal crises and choose among multiple remedies.
- Lose through revolution, insolvency, invasion, or essential-resource failure.
- Save, load, and deterministically resume a campaign.
- Understand major changes through causal turn reports.

Internal playtests should produce meaningful scarcity and political tension
without relying on a scripted sequence.

## Initial scenario

The single MVP scenario is a small agrarian country with barter/local exchange,
weak taxation and administration, agriculture as its largest employer, limited
timber and ore, no domestic fossil-fuel supply, limited infrastructure and
education, modest food reserves, no public debt, four unequal population
groups, and three foreign nations with different needs and strategies.

The opening challenge is to create reliable food surpluses, establish money and
taxation, build manufacturing capacity, and manage development's social costs.

## Included systems

- Six resources: food, timber, ore, energy, consumer goods, and capital goods.
- Five sectors: agriculture, extraction, manufacturing, construction, and
  energy.
- Three age cohorts and four socioeconomic groups.
- Government budgets, domestic and foreign debt, reserves, administration, and
  legitimacy.
- Approximately 15 policies covering exchange, property, trade, taxation,
  labor, welfare, and resources.
- Aggregate infrastructure, capacity, depreciation, and maintenance.
- Three simplified foreign nations and escalating economic conflict.
- Visible systemic strain derived from underlying vulnerabilities.
- Revolution, insolvency, invasion, and essential-resource crises.
- Turn history, causal explanations, and save/load.

## Out of scope

- Tactical warfare or maps.
- Multiplayer.
- Individual citizens or firms.
- Historical countries or exact historical data.
- Detailed geographic supply chains or fully autonomous foreign economies.
- Complex monetary markets, equities, or derivatives.
- AI-generated natural-language events.
- Mod support, native mobile clients, cloud accounts, or online sync.
- Multiple starting scenarios or post-revolution successor play.

## Delivery milestones

### Milestone 0 — Project foundation

- Project configuration and development tooling.
- Backend package foundation and health endpoint.
- Pydantic, SQLAlchemy, SQLite, and Alembic foundations.
- Formatting, linting, tests, and local run instructions.
- No economic simulation logic and no frontend code unless separately requested.

### Milestone 1 — Deterministic economic loop

- Resources, sectors, labor allocation, production, consumption, shortages,
  prices, end-turn API, causal report, and golden-seed tests.

### Milestone 2 — Population and government

- Cohorts, groups, demographic flows, workforce, budgets, infrastructure,
  maintenance, and debt.

### Milestone 3 — Institutions and politics

- Policy adoption, satisfaction, influence, organization, radicalization,
  legitimacy, systemic strain, and warnings.

### Milestone 4 — Trade and foreign nations

- Three foreign actors, trade, world prices, reserves, relationships, and
  escalation states.

### Milestone 5 — Crises and defeat

- Five-turn revolution and insolvency crises, abstract invasion,
  essential-resource collapse, and game-over reporting.

### Milestone 6 — Persistence and balancing

- Save/load, history, events, difficulty profiles, soak tests, balance passes,
  and release preparation.

## Definition of complete

- A clean install starts both services locally.
- A complete campaign is playable through the React UI.
- Every crisis and loss condition is reachable.
- Save/load preserves state and deterministic outcomes.
- Major warnings and losses identify their causal drivers.
- Tests cover core calculations and invariants.
- A 500-turn automated soak test finishes without invalid state or runtime error.
- Setup, architecture, gameplay, and known limitations are documented.

## Balance hypotheses

- Typical first run: 60–120 turns.
- Skilled run: 150–300 turns.
- Exceptional run: more than 300 turns.
- First serious warning: usually by turn 20.
- Crises should have multiple causes and at least two plausible responses.
- Strong short-term optimization should increase long-term fragility.

Source: [Economic Simulator — MVP Product & Engineering Plan](https://app.notion.com/p/3b988d2fa3f381f7a832e2b687d12d15)

