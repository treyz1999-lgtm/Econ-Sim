from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.common import quantize_quantity
from backend.app.domain.resources import ResourceId, ResourceState


@dataclass(frozen=True)
class ConsumptionResolution:
    resources: dict[ResourceId, ResourceState]
    available_supply: dict[ResourceId, Decimal]


def resolve_consumption(
    resources: dict[ResourceId, ResourceState],
) -> ConsumptionResolution:
    updated: dict[ResourceId, ResourceState] = {}
    available_supply: dict[ResourceId, Decimal] = {}
    for resource_id in ResourceId:
        resource = resources[resource_id]
        supply = resource.inventory
        consumption = min(supply, resource.demand)
        shortage = (
            max(Decimal(0), resource.demand - supply) / resource.demand
            if resource.demand > 0
            else Decimal(0)
        )
        updated[resource_id] = resource.model_copy(
            update={
                "inventory": quantize_quantity(supply - consumption),
                "consumption": quantize_quantity(consumption),
                "shortage_ratio": quantize_quantity(shortage),
            }
        )
        available_supply[resource_id] = supply
    return ConsumptionResolution(resources=updated, available_supply=available_supply)
