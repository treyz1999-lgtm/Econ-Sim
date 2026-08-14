from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_price
from backend.app.domain.resources import ResourceId, ResourceState


def clamp(minimum: Decimal, maximum: Decimal, value: Decimal) -> Decimal:
    return max(minimum, min(maximum, value))


def update_prices(
    resources: dict[ResourceId, ResourceState], balance: BalanceConfig
) -> dict[ResourceId, ResourceState]:
    shortage_coefficient = balance.shortage_pressure_coefficient
    surplus_coefficient = balance.surplus_pressure_coefficient
    surplus_cap = balance.surplus_pressure_cap
    multiplier_floor = balance.price_multiplier_floor
    multiplier_ceiling = balance.price_multiplier_ceiling

    updated: dict[ResourceId, ResourceState] = {}
    for resource_id, resource in resources.items():
        shortage_pressure = resource.shortage_ratio * shortage_coefficient
        surplus_ratio = max(
            Decimal(0),
            resource.inventory - resource.strategic_reserve_target,
        ) / max(resource.demand, Decimal(1))
        surplus_pressure = min(surplus_cap, surplus_ratio * surplus_coefficient)
        multiplier = clamp(
            multiplier_floor,
            multiplier_ceiling,
            Decimal(1) + shortage_pressure - surplus_pressure,
        )
        updated[resource_id] = resource.model_copy(
            update={"price": quantize_price(resource.price * multiplier)}
        )
    return updated
