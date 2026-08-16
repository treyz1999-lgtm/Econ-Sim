from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.data import load_scenario
from backend.app.persistence.models import CampaignModel
from backend.app.persistence.repositories import get_campaign_state


def test_milestone_one_state_is_upgraded_deterministically(
    session_factory: sessionmaker[Session],
) -> None:
    campaign_id = UUID("00000000-0000-0000-0000-000000000010")
    state = load_scenario(str(campaign_id), 42)
    legacy = state.model_dump(mode="json")
    legacy.pop("schema_version")
    legacy.pop("population")
    legacy.pop("government")
    with session_factory() as session, session.begin():
        session.add(
            CampaignModel(
                id=str(campaign_id),
                scenario_id="agrarian_start",
                seed=42,
                current_turn=state.turn,
                current_state=legacy,
            )
        )
    with session_factory() as session:
        upgraded = get_campaign_state(session, campaign_id)

    assert upgraded.schema_version == 4
    assert upgraded.population == state.population
    assert upgraded.government == state.government
    assert upgraded.policies == state.policies
    assert upgraded.politics == state.politics
    assert upgraded.foreign == state.foreign


def test_milestone_three_state_receives_foreign_baseline(
    session_factory: sessionmaker[Session],
) -> None:
    """Schema-three snapshots should retain state and gain configured actors."""
    campaign_id = UUID("00000000-0000-0000-0000-000000000011")
    state = load_scenario(str(campaign_id), 43)
    legacy = state.model_dump(mode="json")
    legacy["schema_version"] = 3
    legacy.pop("foreign")
    with session_factory() as session, session.begin():
        session.add(
            CampaignModel(
                id=str(campaign_id),
                scenario_id="agrarian_start",
                seed=43,
                current_turn=state.turn,
                current_state=legacy,
            )
        )

    with session_factory() as session:
        upgraded = get_campaign_state(session, campaign_id)

    assert upgraded.schema_version == 4
    assert upgraded.policies == state.policies
    assert upgraded.politics == state.politics
    assert upgraded.foreign == state.foreign
