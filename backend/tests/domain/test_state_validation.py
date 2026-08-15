from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from backend.app.core.data import load_scenario
from backend.app.domain.population import AgeCohortId, PopulationGroupId
from backend.app.domain.production import SectorId
from backend.app.domain.state import PlayerActions
from backend.tests.helpers import government_actions

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_scenario_contains_complete_nonnegative_economy() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)

    assert len(state.resources) == 6
    assert len(state.sectors) == 5
    assert all(resource.inventory >= 0 for resource in state.resources.values())


def test_actions_allow_partial_sector_maps() -> None:
    actions = PlayerActions(
        labor_allocation={SectorId.AGRICULTURE: {}},
        government=government_actions(),
    )

    assert set(actions.labor_allocation) == {SectorId.AGRICULTURE}


def test_actions_reject_negative_labor() -> None:
    allocation = {
        SectorId.ENERGY: {
            PopulationGroupId.WORKERS: {AgeCohortId.CHILDREN: Decimal("-1")}
        }
    }

    with pytest.raises(ValidationError):
        PlayerActions(labor_allocation=allocation, government=government_actions())
