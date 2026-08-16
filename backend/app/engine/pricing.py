from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_price
from backend.app.domain.resources import ResourceId, ResourceState


def clamp(minimum: Decimal, maximum: Decimal, value: Decimal) -> Decimal:
    """Constrain one price multiplier to configured stability bounds."""
    return max(minimum, min(maximum, value))


def update_prices(
    resources: dict[ResourceId, ResourceState], balance: BalanceConfig
) -> dict[ResourceId, ResourceState]:
    """Update domestic prices from shortages, imports, and excess inventory."""
    shortage_coefficient = balance.shortage_pressure_coefficient
    surplus_coefficient = balance.surplus_pressure_coefficient
    surplus_cap = balance.surplus_pressure_cap
    multiplier_floor = balance.price_multiplier_floor
    multiplier_ceiling = balance.price_multiplier_ceiling

    updated: dict[ResourceId, ResourceState] = {}
    for resource_id, resource in resources.items():
        shortage_pressure = resource.shortage_ratio * shortage_coefficient
        import_share = resource.imports / max(resource.demand, Decimal(1))
        foreign_premium = max(
            Decimal(0), resource.world_price / resource.price - Decimal(1)
        )
        import_pressure = (
            import_share * foreign_premium * balance.import_price_pressure_coefficient
        )
        surplus_ratio = max(
            Decimal(0),
            resource.inventory - resource.strategic_reserve_target,
        ) / max(resource.demand, Decimal(1))
        surplus_pressure = min(surplus_cap, surplus_ratio * surplus_coefficient)
        multiplier = clamp(
            multiplier_floor,
            multiplier_ceiling,
            Decimal(1) + shortage_pressure + import_pressure - surplus_pressure,
        )
        updated[resource_id] = resource.model_copy(
            update={"price": quantize_price(resource.price * multiplier)}
        )
    return updated
