from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.government import SpendingCategory
from backend.app.domain.policies import PolicyDimension
from backend.app.domain.politics import StrainComponents, WarningLevel
from backend.app.domain.population import AgeCohortId
from backend.app.domain.production import SectorId
from backend.app.domain.resources import ResourceId


class Cause(BaseModel):
    """Describe one numeric contributor to a reported metric change."""

    model_config = ConfigDict(frozen=True)

    code: str
    value: Decimal = Field(allow_inf_nan=False)
    message: str


class MetricExplanation(BaseModel):
    """Group causal contributions under the metric they explain."""

    model_config = ConfigDict(frozen=True)

    metric: str
    causes: tuple[Cause, ...]


class SectorTurnResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    output: Decimal = Field(ge=0, allow_inf_nan=False)
    inputs_consumed: dict[ResourceId, Decimal]
    binding_constraint: str


class ResourceTurnResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    opening_inventory: Decimal = Field(ge=0, allow_inf_nan=False)
    production: Decimal = Field(ge=0, allow_inf_nan=False)
    production_inputs: Decimal = Field(ge=0, allow_inf_nan=False)
    demand: Decimal = Field(ge=0, allow_inf_nan=False)
    consumption: Decimal = Field(ge=0, allow_inf_nan=False)
    ending_inventory: Decimal = Field(ge=0, allow_inf_nan=False)
    shortage_ratio: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    old_price: Decimal = Field(gt=0, allow_inf_nan=False)
    new_price: Decimal = Field(gt=0, allow_inf_nan=False)


class PopulationTurnResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    opening_population: Decimal = Field(ge=0, allow_inf_nan=False)
    ending_population: Decimal = Field(ge=0, allow_inf_nan=False)
    births: Decimal = Field(ge=0, allow_inf_nan=False)
    deaths: dict[AgeCohortId, Decimal]
    net_migration: Decimal = Field(allow_inf_nan=False)
    child_labor_exposure: Decimal = Field(ge=0, le=1)
    elderly_labor_exposure: Decimal = Field(ge=0, le=1)
    education_index: Decimal = Field(ge=0, le=1)


class GovernmentTurnResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    tax_revenue: Decimal = Field(ge=0, allow_inf_nan=False)
    spending: dict[SpendingCategory, Decimal]
    primary_balance: Decimal = Field(allow_inf_nan=False)
    overall_balance: Decimal = Field(allow_inf_nan=False)
    debt_service: Decimal = Field(ge=0, allow_inf_nan=False)
    domestic_borrowing: Decimal = Field(ge=0, allow_inf_nan=False)
    domestic_debt: Decimal = Field(ge=0, allow_inf_nan=False)
    foreign_debt: Decimal = Field(ge=0, allow_inf_nan=False)
    foreign_reserves: Decimal = Field(ge=0, allow_inf_nan=False)
    infrastructure: Decimal = Field(ge=0, allow_inf_nan=False)
    infrastructure_depreciation: Decimal = Field(ge=0, allow_inf_nan=False)
    infrastructure_added: Decimal = Field(ge=0, allow_inf_nan=False)
    legitimacy: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    administrative_capacity: Decimal = Field(ge=0, le=1, allow_inf_nan=False)


class PolicyTurnResult(BaseModel):
    """Summarize policy adoption, activation, and resulting institutions."""

    model_config = ConfigDict(frozen=True)

    adopted_policy: str | None
    activated_policy: str | None
    active: dict[PolicyDimension, str]


class PoliticsTurnResult(BaseModel):
    """Expose aggregate political pressure and its normalized components."""

    model_config = ConfigDict(frozen=True)

    systemic_strain: Decimal = Field(ge=0, le=1)
    warning_level: WarningLevel
    polarization: Decimal = Field(ge=0, le=1)
    resilience: Decimal = Field(ge=0, le=1)
    environmental_damage: Decimal = Field(ge=0, le=1)
    components: StrainComponents


class TurnReport(BaseModel):
    """Return reconciled economic, demographic, government, and political results."""

    model_config = ConfigDict(frozen=True)

    previous_turn: int = Field(ge=0)
    turn: int = Field(ge=1)
    assigned_labor: Decimal = Field(ge=0, allow_inf_nan=False)
    assigned_population: Decimal = Field(ge=0, allow_inf_nan=False)
    cohort_assignments: dict[AgeCohortId, Decimal]
    unassigned_labor: Decimal = Field(ge=0, allow_inf_nan=False)
    sectors: dict[SectorId, SectorTurnResult]
    resources: dict[ResourceId, ResourceTurnResult]
    population: PopulationTurnResult
    government: GovernmentTurnResult
    policy: PolicyTurnResult
    politics: PoliticsTurnResult
    warnings: tuple[str, ...]
    explanations: tuple[MetricExplanation, ...]
