from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_quantity
from backend.app.domain.government import GovernmentState, SpendingCategory
from backend.app.domain.population import (
    AgeCohortId,
    PopulationGroupId,
    PopulationGroupState,
    PopulationState,
)


@dataclass(frozen=True)
class PopulationResolution:
    population: PopulationState
    births: Decimal
    deaths: dict[AgeCohortId, Decimal]
    net_migration: Decimal


def resolve_population(
    population: PopulationState,
    government: GovernmentState,
    food_shortage_ratio: Decimal,
    child_labor_exposure: Decimal,
    elderly_labor_exposure: Decimal,
    balance: BalanceConfig,
) -> PopulationResolution:
    total = population.total
    working = population.cohort_total(AgeCohortId.WORKING_AGE)
    food_security = Decimal(1) - food_shortage_ratio
    births = quantize_quantity(working * balance.base_birth_rate * food_security)
    health_coverage = min(
        Decimal(1),
        government.spending[SpendingCategory.HEALTH] / max(total, Decimal(1)),
    )
    education_coverage = min(
        Decimal(1),
        government.spending[SpendingCategory.EDUCATION] / max(total, Decimal(1)),
    )
    health_mitigation = health_coverage * balance.health_mortality_mitigation
    rates = {
        cohort: balance.base_mortality_rates[cohort.value]
        + food_shortage_ratio * balance.food_shortage_mortality_coefficient
        - health_mitigation
        for cohort in AgeCohortId
    }
    rates[AgeCohortId.CHILDREN] += (
        child_labor_exposure * balance.child_labor_mortality_coefficient
    )
    rates[AgeCohortId.ELDERLY] += (
        elderly_labor_exposure * balance.elderly_labor_mortality_coefficient
    )
    rates = {
        cohort: max(Decimal(0), min(Decimal(1), rate)) for cohort, rate in rates.items()
    }
    deaths = {
        cohort: quantize_quantity(population.cohort_total(cohort) * rates[cohort])
        for cohort in AgeCohortId
    }
    net_migration = quantize_quantity(
        working * (balance.base_migration_rate - food_shortage_ratio * Decimal("0.02"))
    )
    child_aging = quantize_quantity(
        population.cohort_total(AgeCohortId.CHILDREN) / Decimal(18)
    )
    working_aging = quantize_quantity(working / Decimal(47))
    updated_groups: dict[PopulationGroupId, PopulationGroupState] = {}
    for group_id, group in population.groups.items():
        child_share = group.cohorts[AgeCohortId.CHILDREN] / max(
            population.cohort_total(AgeCohortId.CHILDREN), Decimal(1)
        )
        working_share = group.cohorts[AgeCohortId.WORKING_AGE] / max(
            working, Decimal(1)
        )
        elderly_share = group.cohorts[AgeCohortId.ELDERLY] / max(
            population.cohort_total(AgeCohortId.ELDERLY), Decimal(1)
        )
        cohorts = {
            AgeCohortId.CHILDREN: max(
                Decimal(0),
                group.cohorts[AgeCohortId.CHILDREN]
                + births * working_share
                - deaths[AgeCohortId.CHILDREN] * child_share
                - child_aging * child_share,
            ),
            AgeCohortId.WORKING_AGE: max(
                Decimal(0),
                group.cohorts[AgeCohortId.WORKING_AGE]
                + child_aging * child_share
                - deaths[AgeCohortId.WORKING_AGE] * working_share
                - working_aging * working_share
                + net_migration * working_share,
            ),
            AgeCohortId.ELDERLY: max(
                Decimal(0),
                group.cohorts[AgeCohortId.ELDERLY]
                + working_aging * working_share
                - deaths[AgeCohortId.ELDERLY] * elderly_share,
            ),
        }
        updated_groups[group_id] = group.model_copy(
            update={
                "cohorts": {
                    cohort: quantize_quantity(value)
                    for cohort, value in cohorts.items()
                }
            }
        )
    expected_total = quantize_quantity(
        total + births - sum(deaths.values(), Decimal(0)) + net_migration
    )
    distributed_total = sum(
        (sum(group.cohorts.values(), Decimal(0)) for group in updated_groups.values()),
        Decimal(0),
    )
    residual = expected_total - distributed_total
    if residual:
        admins = updated_groups[PopulationGroupId.ADMINS]
        admin_cohorts = dict(admins.cohorts)
        admin_cohorts[AgeCohortId.WORKING_AGE] = quantize_quantity(
            admin_cohorts[AgeCohortId.WORKING_AGE] + residual
        )
        updated_groups[PopulationGroupId.ADMINS] = admins.model_copy(
            update={"cohorts": admin_cohorts}
        )
    education_gain = (
        balance.education_gain_rate
        * education_coverage
        * (Decimal(1) - balance.child_labor_education_penalty * child_labor_exposure)
    )
    next_education = min(
        Decimal(1), max(Decimal(0), population.education_index + education_gain)
    )
    next_population = population.model_copy(
        update={
            "groups": updated_groups,
            "education_index": next_education,
            "births": births,
            "deaths": deaths,
            "aging": {
                AgeCohortId.CHILDREN: child_aging,
                AgeCohortId.WORKING_AGE: working_aging,
                AgeCohortId.ELDERLY: Decimal(0),
            },
            "net_migration": net_migration,
            "child_labor_exposure": child_labor_exposure,
            "elderly_labor_exposure": elderly_labor_exposure,
        }
    )
    return PopulationResolution(
        population=next_population,
        births=births,
        deaths=deaths,
        net_migration=net_migration,
    )
