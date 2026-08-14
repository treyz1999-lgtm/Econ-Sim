from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ResourceId(StrEnum):
    FOOD = "food"
    TIMBER = "timber"
    ORE = "ore"
    ENERGY = "energy"
    CONSUMER_GOODS = "consumer_goods"
    CAPITAL_GOODS = "capital_goods"


class ResourceState(BaseModel):
    model_config = ConfigDict(frozen=True)

    inventory: Decimal = Field(ge=0, allow_inf_nan=False)
    production: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    demand: Decimal = Field(ge=0, allow_inf_nan=False)
    consumption: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    imports: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    exports: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    price: Decimal = Field(gt=0, allow_inf_nan=False)
    world_price: Decimal = Field(gt=0, allow_inf_nan=False)
    shortage_ratio: Decimal = Field(default=Decimal(0), ge=0, le=1, allow_inf_nan=False)
    strategic_reserve_target: Decimal = Field(ge=0, allow_inf_nan=False)
