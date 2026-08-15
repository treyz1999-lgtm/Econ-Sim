from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.government import GovernmentActions
from backend.app.domain.policies import PolicyAdoption, PolicyState
from backend.app.domain.politics import PoliticsState
from backend.app.domain.population import AgeCohortId, PopulationGroupId
from backend.app.domain.production import SectorId
from backend.app.domain.reports import TurnReport
from backend.app.domain.resources import ResourceId
from backend.app.domain.state import GameState
from backend.app.schemas.government import GovernmentSummary
from backend.app.schemas.population import PopulationSummary


class EndTurnRequest(BaseModel):
    """Validate all choices submitted for one atomic annual turn."""

    model_config = ConfigDict(extra="forbid")

    expected_turn: int = Field(ge=0)
    labor_allocation: dict[
        SectorId, dict[PopulationGroupId, dict[AgeCohortId, Decimal]]
    ]
    government: GovernmentActions
    policy_adoption: PolicyAdoption | None = None


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
    """Provide a compact backend projection for a future dashboard."""

    turn: int
    available_labor: Decimal
    assigned_labor: Decimal
    unassigned_labor: Decimal
    resources: dict[ResourceId, DashboardResource]
    sectors: dict[SectorId, DashboardSector]
    population: PopulationSummary
    government: GovernmentSummary
    policies: PolicyState
    politics: PoliticsState
    warnings: tuple[str, ...]


class EndTurnResponse(BaseModel):
    state: GameState
    turn_report: TurnReport
    dashboard: DashboardSummary


def build_dashboard(state: GameState, report: TurnReport) -> DashboardSummary:
    """Project a completed state and report into dashboard-ready data."""
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
        population=PopulationSummary(
            total=state.population.total,
            cohorts={
                cohort: state.population.cohort_total(cohort) for cohort in AgeCohortId
            },
            groups={
                group_id: sum(group.cohorts.values(), Decimal(0))
                for group_id, group in state.population.groups.items()
            },
            dependency_ratio=state.population.dependency_ratio,
            education_index=state.population.education_index,
            child_labor_exposure=state.population.child_labor_exposure,
            elderly_labor_exposure=state.population.elderly_labor_exposure,
        ),
        government=GovernmentSummary(
            tax_rate=state.government.tax_rate,
            tax_revenue=state.government.tax_revenue,
            spending=state.government.spending,
            treasury=state.government.treasury,
            domestic_debt=state.government.domestic_debt,
            foreign_debt=state.government.foreign_debt,
            foreign_reserves=state.government.foreign_reserves,
            debt_service=state.government.debt_service,
            infrastructure=state.government.infrastructure,
            infrastructure_condition=state.government.infrastructure_condition,
            legitimacy=state.government.legitimacy,
            administrative_capacity=state.government.administrative_capacity,
        ),
        policies=state.policies,
        politics=state.politics,
        warnings=report.warnings,
    )
