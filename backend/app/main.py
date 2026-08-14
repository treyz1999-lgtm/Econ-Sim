from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, version=settings.app_version)
    application.include_router(api_router)
    return application


app = create_app()
