from decimal import Decimal
from uuid import UUID

import pytest

from backend.app.core.data import load_balance, load_policies, load_scenario
from backend.app.domain.policies import PolicyAdoption, PolicyDimension
from backend.app.engine.policies import PolicyAdoptionError, resolve_policies
from backend.app.engine.turn_engine import resolve_turn
from backend.tests.helpers import default_actions

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000031")


def test_policy_catalog_covers_every_dimension_and_group() -> None:
    """The data catalog must define all institutional dimensions and reactions."""
    catalog = load_policies()

    assert len(catalog) == 21
    assert {item.dimension for item in catalog.values()} == set(PolicyDimension)
    assert all(len(item.group_reactions) == 4 for item in catalog.values())


def test_policy_cost_and_delayed_activation_are_deterministic() -> None:
    """Adoption costs apply now while configured institutional effects wait."""
    state = load_scenario(str(CAMPAIGN_ID), 42)
    baseline, _ = resolve_turn(state, default_actions(), load_balance())
    actions = default_actions().model_copy(
        update={"policy_adoption": PolicyAdoption(policy_id="commodity_currency")}
    )

    first, first_report = resolve_turn(state, actions, load_balance())
    second, second_report = resolve_turn(first, default_actions(), load_balance())

    assert first.policies.pending is not None
    assert first.policies.active[PolicyDimension.EXCHANGE] == "barter"
    assert first_report.policy.adopted_policy == "commodity_currency"
    assert first.government.treasury == baseline.government.treasury - Decimal("8")
    assert second.policies.pending is None
    assert second.policies.active[PolicyDimension.EXCHANGE] == "commodity_currency"
    assert second_report.policy.activated_policy == "commodity_currency"


def test_ineligible_policy_rejects_before_mutation() -> None:
    """Prerequisite failure must leave the immutable input state unchanged."""
    state = load_scenario(str(CAMPAIGN_ID), 42)
    original = state.model_dump_json()

    with pytest.raises(PolicyAdoptionError, match="prerequisites_not_met"):
        resolve_policies(
            state.policies,
            state.government,
            state.population,
            PolicyAdoption(policy_id="income_tax"),
            1,
            load_policies(),
        )

    assert state.model_dump_json() == original


def test_administration_spending_builds_policy_capacity() -> None:
    """Funded administration should expand capacity for advanced institutions."""
    state = load_scenario(str(CAMPAIGN_ID), 42)

    next_state, _ = resolve_turn(state, default_actions(), load_balance())

    assert (
        next_state.government.administrative_capacity
        > state.government.administrative_capacity
    )
