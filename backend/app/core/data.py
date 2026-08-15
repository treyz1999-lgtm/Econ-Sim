import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.policies import PolicyDefinition
from backend.app.domain.state import GameState

DATA_DIRECTORY = Path(__file__).parents[1] / "data"


class BalanceConfig(BaseModel):
    """Validate all tunable economic, demographic, and political coefficients."""

    model_config = ConfigDict(frozen=True)

    shortage_pressure_coefficient: Decimal = Field(ge=0, allow_inf_nan=False)
    surplus_pressure_coefficient: Decimal = Field(ge=0, allow_inf_nan=False)
    surplus_pressure_cap: Decimal = Field(ge=0, allow_inf_nan=False)
    price_multiplier_floor: Decimal = Field(gt=0, allow_inf_nan=False)
    price_multiplier_ceiling: Decimal = Field(gt=0, allow_inf_nan=False)
    shortage_warning_threshold: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    cohort_productivity: dict[str, Decimal]
    per_capita_demand: dict[str, dict[str, dict[str, Decimal]]]
    child_labor_education_penalty: Decimal = Field(ge=0, le=1)
    child_labor_mortality_coefficient: Decimal = Field(ge=0, le=1)
    elderly_labor_mortality_coefficient: Decimal = Field(ge=0, le=1)
    base_birth_rate: Decimal = Field(ge=0, le=1)
    base_mortality_rates: dict[str, Decimal]
    food_shortage_mortality_coefficient: Decimal = Field(ge=0, le=1)
    health_mortality_mitigation: Decimal = Field(ge=0, le=1)
    base_migration_rate: Decimal = Field(ge=-1, le=1)
    education_gain_rate: Decimal = Field(ge=0, le=1)
    owner_income_share: Decimal = Field(ge=0, le=1)
    welfare_transfer_share: Decimal = Field(ge=0, le=1)
    foreign_borrowing_limit: Decimal = Field(ge=0)
    infrastructure_maintenance_cost: Decimal = Field(ge=0)
    infrastructure_depreciation_rate: Decimal = Field(ge=0, le=1)
    construction_cost_per_unit: Decimal = Field(gt=0)
    infrastructure_conversion: Decimal = Field(ge=0)
    sector_capacity_conversion: Decimal = Field(ge=0)
    administrative_capacity_gain_rate: Decimal = Field(ge=0, le=1)
    satisfaction_adjustment_rate: Decimal = Field(ge=0, le=1)
    expectation_gain_rate: Decimal = Field(ge=0, le=1)
    expectation_loss_rate: Decimal = Field(ge=0, le=1)
    organization_gain_rate: Decimal = Field(ge=0, le=1)
    organization_decay_rate: Decimal = Field(ge=0, le=1)
    radicalization_gain_rate: Decimal = Field(ge=0, le=1)
    radicalization_recovery_rate: Decimal = Field(ge=0, le=1)
    grievance_threshold: Decimal = Field(ge=0, le=1)
    legitimacy_adjustment_rate: Decimal = Field(ge=0, le=1)
    environmental_damage_rate: Decimal = Field(ge=0)
    environmental_recovery_rate: Decimal = Field(ge=0, le=1)
    strain_warning_thresholds: dict[str, Decimal]
    strain_weights: dict[str, Decimal]

    @model_validator(mode="after")
    def validate_price_bounds(self) -> "BalanceConfig":
        if self.price_multiplier_floor > self.price_multiplier_ceiling:
            raise ValueError("price multiplier floor cannot exceed ceiling")
        return self


def _load_json(filename: str) -> dict[str, Any]:
    """Load one checked-in data document from the backend data directory."""
    with (DATA_DIRECTORY / filename).open(encoding="utf-8") as source:
        return json.load(source)


def load_balance() -> BalanceConfig:
    """Return validated tunable coefficients consumed by engine functions."""
    return BalanceConfig.model_validate(_load_json("balance.json"))


def load_policies() -> dict[str, PolicyDefinition]:
    """Return the validated policy catalog keyed by stable policy ID."""
    definitions = [
        PolicyDefinition.model_validate(item)
        for item in _load_json("policies.json")["policies"]
    ]
    catalog = {definition.id: definition for definition in definitions}
    if len(catalog) != len(definitions):
        raise ValueError("policy IDs must be unique")
    for definition in definitions:
        if any(item not in catalog for item in definition.prerequisites):
            raise ValueError(f"unknown prerequisite for policy {definition.id}")
    return catalog


def load_scenario(
    campaign_id: str, seed: int, scenario_id: str = "agrarian_start"
) -> GameState:
    """Build a deterministic initial game state from scenario configuration."""
    scenarios = _load_json("scenarios.json")
    scenario = scenarios.get(scenario_id)
    if scenario is None:
        raise ValueError(f"unknown scenario: {scenario_id}")
    return GameState.model_validate(
        {
            **scenario,
            "campaign_id": campaign_id,
            "seed": seed,
            "scenario_id": scenario_id,
        }
    )
