from pydantic import BaseModel, ConfigDict

from backend.app.domain.policies import PolicyDefinition, PolicyState


class PolicyAvailability(BaseModel):
    """Pair one catalog definition with campaign-specific eligibility blockers."""

    model_config = ConfigDict(frozen=True)

    definition: PolicyDefinition
    eligible: bool
    blockers: tuple[str, ...]
    active: bool


class PolicyCatalogResponse(BaseModel):
    """Return current institutions and every policy choice available to a campaign."""

    model_config = ConfigDict(frozen=True)

    state: PolicyState
    policies: tuple[PolicyAvailability, ...]
