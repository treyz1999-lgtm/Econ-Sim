from fastapi import APIRouter

from backend.app.api.campaigns import router as campaigns_router
from backend.app.api.foreign import router as foreign_router
from backend.app.api.health import router as health_router
from backend.app.api.policies import router as policies_router
from backend.app.api.turns import router as turns_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(campaigns_router)
api_router.include_router(turns_router)
api_router.include_router(policies_router)
api_router.include_router(foreign_router)
