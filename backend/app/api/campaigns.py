from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.persistence.database import get_session
from backend.app.persistence.repositories import (
    CampaignNotFoundError,
    create_campaign,
    get_campaign_state,
)
from backend.app.schemas.campaigns import CampaignResponse, CreateCampaignRequest

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign_endpoint(
    request: CreateCampaignRequest,
    session: Annotated[Session, Depends(get_session)],
) -> CampaignResponse:
    try:
        with session.begin():
            state = create_campaign(session, request.seed, request.scenario_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return CampaignResponse(state=state)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign_endpoint(
    campaign_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> CampaignResponse:
    try:
        state = get_campaign_state(session, campaign_id)
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail="campaign not found") from error
    return CampaignResponse(state=state)
