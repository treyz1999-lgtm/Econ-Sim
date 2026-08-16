from decimal import Decimal
from uuid import UUID

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.resources import ResourceId
from backend.app.engine.pricing import update_prices

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_price_increase_is_capped() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    resources = dict(state.resources)
    resources[ResourceId.FOOD] = resources[ResourceId.FOOD].model_copy(
        update={"shortage_ratio": Decimal(1), "price": Decimal("10")}
    )

    result = update_prices(resources, load_balance())[ResourceId.FOOD]

    assert result.price == Decimal("15.00")


def test_surplus_lowers_price_without_exceeding_floor() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    resources = dict(state.resources)
    resources[ResourceId.FOOD] = resources[ResourceId.FOOD].model_copy(
        update={"inventory": Decimal("10000"), "price": Decimal("10")}
    )

    result = update_prices(resources, load_balance())[ResourceId.FOOD]

    assert result.price == Decimal("7.50")


def test_inventory_at_reserve_target_keeps_price_stable() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    resources = dict(state.resources)
    food = resources[ResourceId.FOOD]
    resources[ResourceId.FOOD] = food.model_copy(
        update={
            "inventory": food.strategic_reserve_target,
            "shortage_ratio": Decimal(0),
        }
    )

    result = update_prices(resources, load_balance())[ResourceId.FOOD]

    assert result.price == food.price


def test_costly_imports_add_domestic_price_pressure() -> None:
    """Import reliance should transmit a positive foreign-price premium."""
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    food = state.resources[ResourceId.FOOD].model_copy(
        update={
            "inventory": Decimal("50"),
            "demand": Decimal("100"),
            "imports": Decimal("50"),
            "price": Decimal("1"),
            "world_price": Decimal("2"),
            "shortage_ratio": Decimal(0),
        }
    )
    resources = {**state.resources, ResourceId.FOOD: food}

    updated = update_prices(resources, load_balance())

    assert updated[ResourceId.FOOD].price > Decimal("1")
