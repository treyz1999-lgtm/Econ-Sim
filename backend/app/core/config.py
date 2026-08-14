import os

from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_name: str = "Econ Sim API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./econ_sim.db"


settings = Settings(
    database_url=os.getenv("ECON_SIM_DATABASE_URL", "sqlite:///./econ_sim.db")
)
