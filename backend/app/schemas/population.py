from decimal import Decimal

from pydantic import BaseModel

from backend.app.domain.population import AgeCohortId, PopulationGroupId


class PopulationSummary(BaseModel):
    total: Decimal
    cohorts: dict[AgeCohortId, Decimal]
    groups: dict[PopulationGroupId, Decimal]
    dependency_ratio: Decimal
    education_index: Decimal
    child_labor_exposure: Decimal
    elderly_labor_exposure: Decimal
