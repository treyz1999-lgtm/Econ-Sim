from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.common import quantize_quantity
from backend.app.domain.production import SectorId, SectorState
from backend.app.domain.reports import SectorTurnResult
from backend.app.domain.resources import ResourceId, ResourceState


@dataclass(frozen=True)
class ProductionResolution:
    resources: dict[ResourceId, ResourceState]
    sectors: dict[SectorId, SectorState]
    results: dict[SectorId, SectorTurnResult]
    resource_inputs: dict[ResourceId, Decimal]


def resolve_production(
    resources: dict[ResourceId, ResourceState],
    sectors: dict[SectorId, SectorState],
) -> ProductionResolution:
    potential: dict[SectorId, Decimal] = {}
    for sector_id, sector in sectors.items():
        labor_output = sector.assigned_labor * sector.productivity
        potential[sector_id] = min(labor_output, sector.capacity)

    requested_inputs = {resource_id: Decimal(0) for resource_id in ResourceId}
    for sector_id, sector in sectors.items():
        for resource_id, coefficient in sector.input_coefficients.items():
            requested_inputs[resource_id] += potential[sector_id] * coefficient

    resource_scales: dict[ResourceId, Decimal] = {}
    for resource_id, requested in requested_inputs.items():
        resource_scales[resource_id] = (
            min(Decimal(1), resources[resource_id].inventory / requested)
            if requested > 0
            else Decimal(1)
        )

    updated_sectors: dict[SectorId, SectorState] = {}
    results: dict[SectorId, SectorTurnResult] = {}
    resource_inputs = {resource_id: Decimal(0) for resource_id in ResourceId}
    resource_outputs = {resource_id: Decimal(0) for resource_id in ResourceId}

    for sector_id in SectorId:
        sector = sectors[sector_id]
        input_scale = min(
            (resource_scales[item] for item in sector.input_coefficients),
            default=Decimal(1),
        )
        output = quantize_quantity(potential[sector_id] * input_scale)
        inputs_consumed: dict[ResourceId, Decimal] = {}
        for resource_id, coefficient in sector.input_coefficients.items():
            consumed = quantize_quantity(output * coefficient)
            inputs_consumed[resource_id] = consumed
            resource_inputs[resource_id] += consumed
        for resource_id, share in sector.output_mix.items():
            resource_outputs[resource_id] += quantize_quantity(output * share)

        labor_output = sector.assigned_labor * sector.productivity
        if input_scale < 1:
            limiting_resource = min(
                sector.input_coefficients,
                key=lambda item: (resource_scales[item], item.value),
            )
            binding_constraint = f"input:{limiting_resource.value}"
        elif sector.capacity <= labor_output:
            binding_constraint = "capacity"
        else:
            binding_constraint = "labor"

        updated_sectors[sector_id] = sector.model_copy(update={"latest_output": output})
        results[sector_id] = SectorTurnResult(
            output=output,
            inputs_consumed=inputs_consumed,
            binding_constraint=binding_constraint,
        )

    updated_resources: dict[ResourceId, ResourceState] = {}
    for resource_id in ResourceId:
        production = quantize_quantity(resource_outputs[resource_id])
        inputs = min(
            quantize_quantity(resource_inputs[resource_id]),
            resources[resource_id].inventory,
        )
        inventory = quantize_quantity(
            resources[resource_id].inventory - inputs + production
        )
        updated_resources[resource_id] = resources[resource_id].model_copy(
            update={"inventory": inventory, "production": production}
        )
        resource_inputs[resource_id] = inputs

    return ProductionResolution(
        resources=updated_resources,
        sectors=updated_sectors,
        results=results,
        resource_inputs=resource_inputs,
    )
