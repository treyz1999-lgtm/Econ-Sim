from decimal import Decimal

from backend.app.domain.production import SectorId


class LaborAllocationError(ValueError):
    code = "labor_exceeds_available"


def validate_labor_allocation(
    labor_allocation: dict[SectorId, Decimal], available_labor: Decimal
) -> tuple[Decimal, Decimal]:
    assigned = sum(labor_allocation.values(), start=Decimal(0))
    if assigned > available_labor:
        raise LaborAllocationError("assigned labor cannot exceed available labor")
    return assigned, available_labor - assigned
