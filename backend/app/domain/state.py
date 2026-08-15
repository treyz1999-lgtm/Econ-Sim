from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.government import GovernmentActions, GovernmentState
from backend.app.domain.population import (
    AgeCohortId,
    PopulationGroupId,
    PopulationState,
)
from backend.app.domain.production import SectorId, SectorState
from backend.app.domain.resources import ResourceId, ResourceState


class PlayerActions(BaseModel):
    model_config = ConfigDict(frozen=True)

    labor_allocation: dict[
        SectorId, dict[PopulationGroupId, dict[AgeCohortId, Decimal]]
    ]
    government: GovernmentActions

    @model_validator(mode="after")
    def require_all_sectors(self) -> "PlayerActions":
        if not set(self.labor_allocation).issubset(set(SectorId)):
            raise ValueError("labor allocation contains an unknown sector")
        for groups in self.labor_allocation.values():
            for cohorts in groups.values():
                if any(
                    value < 0 or not value.is_finite() for value in cohorts.values()
                ):
                    raise ValueError("labor allocations must be finite and nonnegative")
        return self


class GameState(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = Field(default=2, ge=2)
    campaign_id: UUID
    scenario_id: str
    seed: int
    turn: int = Field(ge=0)
    available_labor: Decimal = Field(ge=0, allow_inf_nan=False)
    resources: dict[ResourceId, ResourceState]
    sectors: dict[SectorId, SectorState]
    population: PopulationState
    government: GovernmentState

    @model_validator(mode="after")
    def require_complete_economy(self) -> "GameState":
        if set(self.resources) != set(ResourceId):
            raise ValueError("game state must include exactly all six resources")
        if set(self.sectors) != set(SectorId):
            raise ValueError("game state must include exactly all five sectors")
        return self
