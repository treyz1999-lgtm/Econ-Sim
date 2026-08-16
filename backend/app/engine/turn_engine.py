from decimal import Decimal

from backend.app.core.data import BalanceConfig, load_policies
from backend.app.domain.common import quantize_quantity
from backend.app.domain.population import AgeCohortId
from backend.app.domain.production import SectorId
from backend.app.domain.reports import (
    Cause,
    ForeignTurnResult,
    GovernmentTurnResult,
    MetricExplanation,
    NationTradeTurnResult,
    PolicyTurnResult,
    PoliticsTurnResult,
    PopulationTurnResult,
    ResourceTurnResult,
    TurnReport,
)
from backend.app.domain.resources import ResourceId
from backend.app.domain.state import GameState, PlayerActions
from backend.app.engine.consumption import resolve_consumption
from backend.app.engine.demand import derive_population_demand
from backend.app.engine.explanations import build_explanations
from backend.app.engine.foreign import resolve_foreign_relations
from backend.app.engine.government import resolve_government
from backend.app.engine.infrastructure import resolve_infrastructure
from backend.app.engine.labor import resolve_labor
from backend.app.engine.policies import resolve_policies
from backend.app.engine.politics import resolve_politics
from backend.app.engine.population import resolve_population
from backend.app.engine.pricing import update_prices
from backend.app.engine.production import resolve_production
from backend.app.engine.trade import resolve_trade


def resolve_turn(
    state: GameState, actions: PlayerActions, balance: BalanceConfig
) -> tuple[GameState, TurnReport]:
    """Resolve one deterministic year and return a new immutable state and report."""
    catalog = load_policies()
    policy = resolve_policies(
        state.policies,
        state.government,
        state.population,
        actions.policy_adoption,
        state.turn + 1,
        catalog,
    )
    labor = resolve_labor(actions.labor_allocation, state.population, balance)
    allocated_sectors = {
        sector_id: sector.model_copy(
            update={"assigned_labor": labor.effective_labor[sector_id]}
        )
        for sector_id, sector in state.sectors.items()
    }
    demanded_resources = derive_population_demand(
        state.resources, state.population, balance
    )
    production = resolve_production(demanded_resources, allocated_sectors)
    trade = resolve_trade(
        production.resources,
        policy.government,
        state.foreign,
        policy.policies,
        actions.trade_orders,
        balance,
    )
    consumption = resolve_consumption(trade.resources)
    priced_resources = update_prices(consumption.resources, balance)
    food = priced_resources[ResourceId.FOOD]
    needs_fulfillment = (
        food.consumption / max(food.demand, Decimal(1)) if food.demand else Decimal(1)
    )
    needs_groups = {
        group_id: group.model_copy(
            update={"needs_fulfillment": min(Decimal(1), needs_fulfillment)}
        )
        for group_id, group in state.population.groups.items()
    }
    population_for_finance = state.population.model_copy(
        update={"groups": needs_groups}
    )
    government = resolve_government(
        trade.government,
        population_for_finance,
        actions.government,
        actions.labor_allocation,
        production.sectors,
        production.results,
        balance,
    )
    infrastructure = resolve_infrastructure(
        government.government,
        actions.government,
        production.sectors,
        production.results[SectorId.CONSTRUCTION].output,
        balance,
    )
    demographics = resolve_population(
        government.population,
        infrastructure.government,
        food.shortage_ratio,
        labor.child_exposure,
        labor.elderly_exposure,
        balance,
    )
    essential_imports = (
        priced_resources[ResourceId.FOOD].imports
        + priced_resources[ResourceId.ENERGY].imports
    )
    essential_demand = (
        priced_resources[ResourceId.FOOD].demand
        + priced_resources[ResourceId.ENERGY].demand
    )
    foreign = resolve_foreign_relations(
        state.foreign,
        trade.nations,
        infrastructure.government,
        essential_imports,
        essential_demand,
        balance,
    )
    politics = resolve_politics(
        state.politics,
        demographics.population,
        infrastructure.government,
        priced_resources,
        infrastructure.sectors,
        production.results,
        policy.policies,
        policy.reactions,
        foreign.foreign.foreign_dependence,
        catalog,
        balance,
    )
    next_available_labor = quantize_quantity(
        demographics.population.cohort_total(AgeCohortId.WORKING_AGE)
        * demographics.population.participation_rate
    )
    resource_results = {
        resource_id: ResourceTurnResult(
            opening_inventory=state.resources[resource_id].inventory,
            production=priced_resources[resource_id].production,
            production_inputs=production.resource_inputs[resource_id],
            demand=priced_resources[resource_id].demand,
            consumption=priced_resources[resource_id].consumption,
            ending_inventory=priced_resources[resource_id].inventory,
            shortage_ratio=priced_resources[resource_id].shortage_ratio,
            old_price=state.resources[resource_id].price,
            new_price=priced_resources[resource_id].price,
            imports=priced_resources[resource_id].imports,
            exports=priced_resources[resource_id].exports,
            old_world_price=state.resources[resource_id].world_price,
            new_world_price=priced_resources[resource_id].world_price,
        )
        for resource_id in ResourceId
    }
    warnings = [
        f"{resource_id.value} shortage: {resource.shortage_ratio}"
        for resource_id, resource in priced_resources.items()
        if resource.shortage_ratio >= balance.shortage_warning_threshold
    ]
    if labor.child_exposure > 0:
        warnings.append(f"child labor exposure: {labor.child_exposure}")
    if labor.elderly_exposure > 0:
        warnings.append(f"elderly labor exposure: {labor.elderly_exposure}")
    if infrastructure.maintenance_coverage < 1:
        warnings.append(
            "infrastructure maintenance coverage: "
            f"{infrastructure.maintenance_coverage}"
        )
    warnings.extend(politics.warnings)
    warnings.extend(foreign.warnings)
    explanations = list(build_explanations(priced_resources, production.results))
    explanations.extend(
        [
            MetricExplanation(
                metric="population.total",
                causes=(
                    Cause(
                        code="births",
                        value=demographics.births,
                        message="Births added population",
                    ),
                    Cause(
                        code="deaths",
                        value=sum(demographics.deaths.values(), Decimal(0)),
                        message="Deaths reduced population",
                    ),
                    Cause(
                        code="net_migration",
                        value=demographics.net_migration,
                        message="Migration changed population",
                    ),
                ),
            ),
            MetricExplanation(
                metric="government.domestic_debt",
                causes=(
                    Cause(
                        code="domestic_borrowing",
                        value=government.domestic_borrowing,
                        message="Domestic borrowing financed the unfunded deficit",
                    ),
                ),
            ),
        ]
    )
    explanations.extend(
        [
            MetricExplanation(
                metric="government.legitimacy",
                causes=(
                    Cause(
                        code="group_satisfaction",
                        value=sum(
                            (
                                group.satisfaction * group.influence
                                for group in politics.politics.groups.values()
                            ),
                            Decimal(0),
                        ),
                        message=(
                            "Influence-weighted group satisfaction supported legitimacy"
                        ),
                    ),
                    Cause(
                        code="systemic_strain",
                        value=politics.politics.systemic_strain,
                        message="Systemic strain weakened government legitimacy",
                    ),
                    Cause(
                        code="resilience",
                        value=politics.politics.resilience,
                        message="Institutional resilience supported legitimacy",
                    ),
                ),
            ),
            MetricExplanation(
                metric="politics.systemic_strain",
                causes=tuple(
                    Cause(
                        code=name,
                        value=value,
                        message=(
                            f"{name.replace('_', ' ').title()} contributed pressure"
                        ),
                    )
                    for name, value in politics.politics.components
                    if value > 0
                ),
            ),
        ]
    )
    if policy.adopted_policy is not None:
        definition = catalog[policy.adopted_policy]
        explanations.append(
            MetricExplanation(
                metric="policies.adoption",
                causes=(
                    Cause(
                        code="implementation_cost",
                        value=definition.implementation_cost,
                        message=f"{definition.name} consumed treasury during adoption",
                    ),
                    Cause(
                        code="administrative_load",
                        value=definition.administrative_load,
                        message=(
                            f"{definition.name} added continuing institutional load"
                        ),
                    ),
                ),
            )
        )
    if trade.total_import_value > 0 or trade.total_export_value > 0:
        explanations.append(
            MetricExplanation(
                metric="foreign.trade_balance",
                causes=(
                    Cause(
                        code="exports",
                        value=trade.total_export_value,
                        message="Exports earned foreign reserves",
                    ),
                    Cause(
                        code="imports",
                        value=-trade.total_import_value,
                        message="Imports consumed foreign reserves",
                    ),
                ),
            )
        )
    next_state = state.model_copy(
        update={
            "turn": state.turn + 1,
            "available_labor": next_available_labor,
            "resources": priced_resources,
            "sectors": infrastructure.sectors,
            "population": demographics.population,
            "government": politics.government,
            "policies": policy.policies,
            "politics": politics.politics,
            "foreign": foreign.foreign,
        }
    )
    working_assigned = labor.assigned_by_cohort[AgeCohortId.WORKING_AGE]
    report = TurnReport(
        previous_turn=state.turn,
        turn=next_state.turn,
        assigned_labor=sum(labor.effective_labor.values(), Decimal(0)),
        assigned_population=labor.assigned_headcount,
        cohort_assignments=labor.assigned_by_cohort,
        unassigned_labor=max(Decimal(0), state.available_labor - working_assigned),
        sectors=production.results,
        resources=resource_results,
        population=PopulationTurnResult(
            opening_population=state.population.total,
            ending_population=demographics.population.total,
            births=demographics.births,
            deaths=demographics.deaths,
            net_migration=demographics.net_migration,
            child_labor_exposure=labor.child_exposure,
            elderly_labor_exposure=labor.elderly_exposure,
            education_index=demographics.population.education_index,
        ),
        government=GovernmentTurnResult(
            tax_revenue=government.government.tax_revenue,
            spending=government.government.spending,
            primary_balance=government.primary_balance,
            overall_balance=government.overall_balance,
            debt_service=government.government.debt_service,
            domestic_borrowing=government.domestic_borrowing,
            domestic_debt=government.government.domestic_debt,
            foreign_debt=government.government.foreign_debt,
            foreign_reserves=government.government.foreign_reserves,
            infrastructure=infrastructure.government.infrastructure,
            infrastructure_depreciation=infrastructure.depreciation,
            infrastructure_added=infrastructure.infrastructure_added,
            legitimacy=politics.government.legitimacy,
            administrative_capacity=politics.government.administrative_capacity,
        ),
        policy=PolicyTurnResult(
            adopted_policy=policy.adopted_policy,
            activated_policy=policy.activated_policy,
            active=policy.policies.active,
        ),
        politics=PoliticsTurnResult(
            systemic_strain=politics.politics.systemic_strain,
            warning_level=politics.politics.warning_level,
            polarization=politics.politics.polarization,
            resilience=politics.politics.resilience,
            environmental_damage=politics.politics.environmental_damage,
            components=politics.politics.components,
        ),
        foreign=ForeignTurnResult(
            nations={
                nation_id: NationTradeTurnResult(
                    imports=trade.nations[nation_id].imports,
                    exports=trade.nations[nation_id].exports,
                    import_cost=trade.nations[nation_id].import_cost,
                    export_revenue=trade.nations[nation_id].export_revenue,
                    trust=nation.trust,
                    relations=nation.relations,
                    pressure=nation.pressure,
                    escalation=nation.escalation,
                )
                for nation_id, nation in foreign.foreign.nations.items()
            },
            total_import_value=trade.total_import_value,
            total_export_value=trade.total_export_value,
            foreign_dependence=foreign.foreign.foreign_dependence,
        ),
        warnings=tuple(warnings),
        explanations=tuple(explanations),
    )
    return next_state, report
