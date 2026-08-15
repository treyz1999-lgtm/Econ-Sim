from decimal import Decimal

from backend.app.core.data import load_balance, load_scenario
from backend.app.engine.population import resolve_population


def test_child_labor_reduces_education_gain_and_increases_deaths() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)
    balance = load_balance()

    baseline = resolve_population(
        state.population, state.government, Decimal(0), Decimal(0), Decimal(0), balance
    )
    exposed = resolve_population(
        state.population,
        state.government,
        Decimal(0),
        Decimal("0.5"),
        Decimal(0),
        balance,
    )

    assert exposed.population.education_index < baseline.population.education_index
    assert exposed.deaths["children"] > baseline.deaths["children"]


def test_food_shortage_increases_mortality_without_negative_population() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)

    result = resolve_population(
        state.population,
        state.government,
        Decimal("1"),
        Decimal(0),
        Decimal(0),
        load_balance(),
    )

    assert sum(result.deaths.values(), Decimal(0)) > 0
    assert all(
        value >= 0
        for group in result.population.groups.values()
        for value in group.cohorts.values()
    )
    expected = (
        state.population.total
        + result.births
        - sum(result.deaths.values(), Decimal(0))
        + result.net_migration
    )
    assert result.population.total == expected


def test_elderly_labor_increases_elderly_deaths() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)
    baseline = resolve_population(
        state.population,
        state.government,
        Decimal(0),
        Decimal(0),
        Decimal(0),
        load_balance(),
    )
    exposed = resolve_population(
        state.population,
        state.government,
        Decimal(0),
        Decimal(0),
        Decimal("0.5"),
        load_balance(),
    )

    assert exposed.deaths["elderly"] > baseline.deaths["elderly"]
