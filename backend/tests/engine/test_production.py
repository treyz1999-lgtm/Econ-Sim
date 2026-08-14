from uuid import UUID

from backend.app.core.data import load_scenario
from backend.app.domain.resources import ResourceId
from backend.app.engine.production import resolve_production

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_production_conserves_inputs_and_never_creates_negative_inventory() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)

    result = resolve_production(state.resources, state.sectors)

    for resource_id, resource in result.resources.items():
        expected = (
            state.resources[resource_id].inventory
            - result.resource_inputs[resource_id]
            + resource.production
        )
        assert resource.inventory == expected
        assert resource.inventory >= 0


def test_missing_energy_limits_all_energy_dependent_sectors() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    resources = dict(state.resources)
    resources[ResourceId.ENERGY] = resources[ResourceId.ENERGY].model_copy(
        update={"inventory": 0}
    )

    result = resolve_production(resources, state.sectors)

    assert result.results["agriculture"].output == 0
    assert result.results["manufacturing"].output == 0
    assert result.results["construction"].output == 0


def test_shared_input_result_does_not_depend_on_mapping_order() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    reversed_sectors = dict(reversed(list(state.sectors.items())))

    normal = resolve_production(state.resources, state.sectors)
    reversed_result = resolve_production(state.resources, reversed_sectors)

    assert normal == reversed_result
