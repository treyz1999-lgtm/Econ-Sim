from decimal import Decimal

from backend.app.domain.government import GovernmentActions, SpendingCategory
from backend.app.domain.population import AgeCohortId, PopulationGroupId
from backend.app.domain.production import SectorId
from backend.app.domain.state import PlayerActions


def labor_allocation() -> dict:
    return {
        SectorId.AGRICULTURE: {
            PopulationGroupId.FARMERS: {AgeCohortId.WORKING_AGE: Decimal("45")}
        },
        SectorId.EXTRACTION: {
            PopulationGroupId.FARMERS: {AgeCohortId.WORKING_AGE: Decimal("10")},
            PopulationGroupId.WORKERS: {AgeCohortId.WORKING_AGE: Decimal("5")},
        },
        SectorId.MANUFACTURING: {
            PopulationGroupId.WORKERS: {AgeCohortId.WORKING_AGE: Decimal("12")},
            PopulationGroupId.OWNERS: {AgeCohortId.WORKING_AGE: Decimal("8")},
        },
        SectorId.CONSTRUCTION: {
            PopulationGroupId.ADMINS: {AgeCohortId.WORKING_AGE: Decimal("4")}
        },
        SectorId.ENERGY: {
            PopulationGroupId.WORKERS: {AgeCohortId.WORKING_AGE: Decimal("4")},
            PopulationGroupId.ADMINS: {AgeCohortId.WORKING_AGE: Decimal("5")},
        },
    }


def government_actions() -> GovernmentActions:
    return GovernmentActions(
        tax_rate=Decimal("0.10"),
        spending={
            SpendingCategory.ADMINISTRATION: Decimal("4"),
            SpendingCategory.INFRASTRUCTURE: Decimal("5"),
            SpendingCategory.EDUCATION: Decimal("3"),
            SpendingCategory.WELFARE: Decimal("1"),
            SpendingCategory.HEALTH: Decimal("2"),
            SpendingCategory.SECURITY: Decimal("1"),
            SpendingCategory.MILITARY_PRODUCTION: Decimal("0"),
        },
        new_foreign_borrowing=Decimal("0"),
        construction_allocation={"infrastructure": Decimal("1")},
    )


def default_actions() -> PlayerActions:
    return PlayerActions(
        labor_allocation=labor_allocation(), government=government_actions()
    )


def end_turn_json(expected_turn: int = 0) -> dict:
    return {
        "expected_turn": expected_turn,
        "labor_allocation": PlayerActions(
            labor_allocation=labor_allocation(), government=government_actions()
        ).model_dump(mode="json")["labor_allocation"],
        "government": government_actions().model_dump(mode="json"),
    }
