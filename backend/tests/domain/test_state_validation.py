from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from backend.app.core.data import load_scenario
from backend.app.domain.production import SectorId
from backend.app.domain.state import PlayerActions

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_scenario_contains_complete_nonnegative_economy() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)

    assert len(state.resources) == 6
    assert len(state.sectors) == 5
    assert all(resource.inventory >= 0 for resource in state.resources.values())


def test_actions_require_every_sector() -> None:
    with pytest.raises(ValidationError):
        PlayerActions(labor_allocation={SectorId.AGRICULTURE: Decimal("10")})


def test_actions_reject_negative_labor() -> None:
    allocation = {sector_id: Decimal("1") for sector_id in SectorId}
    allocation[SectorId.ENERGY] = Decimal("-1")

    with pytest.raises(ValidationError):
        PlayerActions(labor_allocation=allocation)
