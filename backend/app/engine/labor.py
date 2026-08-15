from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_quantity
from backend.app.domain.population import (
    AgeCohortId,
    PopulationGroupId,
    PopulationState,
)
from backend.app.domain.production import SectorId

LaborAllocation = dict[SectorId, dict[PopulationGroupId, dict[AgeCohortId, Decimal]]]


class PopulationAllocationError(ValueError):
    code = "population_allocation_exceeds_available"


@dataclass(frozen=True)
class LaborResolution:
    effective_labor: dict[SectorId, Decimal]
    assigned_by_cohort: dict[AgeCohortId, Decimal]
    assigned_by_group: dict[PopulationGroupId, Decimal]
    assigned_headcount: Decimal
    child_exposure: Decimal
    elderly_exposure: Decimal


def resolve_labor(
    allocation: LaborAllocation,
    population: PopulationState,
    balance: BalanceConfig,
) -> LaborResolution:
    used = {
        (group_id, cohort_id): Decimal(0)
        for group_id in PopulationGroupId
        for cohort_id in AgeCohortId
    }
    effective = {sector_id: Decimal(0) for sector_id in SectorId}
    by_cohort = {cohort_id: Decimal(0) for cohort_id in AgeCohortId}
    by_group = {group_id: Decimal(0) for group_id in PopulationGroupId}
    for sector_id, groups in allocation.items():
        for group_id, cohorts in groups.items():
            for cohort_id, people in cohorts.items():
                used[(group_id, cohort_id)] += people
                by_cohort[cohort_id] += people
                by_group[group_id] += people
                effective[sector_id] += (
                    people * balance.cohort_productivity[cohort_id.value]
                )
    for (group_id, cohort_id), assigned in used.items():
        if assigned > population.groups[group_id].cohorts[cohort_id]:
            raise PopulationAllocationError(
                f"{group_id.value}/{cohort_id.value} assignment exceeds population"
            )
    children = population.cohort_total(AgeCohortId.CHILDREN)
    elderly = population.cohort_total(AgeCohortId.ELDERLY)
    return LaborResolution(
        effective_labor={
            key: quantize_quantity(value) for key, value in effective.items()
        },
        assigned_by_cohort=by_cohort,
        assigned_by_group=by_group,
        assigned_headcount=sum(by_cohort.values(), Decimal(0)),
        child_exposure=by_cohort[AgeCohortId.CHILDREN] / max(children, Decimal(1)),
        elderly_exposure=by_cohort[AgeCohortId.ELDERLY] / max(elderly, Decimal(1)),
    )
