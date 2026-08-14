# Simulation Rules

## Design principles

1. Major changes name their leading causes.
2. Policies impose costs and tradeoffs rather than acting as permanent upgrades.
3. Difficulty emerges from state; time may amplify vulnerabilities but does not
   directly subtract arbitrary health.
4. Fertility, maintenance, debt, depletion, and pollution have delayed effects.
5. Institutions combine into systems; no ideology is a universal endpoint.
6. Terminal failures normally provide warnings, countdowns, and player agency.
7. Seeded simulation inputs produce deterministic outputs independent of UI.

## Turn sequence

One turn represents one year.

1. Review the prior report and warnings.
2. Allocate labor, set trade and budget choices, and optionally change policy.
3. Validate all actions before mutating state.
4. Resolve production inputs and outputs.
5. Resolve consumption, shortages, prices, wages, and employment.
6. Resolve trade, foreign payments, and diplomatic pressure.
7. Resolve revenue, spending, interest, debt, and reserves.
8. Resolve births, deaths, aging, and migration.
9. Update group satisfaction, organization, legitimacy, and crisis risks.
10. Update depreciation, regeneration/depletion, and pollution.
11. Resolve seeded events.
12. Advance crisis countdowns and test loss conditions.
13. Return the new state and a causal turn report.

Only one ordinary policy change is normally allowed per turn. Emergency crisis
actions are separate. The completed turn is atomic.

## Resources and prices

Track food, timber, ore, energy, consumer goods, and capital goods. Each tracks
inventory, production, demand, imports, exports, domestic and world prices,
shortage ratio, and strategic reserve target.

Ore and nonrenewable energy reserves are finite; extraction cost rises as
accessible reserves fall. Timber regenerates, but overharvesting reduces future
regeneration. Renewable energy persists only with adequate capacity and
investment.

```text
shortage_ratio = max(0, demand - available_supply) / max(demand, 1)
new_price = old_price * clamp(
    0.75,
    1.50,
    1 + shortage_pressure + import_pressure - surplus_pressure,
)
```

The multiplier is capped each turn for numerical stability and playability.
Inventories may never become negative.

## Production

Agriculture, extraction, manufacturing, construction, and energy each track
assigned labor, capacity, productivity, inputs, outputs, wage, maintenance, and
pollution intensity. Output is constrained by the minimum of labor, capacity,
and available input factors. Construction converts labor, energy, and capital
goods into capacity and infrastructure. Assigned labor may not exceed available
labor.

## Population

Track children, working-age people, and elderly people, plus farmers, workers,
owners, and administrators. Groups track population share, income, wealth,
needs fulfillment, satisfaction, organization, influence, and radicalization.

```text
next_population = population + births - deaths + net_migration
available_labor = working_age_population * participation_rate
```

Population cannot be negative. Fertility responds to affordability, food,
employment, services, and confidence. Mortality responds to food, pollution,
and health spending. Migration responds to wages, unemployment, stability, and
foreign policy. Demographic effects propagate through cohorts with delay.

## Government, infrastructure, and finance

Track revenue; administration, infrastructure, education, welfare, health,
security, and military-production spending; domestic and foreign debt;
interest and debt service; foreign reserves; administrative capacity; and
legitimacy.

```text
debt_service_ratio = debt_payments / max(government_revenue, 1)
foreign_coverage = foreign_reserves / max(foreign_payments_due, 1)
primary_balance = revenue - non_interest_spending
```

Domestic debt affects domestic wealth and financial stability. Foreign debt
requires exports or reserves and gives creditors leverage. Infrastructure and
capacity depreciate each turn; maintenance limits depreciation. Deferred
maintenance lowers productivity, wastes inputs, raises event risk, and makes
later repairs more expensive.

## Institutions and policies

The MVP targets about 15 policies spanning exchange, property, trade, taxation,
labor, welfare, and resource management. Every policy defines prerequisites,
implementation cost, administrative load, group reactions, delayed modifiers,
benefits, and costs.

## Foreign nations and systemic pressure

Three foreign nations track economic and military-industrial strength,
aggressiveness, trust, relations, resources, trade posture, debt claims,
strategic interest, and diplomatic posture. Escalation proceeds from offers or
demands through tariffs, sanctions, financial pressure, blockade or
destabilization, and finally invasion crisis.

Systemic strain summarizes resource, demographic, inequality, expectation,
infrastructure, debt, environmental, foreign-dependence, institutional, and
political stresses, reduced by legitimacy and resilience. It is not an
independent damage bar. A modest late-game global-pressure factor only
amplifies existing weaknesses.

Persistent ratchets include depleted deposits, sticky expectations and trust,
persistent pollution, post-restructuring borrowing penalties, infrastructure
maintenance obligations, and organized political groups.

## Crises and losses

### Revolution

Pressure combines grievance, organization, and opportunity. Crossing its
threshold starts a five-turn countdown showing participants, causes, required
pressure reduction, responses, and predicted effects. Survival requires
pressure below the exit threshold before the fifth crisis turn resolves.
Repression immediately lowers organization but raises grievance, damages
legitimacy, and worsens future crises.

### Sovereign insolvency

Unpayable debt service caused by inadequate revenue and foreign reserves starts
a five-turn countdown. Restructuring may save the campaign but harms
legitimacy, creditors, trade access, and borrowing costs.

### Foreign invasion

Invasion is an abstract economic-resistance crisis. Resistance depends on
military production, food and energy, infrastructure, financing, labor, allies,
public support, and relative strength. War diverts labor, raises shortages and
debt, damages infrastructure, and creates exhaustion.

### Essential-resource collapse

Food or energy below a critical minimum for several consecutive turns starts a
terminal warning. Supply must recover before its countdown expires.

Crisis countdowns cannot skip states. A game-over report includes years
survived, peak population and output, final institutions, immediate cause, and
three leading structural causes.

## Required invariants

- Population and resource inventories are never negative.
- Assigned labor never exceeds available labor.
- Imports do not exceed affordable foreign currency or credit.
- A completed turn is atomic.
- Identical seeds, initial states, and actions produce identical results.
- Crisis countdowns advance through every defined state.
- Simulation behavior never depends on wall-clock time.
- Formulas with unstable ranges are validated or clamped.

## Milestone 1 formula specification

Milestone 1 uses `Decimal` arithmetic. Resource quantities and annual sector
output are rounded half-to-even to four decimal places at state boundaries;
prices are rounded half-to-even to two decimal places. Intermediate
calculations are not rounded.

Production units are:

- Labor: worker-equivalents.
- Productivity: output units per worker-equivalent per year.
- Capacity: output units per year.
- Input coefficient: resource units consumed per output unit.

```text
labor_output = assigned_labor * productivity
potential_output = min(labor_output, capacity)
```

When sectors share an input, each receives the same proportional fulfillment
factor. This prevents sector iteration order from changing results:

```text
requested_input = sum(sector_potential_output * sector_input_coefficient)
input_scale = min(1, available_input / requested_input)
sector_output = potential_output * min(required_input_scales)
```

Inputs are removed before outputs are added. Output mixes divide sector output
among resources and must sum to one. Construction is the sole Milestone 1
exception: it reports construction activity but does not create a seventh
resource or change capacity before Milestone 2.

Scenario demand is fixed during Milestone 1. Population-driven demand begins in
Milestone 2.

```text
consumption = min(available_supply, demand)
ending_inventory = available_supply - consumption
shortage_ratio = max(0, demand - available_supply) / max(demand, 1)
```

For zero demand, shortage ratio is zero. Milestone 1 price pressure is:

```text
shortage_pressure = shortage_ratio * shortage_pressure_coefficient
import_pressure = 0
surplus_ratio = max(0, ending_inventory - reserve_target) / max(demand, 1)
surplus_pressure = min(surplus_pressure_cap,
                       surplus_ratio * surplus_pressure_coefficient)
price_multiplier = clamp(0.75, 1.50,
                         1 + shortage_pressure - surplus_pressure)
new_price = old_price * price_multiplier
```

All coefficients and initial values are stored in backend JSON data files.

Source: [Economic Simulator — MVP Product & Engineering Plan](https://app.notion.com/p/3b988d2fa3f381f7a832e2b687d12d15)
