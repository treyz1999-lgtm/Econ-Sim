from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_quantity
from backend.app.domain.government import (
    GovernmentActions,
    GovernmentState,
    SpendingCategory,
)
from backend.app.domain.production import SectorId, SectorState


@dataclass(frozen=True)
class InfrastructureResolution:
    government: GovernmentState
    sectors: dict[SectorId, SectorState]
    maintenance_need: Decimal
    maintenance_coverage: Decimal
    depreciation: Decimal
    infrastructure_added: Decimal


def resolve_infrastructure(
    government: GovernmentState,
    actions: GovernmentActions,
    sectors: dict[SectorId, SectorState],
    construction_output: Decimal,
    balance: BalanceConfig,
) -> InfrastructureResolution:
    spending = actions.spending[SpendingCategory.INFRASTRUCTURE]
    maintenance_need = (
        government.infrastructure * balance.infrastructure_maintenance_cost
    )
    maintenance_spending = min(spending, maintenance_need)
    coverage = maintenance_spending / max(maintenance_need, Decimal(1))
    depreciation = quantize_quantity(
        government.infrastructure
        * balance.infrastructure_depreciation_rate
        * (Decimal(1) - coverage)
    )
    remaining = max(Decimal(0), spending - maintenance_spending)
    funded = min(construction_output, remaining / balance.construction_cost_per_unit)
    infrastructure_added = quantize_quantity(
        funded
        * actions.construction_allocation.get("infrastructure", Decimal(0))
        * balance.infrastructure_conversion
    )
    updated_sectors = dict(sectors)
    for sector_id in SectorId:
        share = actions.construction_allocation.get(sector_id.value, Decimal(0))
        addition = quantize_quantity(
            funded * share * balance.sector_capacity_conversion
        )
        updated_sectors[sector_id] = sectors[sector_id].model_copy(
            update={"capacity": sectors[sector_id].capacity + addition}
        )
    next_infrastructure = max(
        Decimal(0), government.infrastructure - depreciation + infrastructure_added
    )
    condition = min(
        Decimal(1), next_infrastructure / max(government.infrastructure, Decimal(1))
    )
    return InfrastructureResolution(
        government=government.model_copy(
            update={
                "infrastructure": quantize_quantity(next_infrastructure),
                "infrastructure_condition": condition,
            }
        ),
        sectors=updated_sectors,
        maintenance_need=quantize_quantity(maintenance_need),
        maintenance_coverage=coverage,
        depreciation=depreciation,
        infrastructure_added=infrastructure_added,
    )
