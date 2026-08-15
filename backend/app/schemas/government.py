from decimal import Decimal

from pydantic import BaseModel

from backend.app.domain.government import SpendingCategory


class GovernmentSummary(BaseModel):
    """Expose the principal fiscal, infrastructure, and legitimacy indicators."""

    tax_rate: Decimal
    tax_revenue: Decimal
    spending: dict[SpendingCategory, Decimal]
    treasury: Decimal
    domestic_debt: Decimal
    foreign_debt: Decimal
    foreign_reserves: Decimal
    debt_service: Decimal
    infrastructure: Decimal
    infrastructure_condition: Decimal
    legitimacy: Decimal
    administrative_capacity: Decimal
