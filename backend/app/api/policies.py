from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.data import load_policies
from backend.app.engine.policies import policy_blockers
from backend.app.persistence.database import get_session
from backend.app.persistence.repositories import (
    CampaignNotFoundError,
    get_campaign_state,
)
from backend.app.schemas.policies import PolicyAvailability, PolicyCatalogResponse

router = APIRouter(prefix="/api/campaigns", tags=["policies"])


@router.get("/{campaign_id}/policies", response_model=PolicyCatalogResponse)
def get_campaign_policies(
    campaign_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> PolicyCatalogResponse:
    """Return the policy catalog with eligibility evaluated against current state."""
    try:
        state = get_campaign_state(session, campaign_id)
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail="campaign not found") from error
    catalog = load_policies()
    policies = tuple(
        PolicyAvailability(
            definition=definition,
            eligible=not (
                blockers := policy_blockers(
                    definition,
                    state.policies,
                    state.government,
                    state.population,
                    catalog,
                )
            ),
            blockers=blockers,
            active=state.policies.active[definition.dimension] == definition.id,
        )
        for definition in catalog.values()
    )
    return PolicyCatalogResponse(state=state.policies, policies=policies)
