from decimal import Decimal

from backend.app.core.data import load_scenario
from backend.app.domain.population import AgeCohortId, PopulationGroupId


def test_population_contains_four_groups_and_three_cohorts() -> None:
    population = load_scenario("00000000-0000-0000-0000-000000000001", 42).population

    assert set(population.groups) == set(PopulationGroupId)
    assert all(
        set(group.cohorts) == set(AgeCohortId) for group in population.groups.values()
    )
    assert population.total == Decimal("200.0")


def test_population_aggregates_reconcile() -> None:
    population = load_scenario("00000000-0000-0000-0000-000000000001", 42).population

    assert (
        sum((population.cohort_total(cohort) for cohort in AgeCohortId), Decimal(0))
        == population.total
    )
    assert population.dependency_ratio == Decimal("0.6")
