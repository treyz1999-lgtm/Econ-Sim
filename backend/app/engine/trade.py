from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.data import BalanceConfig
from backend.app.domain.common import quantize_price, quantize_quantity
from backend.app.domain.foreign import (
    EscalationState,
    ForeignNationId,
    ForeignState,
    TradeOrder,
)
from backend.app.domain.government import GovernmentState
from backend.app.domain.policies import PolicyDimension, PolicyState
from backend.app.domain.resources import ResourceId, ResourceState

ZERO = Decimal(0)
ONE = Decimal(1)


@dataclass(frozen=True)
class NationTradeResult:
    """Summarize requested and executed trade with one foreign actor."""

    requested_imports: Decimal
    requested_exports: Decimal
    imports: dict[ResourceId, Decimal]
    exports: dict[ResourceId, Decimal]
    import_cost: Decimal
    export_revenue: Decimal

    @property
    def requested_total(self) -> Decimal:
        """Return total requested physical trade units."""
        return self.requested_imports + self.requested_exports

    @property
    def executed_total(self) -> Decimal:
        """Return total executed physical trade units."""
        return sum(self.imports.values(), ZERO) + sum(self.exports.values(), ZERO)


@dataclass(frozen=True)
class TradeResolution:
    """Return traded resources, settled reserves, and per-nation results."""

    resources: dict[ResourceId, ResourceState]
    government: GovernmentState
    nations: dict[ForeignNationId, NationTradeResult]
    total_import_value: Decimal
    total_export_value: Decimal


def _policy_multiplier(policies: PolicyState, balance: BalanceConfig) -> Decimal:
    """Map the active trade institution to its permitted volume multiplier."""
    policy = policies.active[PolicyDimension.TRADE]
    if policy == "open_trade":
        return balance.open_trade_multiplier
    if policy == "protectionist_trade":
        return balance.protectionist_trade_multiplier
    return balance.restricted_trade_multiplier


def _escalation_multiplier(escalation: EscalationState) -> Decimal:
    """Reduce market access as diplomatic escalation advances."""
    return {
        EscalationState.NORMAL: ONE,
        EscalationState.DEMANDS: Decimal("0.90"),
        EscalationState.TARIFFS: Decimal("0.75"),
        EscalationState.SANCTIONS: Decimal("0.40"),
        EscalationState.FINANCIAL_PRESSURE: Decimal("0.30"),
        EscalationState.BLOCKADE_WARNING: Decimal("0.15"),
        EscalationState.INVASION_WARNING: Decimal("0.10"),
    }[escalation]


def resolve_trade(
    resources: dict[ResourceId, ResourceState],
    government: GovernmentState,
    foreign: ForeignState,
    policies: PolicyState,
    orders: tuple[TradeOrder, ...],
    balance: BalanceConfig,
) -> TradeResolution:
    """Execute exports then reserve-affordable imports without negative inventory."""
    inventory = {
        resource_id: resource.inventory for resource_id, resource in resources.items()
    }
    imports = {resource_id: ZERO for resource_id in ResourceId}
    exports = {resource_id: ZERO for resource_id in ResourceId}
    reserves = government.foreign_reserves
    policy_multiplier = _policy_multiplier(policies, balance)
    by_nation = {order.nation_id: order for order in orders}
    results: dict[ForeignNationId, NationTradeResult] = {}
    total_export_value = ZERO

    # Export first so foreign earnings can finance imports in the same trade stage.
    export_records: dict[
        ForeignNationId, tuple[dict[ResourceId, Decimal], Decimal]
    ] = {}
    for nation_id in ForeignNationId:
        nation = foreign.nations[nation_id]
        order = by_nation.get(nation_id, TradeOrder(nation_id=nation_id))
        access = policy_multiplier * _escalation_multiplier(nation.escalation)
        executed: dict[ResourceId, Decimal] = {}
        revenue = ZERO
        for resource_id in ResourceId:
            requested = order.exports.get(resource_id, ZERO)
            available = max(
                ZERO,
                inventory[resource_id]
                - resources[resource_id].strategic_reserve_target,
            )
            quantity = quantize_quantity(
                min(requested, nation.export_demand[resource_id] * access, available)
            )
            if quantity > 0:
                executed[resource_id] = quantity
                inventory[resource_id] -= quantity
                exports[resource_id] += quantity
                revenue += quantity * resources[resource_id].world_price
        revenue = quantize_quantity(revenue)
        reserves += revenue
        total_export_value += revenue
        export_records[nation_id] = (executed, revenue)

    total_import_value = ZERO
    for nation_id in ForeignNationId:
        nation = foreign.nations[nation_id]
        order = by_nation.get(nation_id, TradeOrder(nation_id=nation_id))
        access = policy_multiplier * _escalation_multiplier(nation.escalation)
        executed_imports: dict[ResourceId, Decimal] = {}
        cost = ZERO
        for resource_id in ResourceId:
            requested = order.imports.get(resource_id, ZERO)
            offered = min(requested, nation.import_supply[resource_id] * access)
            unit_price = resources[resource_id].world_price
            affordable = reserves / unit_price
            quantity = quantize_quantity(min(offered, affordable))
            if quantity * unit_price > reserves:
                quantity = quantize_quantity(max(ZERO, quantity - Decimal("0.0001")))
            if quantity > 0:
                executed_imports[resource_id] = quantity
                line_cost = quantize_quantity(quantity * unit_price)
                cost += line_cost
                reserves -= line_cost
                inventory[resource_id] += quantity
                imports[resource_id] += quantity
        cost = quantize_quantity(cost)
        total_import_value += cost
        executed_exports, revenue = export_records[nation_id]
        results[nation_id] = NationTradeResult(
            requested_imports=sum(order.imports.values(), ZERO),
            requested_exports=sum(order.exports.values(), ZERO),
            imports=executed_imports,
            exports=executed_exports,
            import_cost=cost,
            export_revenue=revenue,
        )

    updated_resources: dict[ResourceId, ResourceState] = {}
    for resource_id in ResourceId:
        world_supply = sum(
            nation.import_supply[resource_id] for nation in foreign.nations.values()
        )
        world_demand = sum(
            nation.export_demand[resource_id] for nation in foreign.nations.values()
        )
        pressure = (world_demand - world_supply) / max(world_supply, ONE)
        multiplier = max(
            balance.world_price_floor,
            min(
                balance.world_price_ceiling,
                ONE + pressure * balance.world_price_sensitivity,
            ),
        )
        updated_resources[resource_id] = resources[resource_id].model_copy(
            update={
                "inventory": quantize_quantity(inventory[resource_id]),
                "imports": quantize_quantity(imports[resource_id]),
                "exports": quantize_quantity(exports[resource_id]),
                "world_price": quantize_price(
                    resources[resource_id].world_price * multiplier
                ),
            }
        )
    return TradeResolution(
        resources=updated_resources,
        government=government.model_copy(
            update={"foreign_reserves": quantize_quantity(max(ZERO, reserves))}
        ),
        nations=results,
        total_import_value=quantize_quantity(total_import_value),
        total_export_value=quantize_quantity(total_export_value),
    )
