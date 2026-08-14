from decimal import Decimal
from uuid import UUID

import pytest

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.production import SectorId
from backend.app.domain.state import PlayerActions
from backend.app.engine.allocation import LaborAllocationError
from backend.app.engine.turn_engine import resolve_turn

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000001")


def default_actions() -> PlayerActions:
    return PlayerActions(
        labor_allocation={
            SectorId.AGRICULTURE: Decimal("45"),
            SectorId.EXTRACTION: Decimal("15"),
            SectorId.MANUFACTURING: Decimal("20"),
            SectorId.CONSTRUCTION: Decimal("5"),
            SectorId.ENERGY: Decimal("10"),
        }
    )


def test_turn_is_deterministic_and_does_not_mutate_input() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    original_json = state.model_dump_json()

    first = resolve_turn(state, default_actions(), load_balance())
    second = resolve_turn(state, default_actions(), load_balance())

    assert first == second
    assert state.model_dump_json() == original_json
    assert first[0].turn == 1


def test_overallocated_turn_fails_before_state_change() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)
    allocation = {sector_id: Decimal("21") for sector_id in SectorId}

    with pytest.raises(LaborAllocationError):
        resolve_turn(
            state,
            PlayerActions(labor_allocation=allocation),
            load_balance(),
        )

    assert state.turn == 0


def test_report_reconciles_with_resulting_state() -> None:
    state = load_scenario(str(CAMPAIGN_ID), seed=42)

    next_state, report = resolve_turn(state, default_actions(), load_balance())

    for resource_id, result in report.resources.items():
        assert result.ending_inventory == next_state.resources[resource_id].inventory
        assert result.new_price == next_state.resources[resource_id].price
    assert len(report.explanations) == 11
