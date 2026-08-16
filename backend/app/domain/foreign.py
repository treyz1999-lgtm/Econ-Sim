from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.resources import ResourceId


class ForeignNationId(StrEnum):
    """Identify one of the three simplified foreign actors."""

    NORTHREACH = "northreach"
    MERCANTILE_LEAGUE = "mercantile_league"
    IRON_DOMINION = "iron_dominion"


class TradePosture(StrEnum):
    """Describe a foreign nation's configured commercial preference."""

    COOPERATIVE = "cooperative"
    MERCANTILE = "mercantile"
    COERCIVE = "coercive"


class EscalationState(StrEnum):
    """Track ordered diplomatic pressure without entering a crisis."""

    NORMAL = "normal"
    DEMANDS = "demands"
    TARIFFS = "tariffs"
    SANCTIONS = "sanctions"
    FINANCIAL_PRESSURE = "financial_pressure"
    BLOCKADE_WARNING = "blockade_warning"
    INVASION_WARNING = "invasion_warning"


class ForeignNationState(BaseModel):
    """Persist the economic capacity and relationship state of one foreign actor."""

    model_config = ConfigDict(frozen=True)

    name: str
    economic_strength: Decimal = Field(ge=0, le=1)
    military_industrial_strength: Decimal = Field(ge=0, le=1)
    aggressiveness: Decimal = Field(ge=0, le=1)
    trust: Decimal = Field(ge=0, le=1)
    relations: Decimal = Field(ge=-1, le=1)
    import_supply: dict[ResourceId, Decimal]
    export_demand: dict[ResourceId, Decimal]
    trade_posture: TradePosture
    debt_claims: Decimal = Field(default=Decimal(0), ge=0)
    strategic_interest: Decimal = Field(ge=0, le=1)
    escalation: EscalationState = EscalationState.NORMAL
    pressure: Decimal = Field(default=Decimal(0), ge=0, le=1)

    @model_validator(mode="after")
    def require_complete_markets(self) -> "ForeignNationState":
        """Require explicit supply and demand values for all resources."""
        if set(self.import_supply) != set(ResourceId):
            raise ValueError("foreign import supply must include every resource")
        if set(self.export_demand) != set(ResourceId):
            raise ValueError("foreign export demand must include every resource")
        market_values = (*self.import_supply.values(), *self.export_demand.values())
        if any(value < 0 or not value.is_finite() for value in market_values):
            raise ValueError("foreign market quantities must be finite and nonnegative")
        return self


class ForeignState(BaseModel):
    """Collect exactly three foreign actors and aggregate dependence."""

    model_config = ConfigDict(frozen=True)

    nations: dict[ForeignNationId, ForeignNationState]
    foreign_dependence: Decimal = Field(default=Decimal(0), ge=0, le=1)

    @model_validator(mode="after")
    def require_three_nations(self) -> "ForeignState":
        """Reject incomplete foreign-state snapshots."""
        if set(self.nations) != set(ForeignNationId):
            raise ValueError("foreign state must include all three nations")
        return self


class TradeOrder(BaseModel):
    """Request imports and exports with one foreign nation for one turn."""

    model_config = ConfigDict(frozen=True)

    nation_id: ForeignNationId
    imports: dict[ResourceId, Decimal] = Field(default_factory=dict)
    exports: dict[ResourceId, Decimal] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_quantities(self) -> "TradeOrder":
        """Ensure order quantities are finite, nonnegative, and not two-way."""
        values = (*self.imports.values(), *self.exports.values())
        if any(value < 0 or not value.is_finite() for value in values):
            raise ValueError("trade quantities must be finite and nonnegative")
        if set(self.imports) & set(self.exports):
            raise ValueError("a resource cannot be imported and exported together")
        return self
