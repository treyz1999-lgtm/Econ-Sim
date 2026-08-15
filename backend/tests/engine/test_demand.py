from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.population import PopulationGroupId
from backend.app.domain.resources import ResourceId
from backend.app.engine.demand import derive_population_demand


def test_resource_demand_scales_with_population() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)
    groups = dict(state.population.groups)
    farmers = groups[PopulationGroupId.FARMERS]
    groups[PopulationGroupId.FARMERS] = farmers.model_copy(
        update={
            "cohorts": {cohort: value * 2 for cohort, value in farmers.cohorts.items()}
        }
    )
    population = state.population.model_copy(update={"groups": groups})

    demand = derive_population_demand(state.resources, population, load_balance())

    assert demand[ResourceId.FOOD].demand > state.resources[ResourceId.FOOD].demand
