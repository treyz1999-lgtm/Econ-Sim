from backend.app.core.data import BalanceConfig
from backend.app.domain.reports import ResourceTurnResult, TurnReport
from backend.app.domain.resources import ResourceId
from backend.app.domain.state import GameState, PlayerActions
from backend.app.engine.allocation import validate_labor_allocation
from backend.app.engine.consumption import resolve_consumption
from backend.app.engine.explanations import build_explanations
from backend.app.engine.pricing import update_prices
from backend.app.engine.production import resolve_production


def resolve_turn(
    state: GameState, actions: PlayerActions, balance: BalanceConfig
) -> tuple[GameState, TurnReport]:
    assigned, unassigned = validate_labor_allocation(
        actions.labor_allocation, state.available_labor
    )
    allocated_sectors = {
        sector_id: sector.model_copy(
            update={"assigned_labor": actions.labor_allocation[sector_id]}
        )
        for sector_id, sector in state.sectors.items()
    }
    production = resolve_production(state.resources, allocated_sectors)
    consumption = resolve_consumption(production.resources)
    priced_resources = update_prices(consumption.resources, balance)

    resource_results: dict[ResourceId, ResourceTurnResult] = {}
    for resource_id in ResourceId:
        before = state.resources[resource_id]
        after = priced_resources[resource_id]
        resource_results[resource_id] = ResourceTurnResult(
            opening_inventory=before.inventory,
            production=after.production,
            production_inputs=production.resource_inputs[resource_id],
            demand=after.demand,
            consumption=after.consumption,
            ending_inventory=after.inventory,
            shortage_ratio=after.shortage_ratio,
            old_price=before.price,
            new_price=after.price,
        )

    warning_threshold = balance.shortage_warning_threshold
    warnings = tuple(
        f"{resource_id.value} shortage: {resource.shortage_ratio}"
        for resource_id, resource in priced_resources.items()
        if resource.shortage_ratio >= warning_threshold
    )
    explanations = build_explanations(priced_resources, production.results)
    next_state = state.model_copy(
        update={
            "turn": state.turn + 1,
            "resources": priced_resources,
            "sectors": production.sectors,
        }
    )
    report = TurnReport(
        previous_turn=state.turn,
        turn=next_state.turn,
        assigned_labor=assigned,
        unassigned_labor=unassigned,
        sectors=production.results,
        resources=resource_results,
        warnings=warnings,
        explanations=explanations,
    )
    return next_state, report
