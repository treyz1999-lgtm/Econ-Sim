from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_quantity
from backend.app.domain.population import PopulationState
from backend.app.domain.resources import ResourceId, ResourceState


def derive_population_demand(
    resources: dict[ResourceId, ResourceState],
    population: PopulationState,
    balance: BalanceConfig,
) -> dict[ResourceId, ResourceState]:
    updated = {}
    for resource_id, resource in resources.items():
        demand = sum(
            (
                people
                * balance.per_capita_demand[group_id.value][cohort_id.value].get(
                    resource_id.value, 0
                )
                for group_id, group in population.groups.items()
                for cohort_id, people in group.cohorts.items()
            )
        )
        updated[resource_id] = resource.model_copy(
            update={"demand": quantize_quantity(demand)}
        )
    return updated
