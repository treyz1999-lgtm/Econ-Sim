from decimal import Decimal

import pytest

from backend.app.domain.production import SectorId
from backend.app.engine.allocation import (
    LaborAllocationError,
    validate_labor_allocation,
)


def test_under_allocation_is_allowed() -> None:
    allocation = {sector_id: Decimal("10") for sector_id in SectorId}

    assert validate_labor_allocation(allocation, Decimal("100")) == (
        Decimal("50"),
        Decimal("50"),
    )


def test_over_allocation_is_rejected() -> None:
    allocation = {sector_id: Decimal("21") for sector_id in SectorId}

    with pytest.raises(LaborAllocationError):
        validate_labor_allocation(allocation, Decimal("100"))
