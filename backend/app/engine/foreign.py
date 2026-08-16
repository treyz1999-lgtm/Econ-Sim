from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_quantity
from backend.app.domain.foreign import (
    EscalationState,
    ForeignNationId,
    ForeignState,
)
from backend.app.domain.government import GovernmentState
from backend.app.engine.trade import NationTradeResult

ZERO = Decimal(0)
ONE = Decimal(1)
ESCALATION_ORDER = tuple(EscalationState)


@dataclass(frozen=True)
class ForeignResolution:
    """Return updated foreign actors and non-terminal diplomatic warnings."""

    foreign: ForeignState
    warnings: tuple[str, ...]


def _clamp(value: Decimal, low: Decimal = ZERO, high: Decimal = ONE) -> Decimal:
    """Clamp and quantize a foreign-state metric."""
    return quantize_quantity(max(low, min(high, value)))


def resolve_foreign_relations(
    foreign: ForeignState,
    trade_results: dict[ForeignNationId, NationTradeResult],
    government: GovernmentState,
    essential_imports: Decimal,
    essential_demand: Decimal,
    balance: BalanceConfig,
) -> ForeignResolution:
    """Update trust, relations, debt claims, dependence, and ordered escalation."""
    strengths = sum(
        (nation.economic_strength for nation in foreign.nations.values()), ZERO
    )
    nations = {}
    warnings: list[str] = []
    for nation_id in ForeignNationId:
        nation = foreign.nations[nation_id]
        trade = trade_results[nation_id]
        fulfillment = (
            trade.executed_total / trade.requested_total
            if trade.requested_total > 0
            else ONE
        )
        activity = min(ONE, trade.executed_total / Decimal("20"))
        trust = _clamp(
            nation.trust
            + activity * balance.trade_trust_gain_rate
            - (ONE - fulfillment) * balance.unmet_trade_trust_penalty
        )
        relations = _clamp(
            nation.relations
            + activity * Decimal("0.04")
            - (ONE - fulfillment) * Decimal("0.03"),
            Decimal(-1),
            ONE,
        )
        debt_claims = quantize_quantity(
            government.foreign_debt * nation.economic_strength / max(strengths, ONE)
        )
        relationship_pressure = (ONE - relations) / Decimal(2)
        debt_pressure = debt_claims / max(government.tax_revenue * Decimal("5"), ONE)
        pressure = _clamp(
            nation.aggressiveness * nation.strategic_interest * relationship_pressure
            + min(ONE, debt_pressure) * Decimal("0.35")
            - trust * Decimal("0.20")
        )
        index = ESCALATION_ORDER.index(nation.escalation)
        if pressure >= balance.escalation_pressure_high:
            index = min(index + 1, len(ESCALATION_ORDER) - 1)
        elif pressure <= balance.escalation_pressure_low:
            index = max(index - 1, 0)
        escalation = ESCALATION_ORDER[index]
        if escalation != EscalationState.NORMAL:
            warnings.append(
                f"{nation.name} escalation is {escalation.value}: {pressure}"
            )
        nations[nation_id] = nation.model_copy(
            update={
                "trust": trust,
                "relations": relations,
                "debt_claims": debt_claims,
                "pressure": pressure,
                "escalation": escalation,
            }
        )
    dependence = _clamp(essential_imports / max(essential_demand, ONE))
    return ForeignResolution(
        foreign=foreign.model_copy(
            update={"nations": nations, "foreign_dependence": dependence}
        ),
        warnings=tuple(warnings),
    )
