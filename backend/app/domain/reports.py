from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.production import SectorId
from backend.app.domain.resources import ResourceId


class Cause(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    value: Decimal = Field(allow_inf_nan=False)
    message: str


class MetricExplanation(BaseModel):
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


class TurnReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    previous_turn: int = Field(ge=0)
    turn: int = Field(ge=1)
    assigned_labor: Decimal = Field(ge=0, allow_inf_nan=False)
    unassigned_labor: Decimal = Field(ge=0, allow_inf_nan=False)
    sectors: dict[SectorId, SectorTurnResult]
    resources: dict[ResourceId, ResourceTurnResult]
    warnings: tuple[str, ...]
    explanations: tuple[MetricExplanation, ...]
