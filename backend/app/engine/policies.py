from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.government import GovernmentState
from backend.app.domain.policies import (
    PolicyAdoption,
    PolicyDefinition,
    PolicyState,
    PolicyTransition,
)
from backend.app.domain.population import PopulationGroupId, PopulationState


class PolicyAdoptionError(ValueError):
    """Report a stable validation code for an invalid policy turn action."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class PolicyResolution:
    """Return policy state, funded government state, reactions, and events."""

    policies: PolicyState
    government: GovernmentState
    reactions: dict[PopulationGroupId, Decimal]
    adopted_policy: str | None
    activated_policy: str | None


def policy_blockers(
    definition: PolicyDefinition,
    state: PolicyState,
    government: GovernmentState,
    population: PopulationState,
    catalog: dict[str, PolicyDefinition] | None = None,
) -> tuple[str, ...]:
    """Return deterministic eligibility blockers without mutating state."""
    blockers: list[str] = []
    if state.active[definition.dimension] == definition.id:
        blockers.append("already_active")
    if state.pending is not None:
        blockers.append("transition_pending")
    active_ids = set(state.active.values())
    if any(item not in active_ids for item in definition.prerequisites):
        blockers.append("prerequisites_not_met")
    if government.administrative_capacity < definition.minimum_administrative_capacity:
        blockers.append("insufficient_administrative_capacity")
    if population.education_index < definition.minimum_education:
        blockers.append("insufficient_education")
    if government.treasury < definition.implementation_cost:
        blockers.append("insufficient_treasury")
    if catalog is not None:
        current = catalog[state.active[definition.dimension]].administrative_load
        projected = active_administrative_load(state, catalog) - current
        projected += definition.administrative_load
        if projected > government.administrative_capacity:
            blockers.append("administrative_load_exceeds_capacity")
    return tuple(blockers)


def resolve_policies(
    state: PolicyState,
    government: GovernmentState,
    population: PopulationState,
    adoption: PolicyAdoption | None,
    turn: int,
    catalog: dict[str, PolicyDefinition],
) -> PolicyResolution:
    """Activate due transitions and validate one newly requested policy adoption."""
    active = dict(state.active)
    history = state.adoption_history
    pending = state.pending
    activated: str | None = None
    if pending is not None and pending.activation_turn <= turn:
        definition = catalog[pending.policy_id]
        active[definition.dimension] = definition.id
        activated = definition.id
        pending = None

    working_state = state.model_copy(
        update={"active": active, "pending": pending, "adoption_history": history}
    )
    reactions = {group: Decimal(0) for group in PopulationGroupId}
    adopted: str | None = None
    if adoption is not None:
        definition = catalog.get(adoption.policy_id)
        if definition is None:
            raise PolicyAdoptionError("unknown_policy")
        blockers = policy_blockers(
            definition, working_state, government, population, catalog
        )
        if blockers:
            raise PolicyAdoptionError(blockers[0])
        adopted = definition.id
        reactions = dict(definition.group_reactions)
        activation_turn = turn + definition.implementation_delay
        if definition.implementation_delay == 0:
            active[definition.dimension] = definition.id
            activated = definition.id
        else:
            pending = PolicyTransition(
                policy_id=definition.id,
                adopted_turn=turn,
                activation_turn=activation_turn,
            )
        history = (*history, definition.id)
        government = government.model_copy(
            update={"treasury": government.treasury - definition.implementation_cost}
        )
    return PolicyResolution(
        policies=working_state.model_copy(
            update={"active": active, "pending": pending, "adoption_history": history}
        ),
        government=government,
        reactions=reactions,
        adopted_policy=adopted,
        activated_policy=activated,
    )


def active_administrative_load(
    state: PolicyState, catalog: dict[str, PolicyDefinition]
) -> Decimal:
    """Sum continuing administrative load across active institutions."""
    return sum(
        (catalog[item].administrative_load for item in state.active.values()),
        Decimal(0),
    )
