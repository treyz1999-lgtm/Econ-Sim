from decimal import Decimal

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.government import SpendingCategory
from backend.app.engine.infrastructure import resolve_infrastructure
from backend.tests.helpers import government_actions


def test_full_maintenance_prevents_depreciation() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)

    result = resolve_infrastructure(
        state.government,
        government_actions(),
        state.sectors,
        Decimal(0),
        load_balance(),
    )

    assert result.maintenance_coverage == 1
    assert result.depreciation == 0


def test_no_maintenance_causes_depreciation() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)
    actions = government_actions()
    spending = dict(actions.spending)
    spending[SpendingCategory.INFRASTRUCTURE] = Decimal(0)
    actions = actions.model_copy(update={"spending": spending})

    result = resolve_infrastructure(
        state.government, actions, state.sectors, Decimal(0), load_balance()
    )

    assert result.depreciation > 0
    assert result.government.infrastructure < state.government.infrastructure
