from decimal import Decimal

import pytest

from backend.app.core.data import load_balance, load_scenario
from backend.app.engine.government import ForeignBorrowingError, resolve_government
from backend.app.engine.production import resolve_production
from backend.tests.helpers import government_actions, labor_allocation


def test_deficit_is_financed_and_foreign_borrowing_adds_reserves() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)
    production = resolve_production(state.resources, state.sectors)
    actions = government_actions().model_copy(
        update={"new_foreign_borrowing": Decimal("5")}
    )

    result = resolve_government(
        state.government,
        state.population,
        actions,
        labor_allocation(),
        state.sectors,
        production.results,
        load_balance(),
    )

    assert result.government.foreign_debt == 5
    assert result.government.foreign_reserves == 5
    assert result.government.domestic_debt >= 0


def test_foreign_borrowing_limit_is_enforced() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)
    production = resolve_production(state.resources, state.sectors)
    actions = government_actions().model_copy(
        update={"new_foreign_borrowing": Decimal("26")}
    )

    with pytest.raises(ForeignBorrowingError):
        resolve_government(
            state.government,
            state.population,
            actions,
            labor_allocation(),
            state.sectors,
            production.results,
            load_balance(),
        )


def test_deficit_beyond_treasury_creates_domestic_debt() -> None:
    state = load_scenario("00000000-0000-0000-0000-000000000001", 42)
    production = resolve_production(state.resources, state.sectors)
    government = state.government.model_copy(update={"treasury": Decimal(0)})
    actions = government_actions()
    spending = {category: Decimal("20") for category in actions.spending}
    actions = actions.model_copy(update={"spending": spending})

    result = resolve_government(
        government,
        state.population,
        actions,
        labor_allocation(),
        state.sectors,
        production.results,
        load_balance(),
    )

    assert result.domestic_borrowing > 0
    assert result.government.domestic_debt == result.domestic_borrowing
