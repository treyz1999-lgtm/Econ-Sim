import hashlib
import json
from copy import deepcopy
from pathlib import Path

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.state import GameState, PlayerActions
from backend.app.engine.turn_engine import resolve_turn

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "golden_seed_turns.json"


def canonical_digest(model) -> str:
    canonical = json.dumps(
        model.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def deep_merge(target: dict, overrides: dict) -> dict:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def run_fixture(fixture: dict) -> list[dict]:
    state = load_scenario(
        fixture["campaign_id"], fixture["seed"], fixture["scenario_id"]
    )
    balance = load_balance()
    results = []
    for turn in fixture["turns"]:
        raw_action = deep_merge(deepcopy(fixture["base_action"]), turn["overrides"])
        actions = PlayerActions.model_validate(raw_action)
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

    expected = [turn["expected"] for turn in fixture["turns"]]
    assert run_fixture(fixture) == expected
    assert run_fixture(fixture) == run_fixture(fixture)
