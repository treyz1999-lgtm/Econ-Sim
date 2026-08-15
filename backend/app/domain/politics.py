from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.population import PopulationGroupId


class WarningLevel(StrEnum):
    """Classify systemic pressure without starting a later-milestone crisis."""

    STABLE = "stable"
    ELEVATED = "elevated"
    SEVERE = "severe"
    CRITICAL = "critical"


class PoliticalGroupState(BaseModel):
    """Track persistent normalized political conditions for one population group."""

    model_config = ConfigDict(frozen=True)

    expectations: Decimal = Field(ge=0, le=1)
    satisfaction: Decimal = Field(ge=0, le=1)
    organization: Decimal = Field(ge=0, le=1)
    influence: Decimal = Field(ge=0, le=1)
    radicalization: Decimal = Field(ge=0, le=1)


class StrainComponents(BaseModel):
    """Expose normalized causal inputs used to calculate systemic strain."""

    model_config = ConfigDict(frozen=True)

    resource_stress: Decimal = Field(ge=0, le=1)
    demographic_stress: Decimal = Field(ge=0, le=1)
    inequality: Decimal = Field(ge=0, le=1)
    unmet_expectations: Decimal = Field(ge=0, le=1)
    infrastructure_burden: Decimal = Field(ge=0, le=1)
    debt_pressure: Decimal = Field(ge=0, le=1)
    environmental_damage: Decimal = Field(ge=0, le=1)
    foreign_dependence: Decimal = Field(default=Decimal(0), ge=0, le=1)
    institutional_complexity: Decimal = Field(ge=0, le=1)
    political_polarization: Decimal = Field(ge=0, le=1)


class PoliticsState(BaseModel):
    """Persist group politics and aggregate pressure derived by the engine."""

    model_config = ConfigDict(frozen=True)

    groups: dict[PopulationGroupId, PoliticalGroupState]
    systemic_strain: Decimal = Field(ge=0, le=1)
    components: StrainComponents
    polarization: Decimal = Field(ge=0, le=1)
    resilience: Decimal = Field(ge=0, le=1)
    environmental_damage: Decimal = Field(ge=0, le=1)
    warning_level: WarningLevel

    @model_validator(mode="after")
    def require_all_groups(self) -> "PoliticsState":
        """Require political state for each population group."""
        if set(self.groups) != set(PopulationGroupId):
            raise ValueError("politics state must include all population groups")
        return self
