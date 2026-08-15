import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.state import GameState

DATA_DIRECTORY = Path(__file__).parents[1] / "data"


class BalanceConfig(BaseModel):
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

    @model_validator(mode="after")
    def validate_price_bounds(self) -> "BalanceConfig":
        if self.price_multiplier_floor > self.price_multiplier_ceiling:
            raise ValueError("price multiplier floor cannot exceed ceiling")
        return self


def _load_json(filename: str) -> dict[str, Any]:
    with (DATA_DIRECTORY / filename).open(encoding="utf-8") as source:
        return json.load(source)


def load_balance() -> BalanceConfig:
    return BalanceConfig.model_validate(_load_json("balance.json"))


def load_scenario(
    campaign_id: str, seed: int, scenario_id: str = "agrarian_start"
) -> GameState:
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
