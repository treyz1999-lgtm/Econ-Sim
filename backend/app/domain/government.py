from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.production import SectorId


class SpendingCategory(StrEnum):
    ADMINISTRATION = "administration"
    INFRASTRUCTURE = "infrastructure"
    EDUCATION = "education"
    WELFARE = "welfare"
    HEALTH = "health"
    SECURITY = "security"
    MILITARY_PRODUCTION = "military_production"


class GovernmentState(BaseModel):
    model_config = ConfigDict(frozen=True)

    tax_rate: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    tax_revenue: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    spending: dict[SpendingCategory, Decimal]
    treasury: Decimal = Field(ge=0, allow_inf_nan=False)
    domestic_debt: Decimal = Field(ge=0, allow_inf_nan=False)
    foreign_debt: Decimal = Field(ge=0, allow_inf_nan=False)
    domestic_interest_rate: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    foreign_interest_rate: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    debt_service: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    foreign_reserves: Decimal = Field(ge=0, allow_inf_nan=False)
    administrative_capacity: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    legitimacy: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    infrastructure: Decimal = Field(ge=0, allow_inf_nan=False)
    infrastructure_condition: Decimal = Field(ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_spending(self) -> "GovernmentState":
        if set(self.spending) != set(SpendingCategory):
            raise ValueError("government spending must include every category")
        if any(value < 0 or not value.is_finite() for value in self.spending.values()):
            raise ValueError("government spending must be finite and nonnegative")
        return self


class GovernmentActions(BaseModel):
    model_config = ConfigDict(frozen=True)

    tax_rate: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    spending: dict[SpendingCategory, Decimal]
    new_foreign_borrowing: Decimal = Field(ge=0, allow_inf_nan=False)
    construction_allocation: dict[str, Decimal]

    @model_validator(mode="after")
    def validate_actions(self) -> "GovernmentActions":
        if set(self.spending) != set(SpendingCategory):
            raise ValueError("government spending must include every category")
        valid_targets = {"infrastructure", *(sector.value for sector in SectorId)}
        if not set(self.construction_allocation).issubset(valid_targets):
            raise ValueError("unknown construction allocation target")
        values = self.construction_allocation.values()
        if any(value < 0 or not value.is_finite() for value in values):
            raise ValueError("construction shares must be finite and nonnegative")
        if sum(values, Decimal(0)) != Decimal(1):
            raise ValueError("construction shares must sum to one")
        return self
