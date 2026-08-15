from decimal import Decimal

import pytest

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.population import AgeCohortId, PopulationGroupId
from backend.app.domain.production import SectorId
from backend.app.engine.labor import PopulationAllocationError, resolve_labor


def test_all_cohorts_can_work_with_different_effective_labor() -> None:
    population = load_scenario("00000000-0000-0000-0000-000000000001", 42).population
    allocation = {
        SectorId.AGRICULTURE: {
            PopulationGroupId.FARMERS: {
                AgeCohortId.CHILDREN: Decimal("1"),
                AgeCohortId.WORKING_AGE: Decimal("1"),
                AgeCohortId.ELDERLY: Decimal("1"),
            }
        }
    }

    result = resolve_labor(allocation, population, load_balance())

    assert result.assigned_headcount == 3
    assert result.effective_labor[SectorId.AGRICULTURE] == Decimal("2.0500")
    assert result.child_exposure > 0
    assert result.elderly_exposure > 0


def test_population_cell_cannot_be_assigned_twice() -> None:
    population = load_scenario("00000000-0000-0000-0000-000000000001", 42).population
    allocation = {
        SectorId.AGRICULTURE: {
            PopulationGroupId.FARMERS: {AgeCohortId.CHILDREN: Decimal("20")}
        },
        SectorId.EXTRACTION: {
            PopulationGroupId.FARMERS: {AgeCohortId.CHILDREN: Decimal("20")}
        },
    }

    with pytest.raises(PopulationAllocationError):
        resolve_labor(allocation, population, load_balance())
