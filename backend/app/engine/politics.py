from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_quantity
from backend.app.domain.government import GovernmentState
from backend.app.domain.policies import PolicyDefinition, PolicyState
from backend.app.domain.politics import (
    PoliticalGroupState,
    PoliticsState,
    StrainComponents,
    WarningLevel,
)
from backend.app.domain.population import PopulationGroupId, PopulationState
from backend.app.domain.production import SectorId, SectorState
from backend.app.domain.reports import SectorTurnResult
from backend.app.domain.resources import ResourceId, ResourceState
from backend.app.engine.policies import active_administrative_load

ZERO = Decimal(0)
ONE = Decimal(1)


def _clamp(value: Decimal) -> Decimal:
    """Clamp and quantize a normalized political metric to the closed unit range."""
    return quantize_quantity(max(ZERO, min(ONE, value)))


def _weighted_inequality(population: PopulationState) -> Decimal:
    """Calculate a bounded weighted Gini coefficient from group wealth per person."""
    observations: list[tuple[Decimal, Decimal]] = []
    for group in population.groups.values():
        size = sum(group.cohorts.values(), ZERO)
        observations.append((size, group.wealth / max(size, ONE)))
    total_weight = sum((weight for weight, _ in observations), ZERO)
    mean = sum((weight * value for weight, value in observations), ZERO) / max(
        total_weight, ONE
    )
    if mean <= 0:
        return ZERO
    difference = sum(
        weight_a * weight_b * abs(value_a - value_b)
        for weight_a, value_a in observations
        for weight_b, value_b in observations
    )
    return _clamp(difference / (Decimal(2) * total_weight * total_weight * mean))


def _warning_level(strain: Decimal, balance: BalanceConfig) -> WarningLevel:
    """Map systemic strain to a visible non-crisis warning band."""
    thresholds = balance.strain_warning_thresholds
    if strain >= thresholds["critical"]:
        return WarningLevel.CRITICAL
    if strain >= thresholds["severe"]:
        return WarningLevel.SEVERE
    if strain >= thresholds["elevated"]:
        return WarningLevel.ELEVATED
    return WarningLevel.STABLE


@dataclass(frozen=True)
class PoliticsResolution:
    """Return updated political state and legitimacy with causal warning messages."""

    politics: PoliticsState
    government: GovernmentState
    warnings: tuple[str, ...]


def resolve_politics(
    previous: PoliticsState,
    population: PopulationState,
    government: GovernmentState,
    resources: dict[ResourceId, ResourceState],
    sectors: dict[SectorId, SectorState],
    sector_results: dict[SectorId, SectorTurnResult],
    policies: PolicyState,
    reactions: dict[PopulationGroupId, Decimal],
    catalog: dict[str, PolicyDefinition],
    balance: BalanceConfig,
) -> PoliticsResolution:
    """Derive group politics, legitimacy, environmental damage, and systemic strain."""
    total = max(population.total, ONE)
    policy_satisfaction = sum(
        (catalog[item].satisfaction_modifier for item in policies.active.values()), ZERO
    )
    updated_groups: dict[PopulationGroupId, PoliticalGroupState] = {}
    influence_scores: dict[PopulationGroupId, Decimal] = {}
    total_income = max(
        sum((group.income for group in population.groups.values()), ZERO), ONE
    )
    total_wealth = max(
        sum((group.wealth for group in population.groups.values()), ZERO), ONE
    )
    for group_id, demographic in population.groups.items():
        prior = previous.groups[group_id]
        size = sum(demographic.cohorts.values(), ZERO)
        labor_penalty = population.child_labor_exposure * Decimal(
            "0.12"
        ) + population.elderly_labor_exposure * Decimal("0.08")
        tax_penalty = government.tax_rate * Decimal("0.15")
        target = _clamp(
            Decimal("0.25")
            + demographic.needs_fulfillment * Decimal("0.55")
            + policy_satisfaction
            + reactions[group_id]
            - labor_penalty
            - tax_penalty
        )
        satisfaction = _clamp(
            prior.satisfaction
            + (target - prior.satisfaction) * balance.satisfaction_adjustment_rate
        )
        expectation_rate = (
            balance.expectation_gain_rate
            if satisfaction > prior.expectations
            else balance.expectation_loss_rate
        )
        expectations = _clamp(
            prior.expectations + (satisfaction - prior.expectations) * expectation_rate
        )
        grievance = ONE - satisfaction
        organization = _clamp(
            prior.organization
            + grievance * balance.organization_gain_rate
            - satisfaction * balance.organization_decay_rate
        )
        radicalization = _clamp(
            prior.radicalization
            + max(ZERO, grievance - balance.grievance_threshold)
            * organization
            * balance.radicalization_gain_rate
            - max(ZERO, satisfaction - Decimal("0.60"))
            * balance.radicalization_recovery_rate
        )
        updated_groups[group_id] = PoliticalGroupState(
            expectations=expectations,
            satisfaction=satisfaction,
            organization=organization,
            influence=prior.influence,
            radicalization=radicalization,
        )
        admin_bonus = Decimal("0.10") if group_id == PopulationGroupId.ADMINS else ZERO
        influence_scores[group_id] = (
            size / total * Decimal("0.35")
            + demographic.income / total_income * Decimal("0.20")
            + demographic.wealth / total_wealth * Decimal("0.25")
            + organization * Decimal("0.20")
            + admin_bonus
        )
    score_total = max(sum(influence_scores.values(), ZERO), Decimal("0.0001"))
    updated_groups = {
        group_id: group.model_copy(
            update={"influence": _clamp(influence_scores[group_id] / score_total)}
        )
        for group_id, group in updated_groups.items()
    }
    average_satisfaction = sum(
        (group.satisfaction * group.influence for group in updated_groups.values()),
        ZERO,
    )
    polarization = _clamp(
        max(group.satisfaction for group in updated_groups.values())
        - min(group.satisfaction for group in updated_groups.values())
    )
    pollution = sum(
        result.output * sectors[sector_id].pollution_intensity
        for sector_id, result in sector_results.items()
    )
    environmental_modifier = sum(
        (catalog[item].environmental_modifier for item in policies.active.values()),
        ZERO,
    )
    environmental_damage = _clamp(
        previous.environmental_damage * (ONE - balance.environmental_recovery_rate)
        + pollution * balance.environmental_damage_rate * (ONE + environmental_modifier)
    )
    resilience = _clamp(
        population.education_index * Decimal("0.25")
        + government.infrastructure_condition * Decimal("0.30")
        + government.administrative_capacity * Decimal("0.25")
        + min(ONE, government.treasury / Decimal("50")) * Decimal("0.20")
    )
    components = StrainComponents(
        resource_stress=_clamp(
            max(
                resources[ResourceId.FOOD].shortage_ratio,
                resources[ResourceId.ENERGY].shortage_ratio,
            )
        ),
        demographic_stress=_clamp(
            population.dependency_ratio / Decimal(2)
            + population.child_labor_exposure * Decimal("0.25")
            + population.elderly_labor_exposure * Decimal("0.15")
        ),
        inequality=_weighted_inequality(population),
        unmet_expectations=_clamp(
            sum(
                (
                    max(ZERO, group.expectations - group.satisfaction) * group.influence
                    for group in updated_groups.values()
                ),
                ZERO,
            )
        ),
        infrastructure_burden=_clamp(ONE - government.infrastructure_condition),
        debt_pressure=_clamp(
            government.debt_service / max(government.tax_revenue, ONE)
        ),
        environmental_damage=environmental_damage,
        foreign_dependence=ZERO,
        institutional_complexity=_clamp(
            active_administrative_load(policies, catalog)
            / max(government.administrative_capacity, Decimal("0.10"))
        ),
        political_polarization=polarization,
    )
    weighted = sum(
        getattr(components, name) * weight
        for name, weight in balance.strain_weights.items()
    )
    legitimacy_target = _clamp(
        average_satisfaction * Decimal("0.55")
        + government.administrative_capacity * Decimal("0.20")
        + resilience * Decimal("0.25")
        - weighted * Decimal("0.30")
    )
    legitimacy = _clamp(
        government.legitimacy
        + (legitimacy_target - government.legitimacy)
        * balance.legitimacy_adjustment_rate
    )
    strain = _clamp(
        weighted - legitimacy * Decimal("0.12") - resilience * Decimal("0.08")
    )
    level = _warning_level(strain, balance)
    warnings = (
        ()
        if level == WarningLevel.STABLE
        else (f"systemic strain is {level.value}: {strain}",)
    )
    return PoliticsResolution(
        politics=PoliticsState(
            groups=updated_groups,
            systemic_strain=strain,
            components=components,
            polarization=polarization,
            resilience=resilience,
            environmental_damage=environmental_damage,
            warning_level=level,
        ),
        government=government.model_copy(update={"legitimacy": legitimacy}),
        warnings=warnings,
    )
