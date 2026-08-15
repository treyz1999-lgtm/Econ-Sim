from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.population import PopulationGroupId


class PolicyDimension(StrEnum):
    """Identify one mutually exclusive institutional policy dimension."""

    EXCHANGE = "exchange"
    PROPERTY = "property"
    TRADE = "trade"
    TAXATION = "taxation"
    LABOR = "labor"
    WELFARE = "welfare"
    RESOURCE = "resource"


class PolicyDefinition(BaseModel):
    """Describe policy prerequisites, costs, reactions, and delayed benefits."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    dimension: PolicyDimension
    name: str
    description: str
    prerequisites: tuple[str, ...] = ()
    minimum_administrative_capacity: Decimal = Field(default=Decimal(0), ge=0, le=1)
    minimum_education: Decimal = Field(default=Decimal(0), ge=0, le=1)
    implementation_cost: Decimal = Field(ge=0)
    administrative_load: Decimal = Field(ge=0, le=1)
    implementation_delay: int = Field(default=1, ge=0)
    group_reactions: dict[PopulationGroupId, Decimal]
    satisfaction_modifier: Decimal = Field(default=Decimal(0), ge=-1, le=1)
    environmental_modifier: Decimal = Field(default=Decimal(0), ge=-1, le=1)

    @model_validator(mode="after")
    def require_all_group_reactions(self) -> "PolicyDefinition":
        """Ensure every socioeconomic group receives an explicit reaction."""
        if set(self.group_reactions) != set(PopulationGroupId):
            raise ValueError("policy reactions must include all population groups")
        return self


class PolicyTransition(BaseModel):
    """Record an adopted policy waiting for its delayed activation turn."""

    model_config = ConfigDict(frozen=True)

    policy_id: str
    adopted_turn: int = Field(ge=1)
    activation_turn: int = Field(ge=1)


class PolicyState(BaseModel):
    """Persist active institutions, a pending transition, and adoption history."""

    model_config = ConfigDict(frozen=True)

    active: dict[PolicyDimension, str]
    pending: PolicyTransition | None = None
    adoption_history: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_all_dimensions(self) -> "PolicyState":
        """Reject partial institutional states that could produce hidden defaults."""
        if set(self.active) != set(PolicyDimension):
            raise ValueError("policy state must include every policy dimension")
        return self


class PolicyAdoption(BaseModel):
    """Select at most one ordinary policy for the current turn."""

    model_config = ConfigDict(frozen=True)

    policy_id: str = Field(min_length=1)
