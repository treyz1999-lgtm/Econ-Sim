from decimal import Decimal
from uuid import UUID

from backend.app.core.data import load_balance, load_scenario
from backend.app.domain.foreign import EscalationState, ForeignNationId
from backend.app.engine.foreign import ESCALATION_ORDER, resolve_foreign_relations
from backend.app.engine.trade import NationTradeResult

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000042")


def _empty_trade() -> dict[ForeignNationId, NationTradeResult]:
    """Create fulfilled no-op trade results for every configured nation."""
    return {
        nation_id: NationTradeResult(
            requested_imports=Decimal(0),
            requested_exports=Decimal(0),
            imports={},
            exports={},
            import_cost=Decimal(0),
            export_revenue=Decimal(0),
        )
        for nation_id in ForeignNationId
    }


def test_escalation_advances_at_most_one_state() -> None:
    """High pressure may advance warnings but cannot skip ordered states."""
    state = load_scenario(str(CAMPAIGN_ID), 42)
    dominion = state.foreign.nations[ForeignNationId.IRON_DOMINION].model_copy(
        update={
            "aggressiveness": Decimal(1),
            "strategic_interest": Decimal(1),
            "trust": Decimal(0),
            "relations": Decimal(-1),
            "escalation": EscalationState.TARIFFS,
        }
    )
    foreign = state.foreign.model_copy(
        update={
            "nations": {
                **state.foreign.nations,
                ForeignNationId.IRON_DOMINION: dominion,
            }
        }
    )

    result = resolve_foreign_relations(
        foreign,
        _empty_trade(),
        state.government,
        Decimal(0),
        Decimal(1),
        load_balance(),
    )

    escalation = result.foreign.nations[ForeignNationId.IRON_DOMINION].escalation
    assert (
        ESCALATION_ORDER.index(escalation)
        == ESCALATION_ORDER.index(EscalationState.TARIFFS) + 1
    )
    assert escalation == EscalationState.SANCTIONS


def test_essential_imports_create_visible_foreign_dependence() -> None:
    """Dependence must be derived from essential imports rather than elapsed time."""
    state = load_scenario(str(CAMPAIGN_ID), 42)

    result = resolve_foreign_relations(
        state.foreign,
        _empty_trade(),
        state.government,
        Decimal("25"),
        Decimal("100"),
        load_balance(),
    )

    assert result.foreign.foreign_dependence == Decimal("0.2500")
