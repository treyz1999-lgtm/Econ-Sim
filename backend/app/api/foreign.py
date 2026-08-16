from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.persistence.database import get_session
from backend.app.persistence.repositories import (
    CampaignNotFoundError,
    get_campaign_state,
)
from backend.app.schemas.foreign import ForeignStateResponse

router = APIRouter(prefix="/api/campaigns", tags=["foreign"])


@router.get("/{campaign_id}/foreign", response_model=ForeignStateResponse)
def get_campaign_foreign_state(
    campaign_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> ForeignStateResponse:
    """Return persisted foreign actors without running simulation behavior."""
    try:
        state = get_campaign_state(session, campaign_id)
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail="campaign not found") from error
    return ForeignStateResponse(foreign=state.foreign)
