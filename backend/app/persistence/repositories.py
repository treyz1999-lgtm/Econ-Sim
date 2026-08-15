from uuid import UUID, uuid4

from sqlalchemy import update
from sqlalchemy.orm import Session

from backend.app.core.data import load_scenario
from backend.app.domain.reports import TurnReport
from backend.app.domain.state import GameState
from backend.app.persistence.models import CampaignModel, TurnSnapshotModel


class CampaignNotFoundError(LookupError):
    pass


class StaleTurnError(RuntimeError):
    pass


def create_campaign(
    session: Session, seed: int, scenario_id: str = "agrarian_start"
) -> GameState:
    campaign_id = uuid4()
    state = load_scenario(str(campaign_id), seed, scenario_id)
    encoded_state = state.model_dump(mode="json")
    session.add(
        CampaignModel(
            id=str(campaign_id),
            scenario_id=scenario_id,
            seed=seed,
            current_turn=0,
            current_state=encoded_state,
        )
    )
    session.add(
        TurnSnapshotModel(
            campaign_id=str(campaign_id),
            turn_number=0,
            state=encoded_state,
            report=None,
        )
    )
    session.flush()
    return state


def get_campaign_state(session: Session, campaign_id: UUID) -> GameState:
    campaign = session.get(CampaignModel, str(campaign_id))
    if campaign is None:
        raise CampaignNotFoundError(str(campaign_id))
    payload = dict(campaign.current_state)
    if payload.get("schema_version", 1) < 2 or "population" not in payload:
        baseline = load_scenario(campaign.id, campaign.seed, campaign.scenario_id)
        payload.update(
            {
                "schema_version": 2,
                "population": baseline.population.model_dump(mode="json"),
                "government": baseline.government.model_dump(mode="json"),
            }
        )
    return GameState.model_validate(payload)


def save_completed_turn(
    session: Session,
    previous_turn: int,
    state: GameState,
    report: TurnReport,
) -> None:
    encoded_state = state.model_dump(mode="json")
    encoded_report = report.model_dump(mode="json")
    result = session.execute(
        update(CampaignModel)
        .where(
            CampaignModel.id == str(state.campaign_id),
            CampaignModel.current_turn == previous_turn,
        )
        .values(current_turn=state.turn, current_state=encoded_state)
    )
    if result.rowcount != 1:
        raise StaleTurnError("campaign turn changed before completion")
    session.add(
        TurnSnapshotModel(
            campaign_id=str(state.campaign_id),
            turn_number=state.turn,
            state=encoded_state,
            report=encoded_report,
        )
    )
    session.flush()
