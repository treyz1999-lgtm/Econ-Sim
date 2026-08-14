from decimal import Decimal

from backend.app.domain.production import SectorId
from backend.app.domain.reports import Cause, MetricExplanation, SectorTurnResult
from backend.app.domain.resources import ResourceId, ResourceState


def build_explanations(
    resources_after: dict[ResourceId, ResourceState],
    sector_results: dict[SectorId, SectorTurnResult],
) -> tuple[MetricExplanation, ...]:
    explanations: list[MetricExplanation] = []
    for sector_id, result in sector_results.items():
        explanations.append(
            MetricExplanation(
                metric=f"sector.{sector_id.value}.output",
                causes=(
                    Cause(
                        code=result.binding_constraint,
                        value=result.output,
                        message=(
                            f"{sector_id.value} output was limited by "
                            f"{result.binding_constraint}"
                        ),
                    ),
                ),
            )
        )
    for resource_id in ResourceId:
        after = resources_after[resource_id]
        causes: list[Cause] = []
        if after.shortage_ratio > 0:
            causes.append(
                Cause(
                    code="shortage_pressure",
                    value=after.shortage_ratio,
                    message=f"Unmet {resource_id.value} demand raised price pressure",
                )
            )
        if after.inventory > after.strategic_reserve_target:
            causes.append(
                Cause(
                    code="surplus_pressure",
                    value=after.inventory - after.strategic_reserve_target,
                    message=(
                        f"{resource_id.value} inventory above reserve target "
                        "lowered price pressure"
                    ),
                )
            )
        if not causes:
            causes.append(
                Cause(
                    code="balanced_supply",
                    value=Decimal(0),
                    message=f"{resource_id.value} supply produced no price pressure",
                )
            )
        explanations.append(
            MetricExplanation(
                metric=f"resource.{resource_id.value}.price",
                causes=tuple(causes),
            )
        )
    return tuple(explanations)
