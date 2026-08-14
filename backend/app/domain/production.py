from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.resources import ResourceId


class SectorId(StrEnum):
    AGRICULTURE = "agriculture"
    EXTRACTION = "extraction"
    MANUFACTURING = "manufacturing"
    CONSTRUCTION = "construction"
    ENERGY = "energy"


class SectorState(BaseModel):
    model_config = ConfigDict(frozen=True)

    assigned_labor: Decimal = Field(ge=0, allow_inf_nan=False)
    capacity: Decimal = Field(ge=0, allow_inf_nan=False)
    productivity: Decimal = Field(ge=0, allow_inf_nan=False)
    input_coefficients: dict[ResourceId, Decimal] = Field(default_factory=dict)
    output_mix: dict[ResourceId, Decimal] = Field(default_factory=dict)
    wage: Decimal = Field(ge=0, allow_inf_nan=False)
    maintenance_requirement: Decimal = Field(ge=0, allow_inf_nan=False)
    pollution_intensity: Decimal = Field(ge=0, allow_inf_nan=False)
    latest_output: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_coefficients(self) -> "SectorState":
        if any(
            value <= 0 or not value.is_finite()
            for value in self.input_coefficients.values()
        ):
            raise ValueError("input coefficients must be finite and greater than zero")
        if any(
            value <= 0 or not value.is_finite() for value in self.output_mix.values()
        ):
            raise ValueError("output shares must be finite and greater than zero")
        output_total = sum(self.output_mix.values(), start=Decimal(0))
        if self.output_mix and output_total != Decimal(1):
            raise ValueError("output shares must sum to one")
        return self
