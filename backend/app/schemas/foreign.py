from pydantic import BaseModel, ConfigDict

from backend.app.domain.foreign import ForeignState


class ForeignStateResponse(BaseModel):
    """Expose all foreign actors and current economic dependence."""

    model_config = ConfigDict(frozen=True)

    foreign: ForeignState
