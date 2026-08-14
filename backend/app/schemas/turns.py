from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.production import SectorId
from backend.app.domain.reports import TurnReport
from backend.app.domain.resources import ResourceId
from backend.app.domain.state import GameState


class EndTurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_turn: int = Field(ge=0)
    labor_allocation: dict[SectorId, Decimal]

    @model_validator(mode="after")
    def validate_labor_allocation(self) -> "EndTurnRequest":
        if set(self.labor_allocation) != set(SectorId):
            raise ValueError("labor allocation must include exactly all five sectors")
        if any(
            value < 0 or not value.is_finite()
            for value in self.labor_allocation.values()
        ):
            raise ValueError("labor allocations must be finite and nonnegative")
        return self


class DashboardResource(BaseModel):
    inventory: Decimal
    production: Decimal
    demand: Decimal
    consumption: Decimal
    shortage_ratio: Decimal
    price: Decimal


class DashboardSector(BaseModel):
    assigned_labor: Decimal
    capacity: Decimal
    output: Decimal
    binding_constraint: str


class DashboardSummary(BaseModel):
    turn: int
    available_labor: Decimal
    assigned_labor: Decimal
    unassigned_labor: Decimal
    resources: dict[ResourceId, DashboardResource]
    sectors: dict[SectorId, DashboardSector]
    warnings: tuple[str, ...]


class EndTurnResponse(BaseModel):
    state: GameState
    turn_report: TurnReport
    dashboard: DashboardSummary


def build_dashboard(state: GameState, report: TurnReport) -> DashboardSummary:
    return DashboardSummary(
        turn=state.turn,
        available_labor=state.available_labor,
        assigned_labor=report.assigned_labor,
        unassigned_labor=report.unassigned_labor,
        resources={
            resource_id: DashboardResource(
                inventory=resource.inventory,
                production=resource.production,
                demand=resource.demand,
                consumption=resource.consumption,
                shortage_ratio=resource.shortage_ratio,
                price=resource.price,
            )
            for resource_id, resource in state.resources.items()
        },
        sectors={
            sector_id: DashboardSector(
                assigned_labor=sector.assigned_labor,
                capacity=sector.capacity,
                output=report.sectors[sector_id].output,
                binding_constraint=report.sectors[sector_id].binding_constraint,
            )
            for sector_id, sector in state.sectors.items()
        },
        warnings=report.warnings,
    )
