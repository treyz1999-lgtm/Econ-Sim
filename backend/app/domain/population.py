from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PopulationGroupId(StrEnum):
    FARMERS = "farmers"
    WORKERS = "workers"
    OWNERS = "owners"
    ADMINS = "admins"


class AgeCohortId(StrEnum):
    CHILDREN = "children"
    WORKING_AGE = "working_age"
    ELDERLY = "elderly"


class PopulationGroupState(BaseModel):
    model_config = ConfigDict(frozen=True)

    cohorts: dict[AgeCohortId, Decimal]
    income: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    wealth: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    needs_fulfillment: Decimal = Field(
        default=Decimal(1), ge=0, le=1, allow_inf_nan=False
    )

    @model_validator(mode="after")
    def validate_cohorts(self) -> "PopulationGroupState":
        if set(self.cohorts) != set(AgeCohortId):
            raise ValueError("population group must include all age cohorts")
        if any(value < 0 or not value.is_finite() for value in self.cohorts.values()):
            raise ValueError("cohort populations must be finite and nonnegative")
        return self


class PopulationState(BaseModel):
    model_config = ConfigDict(frozen=True)

    groups: dict[PopulationGroupId, PopulationGroupState]
    participation_rate: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    education_index: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    births: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    deaths: dict[AgeCohortId, Decimal] = Field(
        default_factory=lambda: {cohort: Decimal(0) for cohort in AgeCohortId}
    )
    aging: dict[AgeCohortId, Decimal] = Field(
        default_factory=lambda: {
            AgeCohortId.CHILDREN: Decimal(0),
            AgeCohortId.WORKING_AGE: Decimal(0),
            AgeCohortId.ELDERLY: Decimal(0),
        }
    )
    net_migration: Decimal = Field(default=Decimal(0), allow_inf_nan=False)
    child_labor_exposure: Decimal = Field(
        default=Decimal(0), ge=0, le=1, allow_inf_nan=False
    )
    elderly_labor_exposure: Decimal = Field(
        default=Decimal(0), ge=0, le=1, allow_inf_nan=False
    )

    @model_validator(mode="after")
    def validate_groups(self) -> "PopulationState":
        if set(self.groups) != set(PopulationGroupId):
            raise ValueError("population state must include all four groups")
        return self

    def cohort_total(self, cohort: AgeCohortId) -> Decimal:
        return sum(
            (group.cohorts[cohort] for group in self.groups.values()), Decimal(0)
        )

    @property
    def total(self) -> Decimal:
        return sum((self.cohort_total(cohort) for cohort in AgeCohortId), Decimal(0))

    @property
    def dependency_ratio(self) -> Decimal:
        working = self.cohort_total(AgeCohortId.WORKING_AGE)
        dependents = self.cohort_total(AgeCohortId.CHILDREN) + self.cohort_total(
            AgeCohortId.ELDERLY
        )
        return dependents / max(working, Decimal(1))
