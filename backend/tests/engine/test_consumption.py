from decimal import Decimal
from uuid import UUID

from backend.app.core.data import load_scenario
from backend.app.domain.resources import ResourceId
from backend.app.engine.consumption import resolve_consumption

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_shortage_consumes_supply_without_negative_inventory() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    resources = dict(state.resources)
    food = resources[ResourceId.FOOD].model_copy(
        update={"inventory": Decimal("25"), "demand": Decimal("100")}
    )
    resources[ResourceId.FOOD] = food

    result = resolve_consumption(resources).resources[ResourceId.FOOD]

    assert result.consumption == Decimal("25.0000")
    assert result.inventory == 0
    assert result.shortage_ratio == Decimal("0.7500")


def test_zero_demand_has_zero_shortage() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    resources = dict(state.resources)
    resources[ResourceId.FOOD] = resources[ResourceId.FOOD].model_copy(
        update={"demand": Decimal(0)}
    )

    result = resolve_consumption(resources).resources[ResourceId.FOOD]

    assert result.shortage_ratio == 0
