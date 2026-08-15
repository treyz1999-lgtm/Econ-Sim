from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.data import load_balance
from backend.app.domain.state import PlayerActions
from backend.app.engine.allocation import LaborAllocationError
from backend.app.engine.government import ForeignBorrowingError
from backend.app.engine.labor import PopulationAllocationError
from backend.app.engine.turn_engine import resolve_turn
from backend.app.persistence.database import get_session
from backend.app.persistence.repositories import (
    CampaignNotFoundError,
    StaleTurnError,
    get_campaign_state,
    save_completed_turn,
)
from backend.app.schemas.turns import EndTurnRequest, EndTurnResponse, build_dashboard

router = APIRouter(prefix="/api/campaigns", tags=["turns"])


@router.post("/{campaign_id}/turns", response_model=EndTurnResponse)
def end_turn(
    campaign_id: UUID,
    request: EndTurnRequest,
    session: Annotated[Session, Depends(get_session)],
) -> EndTurnResponse:
    try:
        with session.begin():
            state = get_campaign_state(session, campaign_id)
            if state.turn != request.expected_turn:
                raise StaleTurnError("submitted turn is stale")
            actions = PlayerActions(
                labor_allocation=request.labor_allocation,
                government=request.government,
            )
            next_state, report = resolve_turn(state, actions, load_balance())
            save_completed_turn(session, state.turn, next_state, report)
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail="campaign not found") from error
    except StaleTurnError as error:
        raise HTTPException(status_code=409, detail={"code": "stale_turn"}) from error
    except LaborAllocationError as error:
        raise HTTPException(status_code=422, detail={"code": error.code}) from error
    except (PopulationAllocationError, ForeignBorrowingError) as error:
        raise HTTPException(status_code=422, detail={"code": error.code}) from error
    return EndTurnResponse(
        state=next_state,
        turn_report=report,
        dashboard=build_dashboard(next_state, report),
    )
