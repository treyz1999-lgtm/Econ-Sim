import hashlib
import json
from decimal import Decimal
from pathlib import Path

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.production import SectorId
from backend.app.domain.state import GameState, PlayerActions
from backend.app.engine.turn_engine import resolve_turn

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "golden_seed_turns.json"


def canonical_digest(model) -> str:
    canonical = json.dumps(
        model.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def run_fixture(fixture: dict) -> list[dict]:
    state = load_scenario(
        fixture["campaign_id"], fixture["seed"], fixture["scenario_id"]
    )
    balance = load_balance()
    results = []
    for raw_action in fixture["actions"]:
        actions = PlayerActions(
            labor_allocation={
                SectorId(key): Decimal(value) for key, value in raw_action.items()
            }
        )
        state, report = resolve_turn(state, actions, balance)
        results.append(
            {
                "turn": state.turn,
                "state_sha256": canonical_digest(state),
                "report_sha256": canonical_digest(report),
            }
        )
        state = GameState.model_validate_json(state.model_dump_json())
    return results


def test_golden_seed_matches_reviewed_canonical_digests() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert run_fixture(fixture) == fixture["expected"]
    assert run_fixture(fixture) == run_fixture(fixture)
