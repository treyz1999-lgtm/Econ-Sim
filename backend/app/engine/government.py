from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_quantity
from backend.app.domain.government import (
    GovernmentActions,
    GovernmentState,
    SpendingCategory,
)
from backend.app.domain.population import (
    PopulationGroupId,
    PopulationGroupState,
    PopulationState,
)
from backend.app.domain.production import SectorId, SectorState
from backend.app.domain.reports import SectorTurnResult


class ForeignBorrowingError(ValueError):
    code = "foreign_borrowing_exceeds_limit"


@dataclass(frozen=True)
class GovernmentResolution:
    government: GovernmentState
    population: PopulationState
    primary_balance: Decimal
    overall_balance: Decimal
    domestic_borrowing: Decimal


def resolve_government(
    government: GovernmentState,
    population: PopulationState,
    actions: GovernmentActions,
    labor_allocation: dict,
    sectors: dict[SectorId, SectorState],
    sector_results: dict[SectorId, SectorTurnResult],
    balance: BalanceConfig,
) -> GovernmentResolution:
    if actions.new_foreign_borrowing > balance.foreign_borrowing_limit:
        raise ForeignBorrowingError("foreign borrowing exceeds per-turn limit")
    incomes = {group_id: Decimal(0) for group_id in PopulationGroupId}
    for sector_id, groups in labor_allocation.items():
        for group_id, cohorts in groups.items():
            headcount = sum(cohorts.values(), Decimal(0))
            incomes[group_id] += headcount * sectors[sector_id].wage
    output_value = sum(
        (
            result.output * sectors[sector_id].wage
            for sector_id, result in sector_results.items()
        ),
        Decimal(0),
    )
    incomes[PopulationGroupId.OWNERS] += output_value * balance.owner_income_share
    taxable_income = sum(incomes.values(), Decimal(0))
    tax_revenue = quantize_quantity(taxable_income * actions.tax_rate)
    spending_total = sum(actions.spending.values(), Decimal(0))
    domestic_interest = government.domestic_debt * government.domestic_interest_rate
    foreign_interest = government.foreign_debt * government.foreign_interest_rate
    debt_service = quantize_quantity(domestic_interest + foreign_interest)
    primary_balance = tax_revenue - spending_total
    overall_balance = primary_balance - debt_service + actions.new_foreign_borrowing
    domestic_borrowing = max(Decimal(0), -overall_balance - government.treasury)
    treasury = max(Decimal(0), government.treasury + overall_balance)

    welfare = actions.spending[SpendingCategory.WELFARE]
    updated_groups: dict[PopulationGroupId, PopulationGroupState] = {}
    for group_id, group in population.groups.items():
        share = (
            group.cohorts["children"]
            + group.cohorts["working_age"]
            + group.cohorts["elderly"]
        )
        share = share / max(population.total, Decimal(1))
        transfer = welfare * share * balance.welfare_transfer_share
        tax = incomes[group_id] * actions.tax_rate
        disposable = max(Decimal(0), incomes[group_id] - tax + transfer)
        updated_groups[group_id] = group.model_copy(
            update={
                "income": quantize_quantity(incomes[group_id]),
                "wealth": quantize_quantity(group.wealth + disposable),
            }
        )
    return GovernmentResolution(
        government=government.model_copy(
            update={
                "tax_rate": actions.tax_rate,
                "tax_revenue": tax_revenue,
                "spending": actions.spending,
                "treasury": quantize_quantity(treasury),
                "domestic_debt": quantize_quantity(
                    government.domestic_debt + domestic_borrowing
                ),
                "foreign_debt": quantize_quantity(
                    government.foreign_debt + actions.new_foreign_borrowing
                ),
                "foreign_reserves": quantize_quantity(
                    government.foreign_reserves + actions.new_foreign_borrowing
                ),
                "debt_service": debt_service,
            }
        ),
        population=population.model_copy(update={"groups": updated_groups}),
        primary_balance=quantize_quantity(primary_balance),
        overall_balance=quantize_quantity(overall_balance),
        domestic_borrowing=quantize_quantity(domestic_borrowing),
    )
