from decimal import Decimal
from uuid import UUID

from backend.app.core.data import load_balance, load_policies, load_scenario
from backend.app.domain.population import PopulationGroupId
from backend.app.domain.resources import ResourceId
from backend.app.engine.politics import resolve_politics
from backend.app.engine.production import resolve_production

CAMPAIGN_ID = UUID("00000000-0000-0000-0000-000000000032")


def _resolve(state, population=None, government=None):
    """Resolve politics with a real production result and optional state overrides."""
    production = resolve_production(state.resources, state.sectors)
    return resolve_politics(
        state.politics,
        population or state.population,
        government or state.government,
        state.resources,
        state.sectors,
        production.results,
        state.policies,
        {group: Decimal(0) for group in PopulationGroupId},
        Decimal(0),
        load_policies(),
        load_balance(),
    )


def test_political_metrics_are_bounded_normalized_and_deterministic() -> None:
    """Repeated political resolution must be stable and preserve metric bounds."""
    state = load_scenario(str(CAMPAIGN_ID), 42)

    first = _resolve(state)
    second = _resolve(state)

    assert first == second
    assert abs(
        sum((group.influence for group in first.politics.groups.values()), Decimal(0))
        - Decimal(1)
    ) <= Decimal("0.0004")
    for group in first.politics.groups.values():
        assert all(
            Decimal(0) <= value <= Decimal(1)
            for value in (
                group.expectations,
                group.satisfaction,
                group.organization,
                group.influence,
                group.radicalization,
            )
        )


def test_shortage_and_vulnerable_labor_reduce_satisfaction() -> None:
    """Material hardship must create political pressure from simulation state."""
    state = load_scenario(str(CAMPAIGN_ID), 42)
    groups = {
        group_id: group.model_copy(update={"needs_fulfillment": Decimal("0.20")})
        for group_id, group in state.population.groups.items()
    }
    stressed_population = state.population.model_copy(
        update={
            "groups": groups,
            "child_labor_exposure": Decimal("0.50"),
            "elderly_labor_exposure": Decimal("0.50"),
        }
    )
    resources = dict(state.resources)
    resources[ResourceId.FOOD] = resources[ResourceId.FOOD].model_copy(
        update={"shortage_ratio": Decimal("0.80")}
    )
    production = resolve_production(resources, state.sectors)
    stressed = resolve_politics(
        state.politics,
        stressed_population,
        state.government,
        resources,
        state.sectors,
        production.results,
        state.policies,
        {group: Decimal(0) for group in PopulationGroupId},
        Decimal(0),
        load_policies(),
        load_balance(),
    )

    assert (
        stressed.politics.groups[PopulationGroupId.WORKERS].satisfaction
        < state.politics.groups[PopulationGroupId.WORKERS].satisfaction
    )
    assert stressed.politics.components.resource_stress == Decimal("0.8000")
    assert stressed.politics.systemic_strain > Decimal(0)


def test_environmental_damage_responds_to_resource_policy() -> None:
    """Conservation must reduce production-derived damage relative to extraction."""
    state = load_scenario(str(CAMPAIGN_ID), 42)
    extraction = _resolve(state)
    conservation_policies = state.policies.model_copy(
        update={
            "active": {
                **state.policies.active,
                "resource": "conservation_investment",
            }
        }
    )
    production = resolve_production(state.resources, state.sectors)
    conservation = resolve_politics(
        state.politics,
        state.population,
        state.government,
        state.resources,
        state.sectors,
        production.results,
        conservation_policies,
        {group: Decimal(0) for group in PopulationGroupId},
        Decimal(0),
        load_policies(),
        load_balance(),
    )

    assert (
        conservation.politics.environmental_damage
        < extraction.politics.environmental_damage
    )
