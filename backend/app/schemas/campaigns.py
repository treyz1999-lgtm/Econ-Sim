from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.state import GameState


class CreateCampaignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: int = Field(ge=-(2**63), le=2**63 - 1)
    scenario_id: str = Field(default="agrarian_start", min_length=1, max_length=64)


class CampaignResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    state: GameState
