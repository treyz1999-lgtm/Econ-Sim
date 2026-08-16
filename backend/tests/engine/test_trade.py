from decimal import Decimal
from uuid import UUID

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.foreign import ForeignNationId, TradeOrder
from backend.app.domain.resources import ResourceId
from backend.app.engine.trade import resolve_trade

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000041")


def test_imports_are_limited_by_reserves_supply_and_trade_policy() -> None:
    """Trade cannot exceed currency, foreign supply, or institutional access."""
    state = load_scenario(str(CAMPAIGN_ID), 42)
    government = state.government.model_copy(update={"foreign_reserves": Decimal("5")})
    order = TradeOrder(
        nation_id=ForeignNationId.NORTHREACH,
        imports={ResourceId.ENERGY: Decimal("20")},
    )

    result = resolve_trade(
        state.resources,
        government,
        state.foreign,
        state.policies,
        (order,),
        load_balance(),
    )

    imported = result.resources[ResourceId.ENERGY].imports
    assert imported <= Decimal("2")
    assert result.total_import_value <= Decimal("5")
    assert result.government.foreign_reserves >= 0


def test_exports_never_consume_strategic_reserves() -> None:
    """Export fulfillment must preserve inventory at the configured reserve target."""
    state = load_scenario(str(CAMPAIGN_ID), 42)
    order = TradeOrder(
        nation_id=ForeignNationId.MERCANTILE_LEAGUE,
        exports={ResourceId.FOOD: Decimal("1000")},
    )

    result = resolve_trade(
        state.resources,
        state.government,
        state.foreign,
        state.policies,
        (order,),
        load_balance(),
    )

    assert result.resources[ResourceId.FOOD].inventory >= Decimal("50")
    assert result.resources[ResourceId.FOOD].exports <= Decimal("70")
    assert result.total_export_value == result.government.foreign_reserves


def test_world_prices_are_deterministic_and_bounded_per_turn() -> None:
    """Configured foreign supply and demand move prices within stability bounds."""
    state = load_scenario(str(CAMPAIGN_ID), 42)

    first = resolve_trade(
        state.resources,
        state.government,
        state.foreign,
        state.policies,
        (),
        load_balance(),
    )
    second = resolve_trade(
        state.resources,
        state.government,
        state.foreign,
        state.policies,
        (),
        load_balance(),
    )

    assert first == second
    for resource_id, resource in first.resources.items():
        old = state.resources[resource_id].world_price
        assert old * Decimal("0.90") <= resource.world_price <= old * Decimal("1.10")
